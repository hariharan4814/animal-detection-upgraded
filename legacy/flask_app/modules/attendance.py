from database.db import execute_query, execute_update
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_attendance_email(farmer_name, email, action, date, time, location, hours, email_config):
    if not email:
        return
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Farm Management <{email_config['sender_email']}>"
        msg['To'] = email
        msg['Subject'] = f"Attendance {action} Notification - {date}"

        if action == "Check-in":
            body = f"Hello {farmer_name},\n\nYour attendance has been recorded.\nAction: {action}\nDate: {date}\nTime: {time}\nLocation: {location}\n\nHave a great day ahead!"
        else:
            body = f"Hello {farmer_name},\n\nYour attendance has been recorded.\nAction: {action}\nDate: {date}\nTime: {time}\nLocation: {location}\nTotal Hours Today: {hours} hrs\n\nThank you for your work!"

        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            print(f"Attendance email sent to {email}")
    except Exception as e:
        print(f"Error sending attendance email: {e}")

def mark_check_in(farmer_id, email_config, device_location=None):
    date = datetime.now().strftime("%Y-%m-%d")
    check_in_time = datetime.now().strftime("%H:%M:%S")
    
    farmer = execute_query("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
    if not farmer:
        return False
        
    location = device_location if device_location else farmer[0]['field']
    try:
        farmer_email = farmer[0]['email']
    except Exception:
        farmer_email = ''
    farmer_name = farmer[0]['name']

    existing = execute_query("SELECT * FROM attendance WHERE farmer_id = ? AND date = ?", (farmer_id, date))
    if not existing:
        execute_query("INSERT INTO attendance (farmer_id, date, check_in, check_out, total_hours, location) VALUES (?, ?, ?, ?, ?, ?)", 
                      (farmer_id, date, check_in_time, None, 0.0, location), commit=True)
        send_attendance_email(farmer_name, farmer_email, "Check-in", date, check_in_time, location, 0, email_config)
        return True
    return False

def mark_check_out(farmer_id, email_config, device_location=None):
    date = datetime.now().strftime("%Y-%m-%d")
    check_out_time = datetime.now().strftime("%H:%M:%S")
    
    farmer = execute_query("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
    if not farmer:
        return False
        
    location = device_location if device_location else farmer[0]['field']
    try:
        farmer_email = farmer[0]['email']
    except Exception:
        farmer_email = ''
    farmer_name = farmer[0]['name']

    existing = execute_query("SELECT * FROM attendance WHERE farmer_id = ? AND date = ?", (farmer_id, date))
    if existing and existing[0]['check_out'] is None:
        check_in_str = existing[0]['check_in']
        t1 = datetime.strptime(check_in_str, "%H:%M:%S")
        t2 = datetime.strptime(check_out_time, "%H:%M:%S")
        hours = (t2 - t1).total_seconds() / 3600.0
        hours = round(hours, 2)
        
        execute_update("UPDATE attendance SET check_out = ?, total_hours = ? WHERE id = ?", (check_out_time, hours, existing[0]['id']))
        send_attendance_email(farmer_name, farmer_email, "Check-out", date, check_out_time, location, hours, email_config)
        return True
    return False

def get_attendance():
    return execute_query('''
        SELECT a.id, f.name, a.date, a.check_in, a.check_out, a.total_hours, a.location
        FROM attendance a JOIN farmers f ON a.farmer_id = f.id
        ORDER BY a.date DESC, a.check_in DESC
    ''')
