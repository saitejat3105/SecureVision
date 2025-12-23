#db_utils.py
import sqlite3
from datetime import datetime, timedelta
from config import Config

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=None):
    """Execute query and return results"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def execute_insert(query, params):
    """Execute insert and return last row id"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_daily_stats(camera_id, date=None):
    """Get statistics for a specific day"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get intruder count
    cursor.execute('''
        SELECT COUNT(*) as count FROM intruder_logs 
        WHERE camera_id = ? AND date(timestamp) = ?
    ''', (camera_id, date))
    intruders = cursor.fetchone()['count']
    
    # Get weapon detections
    cursor.execute('''
        SELECT COUNT(*) as count FROM intruder_logs 
        WHERE camera_id = ? AND date(timestamp) = ? AND weapon_detected = 1
    ''', (camera_id, date))
    weapons = cursor.fetchone()['count']
    
    # Get masked detections
    cursor.execute('''
        SELECT COUNT(*) as count FROM intruder_logs 
        WHERE camera_id = ? AND date(timestamp) = ? AND mask_detected = 1
    ''', (camera_id, date))
    masked = cursor.fetchone()['count']
    
    conn.close()
    
    return {
        'date': date,
        'intruders': intruders,
        'weapons': weapons,
        'masked': masked
    }

def get_weekly_stats(camera_id):
    """Get statistics for the past week"""
    stats = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        daily = get_daily_stats(camera_id, date)
        stats.append(daily)
    
    return stats

def cleanup_old_logs(days=30):
    """Delete logs older than specified days"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM intruder_logs WHERE timestamp < ?', (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted

def log_activity(camera_id, event_type, description, severity='info'):
    """Log activity event"""
    import uuid
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO activity_logs (id, camera_id, event_type, description, severity)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(uuid.uuid4()), camera_id, event_type, description, severity))
    
    conn.commit()
    conn.close()