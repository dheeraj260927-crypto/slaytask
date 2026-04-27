from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_cloudflared import run_with_cloudflared
from datetime import datetime
import json, os, uuid

app = Flask(__name__)
CORS(app)
run_with_cloudflared(app)

TASKS_FILE = 'tasks.json'

def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = load_tasks()
    date_filter = request.args.get('date')
    if date_filter:
        tasks = [t for t in tasks if t.get('date') == date_filter]
    return jsonify(tasks), 200

@app.route('/api/tasks', methods=['POST'])
def add_task():
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
    return jsonify(task), 201

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
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
            return jsonify(task), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    tasks = load_tasks()
    original_len = len(tasks)
    tasks = [t for t in tasks if t['id'] != task_id]
    if len(tasks) == original_len:
        return jsonify({'error': 'Task not found'}), 404
    save_tasks(tasks)
    return jsonify({'message': 'Task deleted'}), 200

@app.route('/api/tasks/<task_id>/toggle', methods=['PATCH'])
def toggle_task(task_id):
    tasks = load_tasks()
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            task['completed'] = not task['completed']
            tasks[i] = task
            save_tasks(tasks)
            return jsonify(task), 200
    return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    if not os.path.exists(TASKS_FILE):
        save_tasks([])
    print("TaskSlay is starting with a PUBLIC URL...")
    app.run(debug=False, port=5000)
