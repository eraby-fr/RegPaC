import sqlite3
import datetime
from flask import jsonify
import os

db_path: str = '/mnt/NAS/heat_log.db'
temp_db_path: str = '/tmp/heat_log.db'

def get_db_path()->str:
    global db_path, temp_db_path
    if os.path.exists(db_path):
        return db_path
    else:
        return temp_db_path
    
def need_to_sync()->bool:
    global db_path, temp_db_path
    return os.path.exists(temp_db_path) and os.path.exists(db_path)

def log_heatvalue_if_change(on: bool):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS heat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            state BOOLEAN
        )
    ''')
    
    # Check last entry
    cursor.execute('''
        SELECT state FROM heat_log
        ORDER BY timestamp DESC
        LIMIT 1
    ''')
    last_state = cursor.fetchone()

    # Update if state has changed
    if last_state is None or last_state[0] != on:
        cursor.execute('''
            INSERT INTO heat_log (state)
            VALUES (?)
        ''', (on,))

    connection.commit()
    connection.close()

    if need_to_sync():
        sync_heat_db_to_nas()

def retrieve_heat_values(start_date: datetime, end_date:datetime) -> list:
    path = get_db_path()
    if os.path.exists(path):
        connection = sqlite3.connect(path)
    else:
        raise Exception({"error": "Temperature log database not found"})
    
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM heat_log WHERE timestamp BETWEEN \'"\
                   + start_date.strftime('%Y-%m-%d %H:%M:%S') + "\' AND \'" + end_date.strftime('%Y-%m-%d %H:%M:%S')\
                   + "\' ORDER BY timestamp ASC")

    rows = cursor.fetchall()
    connection.close()

    log_entries = []
    for row in rows:
        log_entries.append({
            "id": row[0],
            "timestamp": row[1],
            "state": row[2]
        })

    return log_entries

def log_temperatures(temperatures_sources):
    global db_path, temp_db_path

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

    if need_to_sync():
        sync_temp_db_to_nas()

def retrieve_logged_temperature():
    global db_path, temp_db_path

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
    global db_path, temp_db_path

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
    global db_path, temp_db_path

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