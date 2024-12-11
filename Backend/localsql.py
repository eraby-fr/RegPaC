import sqlite3
import datetime
from flask import jsonify
import os

def get_remote_file_path()->str:
    return '/mnt/NAS/RegPac.db'

def get_local_ramfile_path()->str:
    return '/tmp/RegPac.db'

def remote_file_can_be_created()->bool:
    return False

def get_db_path()->str:
    if os.path.exists(get_remote_file_path()) or remote_file_can_be_created():
        sync_tmp_db_to_nas_db_if_necessary()
        return get_remote_file_path()
    else:
        return get_local_ramfile_path()
    
def need_to_sync()->bool:
    return os.path.exists(get_local_ramfile_path()) and os.path.exists(get_remote_file_path())

def create_heat_log_table_if_not_exists(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS heat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            state BOOLEAN
        )
    ''')

def log_heatvalue_if_change(on: bool):
    connection = sqlite3.connect(get_db_path())
    cursor = connection.cursor()

    create_heat_log_table_if_not_exists(cursor)
    
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

def create_temperature_log_table_if_not_exists(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temperature_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source1 REAL,
            source2 REAL,
            source3 REAL,
            source4 REAL
        )
    ''')

def log_temperatures(temperatures_sources: list):
    connection = sqlite3.connect(get_db_path())

    cursor = connection.cursor()
    create_temperature_log_table_if_not_exists(cursor)

    cursor.execute('''
        INSERT INTO temperature_log (source1, source2, source3, source4)
        VALUES (?, ?, ?, ?)
    ''', (temperatures_sources["1"], temperatures_sources["2"], temperatures_sources["3"], temperatures_sources["4"]))
    connection.commit()
    connection.close()

def retrieve_last_logged_temperature() -> list:
    path = get_db_path()
    if os.path.exists(path):
        connection = sqlite3.connect(path)
    else:
        raise Exception({"error": "Temperature log database not found"})
    
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM temperature_log ORDER BY timestamp DESC LIMIT 1")

    rows = cursor.fetchall()
    connection.close()

    return {'1': rows[0][2], '2': rows[0][3], '3': rows[0][4], '4': rows[0][5]}

def retrieve_logged_temperature(start_date: datetime, end_date:datetime) -> list:
    path = get_db_path()
    if os.path.exists(path):
        connection = sqlite3.connect(path)
    else:
        raise Exception({"error": "Temperature log database not found"})
    
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM temperature_log WHERE timestamp BETWEEN \'"\
                   + start_date.strftime('%Y-%m-%d %H:%M:%S') + "\' AND \'" + end_date.strftime('%Y-%m-%d %H:%M:%S')\
                   + "\' ORDER BY timestamp ASC")

    rows = cursor.fetchall()
    connection.close()

    log_entries = []
    for row in rows:
        log_entries.append({
            "id": row[0],
            "timestamp": row[1],
            "source1": row[2],
            "source2": row[3],
            "source3": row[4],
            "source4": row[5]
        })

    return log_entries

def sync_tmp_db_to_nas_db_if_necessary():
    if not need_to_sync():
        return

    temp_connection = sqlite3.connect(get_local_ramfile_path())
    nas_connection = sqlite3.connect(get_remote_file_path())

    source_cursor = temp_connection.cursor()
    destination_cursor = nas_connection.cursor()

    #duplicate heat log
    source_cursor.execute('SELECT * FROM heat_log')
    rows = source_cursor.fetchall()
    create_heat_log_table_if_not_exists(destination_cursor)
    destination_cursor.executemany('''
        INSERT INTO heat_log (timestamp, state)
        VALUES (?, ?)
    ''', rows)

    #duplicate temperature log
    source_cursor.execute('SELECT * FROM temperature_log')
    rows = source_cursor.fetchall()
    create_temperature_log_table_if_not_exists(destination_cursor)
    destination_cursor.executemany('''
        INSERT INTO temperature_log (timestamp, source1, source2, source3, source4)
        VALUES (?, ?, ?, ?, ?)
    ''', rows)

    nas_connection.commit()
    nas_connection.close()
    temp_connection.close()

    os.remove(get_local_ramfile_path())
