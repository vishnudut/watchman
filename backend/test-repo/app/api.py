import os
import subprocess
import pickle

def execute_command(user_input):
    """Command injection vulnerability"""
    # Dangerous: directly using user input in shell command
    os.system(f"echo {user_input}")

    # Another command injection
    subprocess.call(f"ping -c 1 {user_input}", shell=True)

def unsafe_file_read(filename):
    """Path traversal vulnerability"""
    # No validation - user can access any file
    with open(f"/var/data/{filename}", 'r') as f:
        return f.read()

def deserialize_data(data):
    """Insecure deserialization"""
    # pickle.loads() is dangerous with untrusted data
    return pickle.loads(data)

def render_template(user_data):
    """XSS vulnerability"""
    # Directly inserting user data into HTML
    html = f"<div>Welcome {user_data['name']}</div>"
    return html
