#email_service.py
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from config import Config

class EmailService:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.email_address = Config.EMAIL_ADDRESS
        self.email_password = Config.EMAIL_PASSWORD
        self.recipient = Config.ALERT_RECIPIENT
        
        self.last_alert_time = {}
        self.cooldown = Config.INTRUDER_ALERT_COOLDOWN
    
    def send_alert(self, alert_type, description, image_path=None, camera_id=None, severity=5):
        """Send email alert with optional image"""
        # Check cooldown
        key = f"{camera_id}_{alert_type}"
        current_time = time.time()
        
        if key in self.last_alert_time:
            if current_time - self.last_alert_time[key] < self.cooldown:
                return False, "Alert cooldown active"
        
        self.last_alert_time[key] = current_time
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = self.recipient
        msg['Subject'] = f"🚨 SecureVision Alert: {alert_type.upper()}"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #eee; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 10px; padding: 20px;">
                <h1 style="color: #e94560; text-align: center;">⚠️ Security Alert</h1>
                
                <div style="background: #0f3460; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Alert Type:</strong> {alert_type}</p>
                    <p><strong>Camera ID:</strong> {camera_id}</p>
                    <p><strong>Severity:</strong> {severity}/10</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div style="background: #1a1a2e; padding: 15px; border-radius: 8px;">
                    <h3 style="color: #e94560;">Description</h3>
                    <p>{description}</p>
                </div>
                
                <p style="text-align: center; color: #888; margin-top: 20px;">
                    This is an automated alert from SecureVision Security System
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach image if provided
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                msg.attach(img)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            return True, "Alert sent successfully"
        except Exception as e:
            return False, str(e)
    
    def send_daily_report(self, camera_id, stats):
        """Send daily security report"""
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = self.recipient
        msg['Subject'] = f"📊 SecureVision Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #eee; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 10px; padding: 20px;">
                <h1 style="color: #0ea5e9; text-align: center;">📊 Daily Security Report</h1>
                
                <div style="background: #0f3460; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>Summary for Camera: {camera_id}</h3>
                    <ul>
                        <li>Total Detections: {stats.get('total_detections', 0)}</li>
                        <li>Known Faces: {stats.get('known_faces', 0)}</li>
                        <li>Unknown Faces: {stats.get('unknown_faces', 0)}</li>
                        <li>Alerts Triggered: {stats.get('alerts', 0)}</li>
                        <li>Weapons Detected: {stats.get('weapons', 0)}</li>
                    </ul>
                </div>
                
                <p style="text-align: center; color: #888; margin-top: 20px;">
                    SecureVision Security System - Daily Report
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            return True
        except:
            return False
    
    def send_camera_offline_alert(self, camera_id):
        """Send alert when camera goes offline"""
        return self.send_alert(
            'camera_offline',
            f'Camera {camera_id} appears to be offline or malfunctioning. Please check the device.',
            camera_id=camera_id,
            severity=8
        )