from database.db import execute_query, execute_update
from datetime import datetime

def add_task(task_name, assigned_to):
    date = datetime.now().strftime("%Y-%m-%d")
    execute_query("INSERT INTO tasks (task_name, assigned_to, status, date) VALUES (?, ?, 'Pending', ?)", 
                  (task_name, assigned_to, date), commit=True)

def update_task_status(task_id, status):
    execute_update("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))

def get_all_tasks():
    return execute_query('''
        SELECT t.id, t.task_name, f.name as assigned_to_name, t.status, t.date
        FROM tasks t LEFT JOIN farmers f ON t.assigned_to = f.id
        ORDER BY t.id DESC
    ''')
