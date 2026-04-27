"""Launches TaskSlay with a public Cloudflare tunnel and saves the URL to url.txt"""
import subprocess, sys, re, threading, time

def run():
    proc = subprocess.Popen(
        [sys.executable, 'run_public.py'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in proc.stdout:
        print(line, end='')
        if 'trycloudflare.com' in line:
            url = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
            if url:
                with open('url.txt', 'w') as f:
                    f.write(url.group(0))
                print(f"\n{'='*60}")
                print(f"PUBLIC URL: {url.group(0)}")
                print(f"{'='*60}\n")

if __name__ == '__main__':
    run()
