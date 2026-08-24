from database.db import execute_query, execute_update
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import pygame
import os

def trigger_alert(animal_log_id, animal_type, image_path, threat_level, email_config, timestamp, location):
    # Store in alerts table
    alert_type = 'Email + Buzzer' if threat_level == 'high' else 'Email' if threat_level == 'medium' else 'Log Only'
    execute_query("INSERT INTO alerts (animal_log_id, alert_type, status) VALUES (?, ?, 'Triggered')",
                  (animal_log_id, alert_type), commit=True)
    
    if threat_level in ['high', 'medium']:
        send_email(animal_type, image_path, email_config, threat_level, timestamp, location)
        
    if threat_level == 'high':
        play_buzzer()

def send_email(animal_type, image_path, email_config, threat_level, timestamp, location):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Animal Detection Project <{email_config['sender_email']}>"
        recipients = [email.strip() for email in email_config['recipient_email'].split(',')]
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = f"{threat_level.upper()} ALERT: {animal_type} Detected!"

        body = f"A {threat_level} threat level animal ({animal_type}) has been detected by the system.\n\nTime: {timestamp}\nLocation: {location}"
        msg.attach(MIMEText(body, 'plain'))

        # Note: image_path is relative to the working directory (e.g. static/...)
        if os.path.exists(image_path):
            with open(image_path, 'rb') as img_file:
                img = MIMEImage(img_file.read())
                msg.attach(img)
                
        # Attach warning_sound.mp3
        sound_paths = [
            'warning_sound.mp3',
            os.path.join(os.path.dirname(__file__), '..', 'warning_sound.mp3')
        ]
        
        for path in sound_paths:
            if os.path.exists(path):
                with open(path, 'rb') as audio_file:
                    audio_part = MIMEBase('audio', 'mpeg')
                    audio_part.set_payload(audio_file.read())
                    encoders.encode_base64(audio_part)
                    audio_part.add_header('Content-Disposition', 'attachment; filename="warning_sound.mp3"')
                    msg.attach(audio_part)
                break
                
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg, to_addrs=recipients)
            print(f"Alert email sent for {animal_type}")
    except Exception as e:
        print(f"Error sending alert email: {e}")

def play_buzzer():
    try:
        pygame.init()
        pygame.mixer.init()
        sound_paths = [
            'warning_sound.mp3',
            os.path.join(os.path.dirname(__file__), '..', 'warning_sound.mp3')
        ]
        for path in sound_paths:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                sound.play()
                print("Buzzer triggered.")
                break
    except Exception as e:
        print(f"Error playing buzzer: {e}")

def get_recent_alerts():
    return execute_query('''
        SELECT a.id, al.animal_type, a.alert_type, al.timestamp, a.status 
        FROM alerts a JOIN animal_logs al ON a.animal_log_id = al.id
        ORDER BY al.timestamp DESC LIMIT 10
    ''')
