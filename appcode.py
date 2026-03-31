from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import atexit
import uuid

# plyer only works on desktop (Windows/macOS/Linux with GUI)
try:
    from plyer import notification
    NOTIFICATIONS_ENABLED = True
except Exception:
    NOTIFICATIONS_ENABLED = False

app = Flask(__name__)
CORS(app)

TASKS_FILE = 'tasks.json'

scheduler = BackgroundScheduler()
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

# ==================== HELPER FUNCTIONS ====================

def load_tasks():
    """Load tasks from JSON file"""
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_tasks(tasks):
    """Save tasks to JSON file"""
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)

def send_notification(title, message):
    """Send desktop notification to user (only on desktop environments)"""
    if not NOTIFICATIONS_ENABLED:
        print(f"[Reminder] {title}: {message}")
        return
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='TaskSlay',
            timeout=10
        )
    except Exception as e:
        print(f"Notification error: {e}")

def schedule_task_reminder(task_id, task_name, reminder_time):
    """Schedule a reminder for a specific task"""
    try:
        reminder_dt = datetime.strptime(reminder_time, '%Y-%m-%d %H:%M')
        job_id = f"task_{task_id}"

        # Remove existing job if it exists
        try:
            scheduler.remove_job(job_id)
        except JobLookupError:
            pass

        scheduler.add_job(
            func=lambda: send_notification('TaskSlay Reminder', f'Task: {task_name}'),
            trigger='date',
            run_date=reminder_dt,
            id=job_id
        )
    except Exception as e:
        print(f"Error scheduling reminder: {e}")

# ==================== FRONTEND ROUTE ====================

@app.route('/')
def home():
    """Serve the TaskSlay frontend"""
    return render_template('index.html')

# ==================== API ROUTES ====================

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks, optionally filtered by date"""
    tasks = load_tasks()
    date_filter = request.args.get('date')

    if date_filter:
        tasks = [t for t in tasks if t.get('date') == date_filter]

    return jsonify(tasks), 200

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task"""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Task name is required'}), 400

    task = {
        'id': str(uuid.uuid4()),
        'name': data['name'],
        'description': data.get('description', ''),
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'time': data.get('time', ''),
        'priority': data.get('priority', 'medium'),
        'category': data.get('category', 'general'),
        'completed': False,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)

    # Schedule reminder if time is provided
    if task['time']:
        reminder_time = f"{task['date']} {task['time']}"
        schedule_task_reminder(task['id'], task['name'], reminder_time)

    return jsonify(task), 201

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update an existing task"""
    data = request.get_json()
    tasks = load_tasks()

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            task['name'] = data.get('name', task['name'])
            task['description'] = data.get('description', task['description'])
            task['date'] = data.get('date', task['date'])
            task['time'] = data.get('time', task['time'])
            task['priority'] = data.get('priority', task['priority'])
            task['category'] = data.get('category', task['category'])
            task['completed'] = data.get('completed', task['completed'])
            tasks[i] = task
            save_tasks(tasks)

            # Reschedule reminder if time changed
            if task['time']:
                reminder_time = f"{task['date']} {task['time']}"
                schedule_task_reminder(task['id'], task['name'], reminder_time)

            return jsonify(task), 200

    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    tasks = load_tasks()
    original_len = len(tasks)
    tasks = [t for t in tasks if t['id'] != task_id]

    if len(tasks) == original_len:
        return jsonify({'error': 'Task not found'}), 404

    save_tasks(tasks)

    # Remove scheduled reminder
    try:
        scheduler.remove_job(f"task_{task_id}")
    except Exception:
        pass

    return jsonify({'message': 'Task deleted'}), 200

@app.route('/api/tasks/<task_id>/toggle', methods=['PATCH'])
def toggle_task(task_id):
    """Toggle task completion status"""
    tasks = load_tasks()

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            task['completed'] = not task['completed']
            tasks[i] = task
            save_tasks(tasks)
            return jsonify(task), 200

    return jsonify({'error': 'Task not found'}), 404

# ==================== RUN APP ====================

if __name__ == '__main__':
    # Create tasks file if it doesn't exist
    if not os.path.exists(TASKS_FILE):
        save_tasks([])

    port = int(os.environ.get('PORT', 5000))
    print("TaskSlay Daily Task Manager is running!")
    print(f"API available at http://localhost:{port}/api/tasks")
    app.run(debug=False, host='0.0.0.0', port=port)