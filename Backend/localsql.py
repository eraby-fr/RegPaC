import sqlite3
from flask import jsonify
import os

def log_heatvalue_if_change(on: bool):
    db_path = '/mnt/NAS/heat_log.db'
    temp_db_path = '/tmp/heat_log.db'
    
    if os.path.exists(db_path):
        connection = sqlite3.connect(db_path)
    else:
        connection = sqlite3.connect(temp_db_path)
    
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS heat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            state BOOLEAN
        )
    ''')
    cursor.execute('''
        INSERT INTO heat_log (state)
        VALUES (?)
    ''', (on,))
    connection.commit()
    connection.close()

    if os.path.exists(db_path) and os.path.exists(temp_db_path):
        sync_heat_db_to_nas()

def log_temperatures(temperatures_sources):
    db_path = '/mnt/NAS/temperature_log.db'
    temp_db_path = '/tmp/temperature_log.db'

    if os.path.exists(db_path):
        connection = sqlite3.connect(db_path)
    else:
        connection = sqlite3.connect(temp_db_path)

    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temperature_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source1 REAL,
            source2 REAL,
            source3 REAL
        )
    ''')
    cursor.execute('''
        INSERT INTO temperature_log (source1, source2, source3)
        VALUES (?, ?, ?)
    ''', (temperatures_sources["1"], temperatures_sources["2"], temperatures_sources["3"]))
    connection.commit()
    connection.close()

    if os.path.exists(db_path) and os.path.exists(temp_db_path):
        sync_temp_db_to_nas()

def retrieve_logged_temperature():
    db_path = '/mnt/NAS/temperature_log.db'
    temp_db_path = '/tmp/temperature_log.db'

    if os.path.exists(db_path):
        connection = sqlite3.connect(db_path)
    elif os.path.exists(temp_db_path):
        connection = sqlite3.connect(temp_db_path)
    else:
        raise Exception({"error": "Temperature log database not found"})
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM temperature_log
        WHERE timestamp BETWEEN ? AND ?
    ''', (start_date, end_date))

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        return jsonify({"message": "No data found for the given date range"}), 404

    log_entries = []
    for row in rows:
        log_entries.append({
            "id": row[0],
            "timestamp": row[1],
            "source1": row[2],
            "source2": row[3],
            "source3": row[4]
        })

    return jsonify(log_entries), 200

def sync_temp_db_to_nas():
    db_path = '/mnt/NAS/temperature_log.db'
    temp_db_path = '/tmp/temperature_log.db'

    if not os.path.exists(temp_db_path):
        return

    nas_connection = sqlite3.connect(db_path)
    temp_connection = sqlite3.connect(temp_db_path)

    nas_cursor = nas_connection.cursor()
    temp_cursor = temp_connection.cursor()

    temp_cursor.execute('SELECT * FROM temperature_log')
    rows = temp_cursor.fetchall()
    nas_cursor.executemany('''
        INSERT INTO temperature_log (timestamp, source1, source2, source3)
        VALUES (?, ?, ?, ?)
    ''', rows)

    nas_connection.commit()
    nas_connection.close()
    temp_connection.close()

    os.remove(temp_db_path)

def sync_heat_db_to_nas():
    db_path = '/mnt/NAS/heat_log.db'
    temp_db_path = '/tmp/heat_log.db'

    if not os.path.exists(temp_db_path):
        return

    nas_connection = sqlite3.connect(db_path)
    temp_connection = sqlite3.connect(temp_db_path)

    nas_cursor = nas_connection.cursor()
    temp_cursor = temp_connection.cursor()

    temp_cursor.execute('SELECT * FROM heat_log')
    rows = temp_cursor.fetchall()
    nas_cursor.executemany('''
        INSERT INTO heat_log (timestamp, state)
        VALUES (?, ?)
    ''', rows)

    nas_connection.commit()
    nas_connection.close()
    temp_connection.close()

    os.remove(temp_db_path)