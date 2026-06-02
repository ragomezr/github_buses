import os
import psycopg2
import requests
import time
import sys
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2


URL = "https://exo.chrono-saeiv.com/api/opendata/v1/STS/vehicleposition?token=ed02f9a16ccc44f1b3ee37d704db5bfd"
DATABASE_URL = os.environ.get("DATABASE_URL")

def obtener_conexion():
    # Si estás probando local, puedes poner tu cadena de conexión directa aquí temporalmente
    if not DATABASE_URL:
        raise ValueError("La variable de entorno DATABASE_URL no está configurada.")
    return psycopg2.connect(DATABASE_URL)

    

def crear_db():
    conn = obtener_conexion()
    cursor = conn.cursor()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT,
            vehicle_id  TEXT,
            route_id    TEXT,
            lat         REAL,
            lon         REAL,
            speed_kmh   REAL,
            bearing     REAL,
            stop_id     TEXT,
            status      INTEGER
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def guardar_snapshot():
    response = requests.get(URL, timeout=10)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    
    conn = sqlite3.connect(DB_PATH)
    count = 0
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            v = entity.vehicle
            timestamp = datetime.fromtimestamp(v.timestamp, tz=timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO snapshots 
                (timestamp, vehicle_id, route_id, lat, lon, speed_kmh, bearing, stop_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                v.vehicle.id,
                v.trip.route_id,
                v.position.latitude,
                v.position.longitude,
                round(v.position.speed * 3.6, 1),
                v.position.bearing,
                v.stop_id,
                v.current_status
            ))
            count+= 1

    conn.commit()
    conn.close()
    print(f"{timestamp} +{count} vehicles saved")

if __name__ == "__main__":
    crear_db()
    print("Saving data every 20s... (Ctrl+C to quit)")
    while True:
        try:
            guardar_snapshot()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(20)