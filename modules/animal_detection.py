import cv2
import torch
import numpy as np
import time
import os
from ultralytics import YOLO
import json
from datetime import datetime
from database.db import execute_query
from modules.alerts import trigger_alert

class AnimalDetectionSystem:
    def __init__(self, email_config, config_data):
        self.email_config = email_config
        self.config_data = config_data
        
        self.ANIMAL_CLASSES = [
            'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 
            'zebra', 'giraffe', 'lion', 'tiger', 'cheetah', 'monkey', 
            'leopard', 'wolf', 'fox', 'deer', 'hippo', 'hyena', 
            'jackal', 'kangaroo', 'squirrel', 'penguin', 'eagle', 
            'owl', 'snake', 'crocodile', 'mouse', 'rat'
        ]

        try:
            self.model = YOLO('yolov8n.pt') 
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

        self.COLORS = np.random.uniform(0, 255, size=(len(self.ANIMAL_CLASSES), 3))
        self.threat_levels = self.config_data.get('animal_threat_levels', {})
        
        self.last_notification_time = 0
        self.notification_cooldown = 300  

    def detect_animals(self, frame):
        if self.model is None:
            return frame

        results = self.model(frame, stream=False, verbose=False)
        highest_threat_animal = None
        highest_threat_level = 'low'
        highest_conf = 0

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = self.model.names[cls]

                if label in self.ANIMAL_CLASSES and conf > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    color = tuple(map(int, self.COLORS[self.ANIMAL_CLASSES.index(label)]))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                    threat_level = self.threat_levels.get(label, 'low')
                    if threat_level == 'high':
                        highest_threat_level = 'high'
                        highest_threat_animal = label
                        highest_conf = conf
                    elif threat_level == 'medium' and highest_threat_level != 'high':
                        highest_threat_level = 'medium'
                        highest_threat_animal = label
                        highest_conf = conf
                    elif highest_threat_animal is None:
                        highest_threat_animal = label
                        highest_conf = conf

        current_time = time.time()
        if highest_threat_animal and (current_time - self.last_notification_time >= self.notification_cooldown):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            image_filename = f'detected_{highest_threat_animal}_{int(current_time)}.jpg'
            image_path = os.path.join('static', image_filename)
            
            # Ensure static dir exists
            os.makedirs('static', exist_ok=True)
            cv2.imwrite(image_path, frame)
            
            # Save to animal_logs
            log_id = execute_query(
                "INSERT INTO animal_logs (animal_type, confidence, timestamp, field, image_path) VALUES (?, ?, ?, ?, ?)",
                (highest_threat_animal, highest_conf, timestamp, 'Main Field', image_path), commit=True
            )
            
            # Trigger alerts
            trigger_alert(log_id, highest_threat_animal, image_path, highest_threat_level, self.email_config, timestamp, 'Main Field')
            
            self.last_notification_time = current_time

        return frame

class VideoStreaming:
    def __init__(self, email_config, config_data):
        self.VIDEO = cv2.VideoCapture(0)
        self.DETECTOR = AnimalDetectionSystem(email_config, config_data)
        self._detect = False
        self._camera_on = True

    def reset_camera(self):
        self.VIDEO.release()
        self.VIDEO = cv2.VideoCapture(0)
        self._detect = False
        self._camera_on = True

    def generate_frames(self):
        while True:
            if not self._camera_on:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Camera OFF", (230, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.1)
                continue

            ret, frame = self.VIDEO.read()
            if not ret:
                break
            if self._detect:
                frame = self.DETECTOR.detect_animals(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
