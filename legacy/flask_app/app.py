from flask import Flask, render_template, request, Response, jsonify, redirect, url_for
from database.db import init_db, execute_query
from modules.animal_detection import VideoStreaming
from modules.attendance import mark_check_in, mark_check_out, get_attendance
from modules.tasks import add_task, update_task_status, get_all_tasks
from modules.alerts import get_recent_alerts
import json
import os
import pygame
from datetime import datetime

app = Flask(__name__)

# Load config
with open('config.json', 'r') as f:
    config_data = json.load(f)

# Email configuration
EMAIL_CONFIG = {
    'sender_email': '2ktamilstatus@gmail.com',
    'sender_password': 'fjod levk pskl dkvs',
    'recipient_email': 'hariharan4814@gmail.com,hariharanb.inbox@gmail.com',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

VIDEO_STREAM = VideoStreaming(EMAIL_CONFIG, config_data)

@app.route('/')
def dashboard():
    # Top stats
    total_farmers = execute_query("SELECT COUNT(*) as c FROM farmers")[0]['c']
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = execute_query("SELECT COUNT(*) as c FROM attendance WHERE date = ?", (today,))[0]['c']
    
    alerts_today = execute_query("SELECT COUNT(*) as c FROM alerts a JOIN animal_logs al ON a.animal_log_id = al.id WHERE al.timestamp LIKE ?", (f"{today}%",))[0]['c']
    
    completed_tasks = execute_query("SELECT COUNT(*) as c FROM tasks WHERE status = 'Completed'")[0]['c']
    
    return render_template('dashboard.html', 
                           total_farmers=total_farmers, 
                           today_attendance=today_attendance,
                           alerts_today=alerts_today,
                           completed_tasks=completed_tasks)

@app.route('/camera')
def camera_page():
    return render_template('camera.html')

@app.route('/attendance')
def attendance_page():
    attendance_logs = get_attendance()
    farmers = execute_query("SELECT * FROM farmers")
    return render_template('attendance.html', attendance_logs=attendance_logs, farmers=farmers)

@app.route('/tasks')
def tasks_page():
    recent_tasks = get_all_tasks()
    farmers = execute_query("SELECT * FROM farmers")
    return render_template('tasks.html', recent_tasks=recent_tasks, farmers=farmers)

@app.route('/alerts')
def alerts_page():
    recent_logs = execute_query("SELECT * FROM animal_logs ORDER BY timestamp DESC LIMIT 50")
    return render_template('alerts.html', recent_logs=recent_logs)

@app.route('/video_feed')
def video_feed():
    return Response(VIDEO_STREAM.generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_detection')
def toggle_detection():
    VIDEO_STREAM._detect = not VIDEO_STREAM._detect
    return jsonify(status="success", detect=VIDEO_STREAM._detect)

@app.route('/toggle_camera')
def toggle_camera():
    VIDEO_STREAM._camera_on = not VIDEO_STREAM._camera_on
    return jsonify(status="success", camera_on=VIDEO_STREAM._camera_on)

# Attendance Routes
@app.route('/check_in', methods=['POST'])
def check_in():
    farmer_id = request.form.get('farmer_id')
    device_location = request.form.get('device_location')
    if farmer_id:
        mark_check_in(farmer_id, EMAIL_CONFIG, device_location)
    return redirect(url_for('attendance_page'))

@app.route('/check_out', methods=['POST'])
def check_out():
    farmer_id = request.form.get('farmer_id')
    device_location = request.form.get('device_location')
    if farmer_id:
        mark_check_out(farmer_id, EMAIL_CONFIG, device_location)
    return redirect(url_for('attendance_page'))

# Task Routes
@app.route('/add_task', methods=['POST'])
def add_new_task():
    task_name = request.form.get('task_name')
    assigned_to = request.form.get('assigned_to')
    if task_name and assigned_to:
        add_task(task_name, assigned_to)
    return redirect(url_for('tasks_page'))

@app.route('/update_task', methods=['POST'])
def update_task():
    task_id = request.form.get('task_id')
    status = request.form.get('status')
    if task_id and status:
        update_task_status(task_id, status)
    return redirect(url_for('tasks_page'))

@app.route('/attendance_report', methods=['GET', 'POST'])
def attendance_report():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if start_date and end_date:
            logs = execute_query('''
                SELECT a.id, f.name, a.date, a.check_in, a.check_out, a.total_hours, a.location
                FROM attendance a JOIN farmers f ON a.farmer_id = f.id
                WHERE a.date >= ? AND a.date <= ?
                ORDER BY a.date DESC, a.check_in DESC
            ''', (start_date, end_date))
        else:
            logs = get_attendance()
    else:
        logs = get_attendance()
        start_date = ''
        end_date = ''
        
    return render_template('attendance_report.html', logs=logs, start_date=start_date, end_date=end_date)

# Farmer Management Routes
@app.route('/farmers')
def manage_farmers():
    farmers = execute_query("SELECT * FROM farmers")
    return render_template('farmers.html', farmers=farmers)

@app.route('/add_farmer', methods=['POST'])
def add_farmer():
    name = request.form.get('name')
    phone = request.form.get('phone')
    field = request.form.get('field')
    email = request.form.get('email')
    if name and phone and field:
        execute_query("INSERT INTO farmers (name, phone, field, email) VALUES (?, ?, ?, ?)", 
                      (name, phone, field, email), commit=True)
    return redirect(url_for('manage_farmers'))

@app.route('/delete_farmer/<int:farmer_id>', methods=['POST'])
def delete_farmer(farmer_id):
    execute_query("DELETE FROM farmers WHERE id = ?", (farmer_id,), commit=True)
    return redirect(url_for('manage_farmers'))

if __name__ == '__main__':
    # Initialize DB before running
    init_db()
    
    # Add dummy farmers if none exist
    farmers_count = execute_query("SELECT COUNT(*) as count FROM farmers")[0]['count']
    if farmers_count == 0:
        execute_query("INSERT INTO farmers (name, phone, field, email) VALUES ('John Doe', '1234567890', 'North Field', 'john@example.com')", commit=True)
        execute_query("INSERT INTO farmers (name, phone, field, email) VALUES ('Jane Smith', '0987654321', 'South Field', 'jane@example.com')", commit=True)
        
    app.run(debug=True, host='0.0.0.0', port=5000)
