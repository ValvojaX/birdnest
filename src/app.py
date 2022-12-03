from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
from time import time
from src.violation_monitor.violation_monitor import ViolationMonitor, Drone, Pilot
from src.database.database import Database
from src.utils.delayed_task import DelayedTask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)

database: Database | None = None
violation_monitor: ViolationMonitor | None = None
delete_data_after = 60 * 10 # 10 minutes


def fetch_violations():
    result = database.db.execute("""
        SELECT drone_serial_number, first_name, last_name, email, phone_number
        FROM pilots
    """)

    rows = result.fetchall()
    pilots: dict[str, Pilot] = {}
    default_pilot = Pilot(first_name="Unknown", last_name="Unknown", email="Unknown", phone_number="Unknown")
    for serial_num, first, last, email, phone in rows:
        pilots[serial_num] = Pilot(first_name=first, last_name=last, email=email, phone_number=phone)

    result = database.db.execute("""
        SELECT serial_number, ROUND(position_x, 2), ROUND(position_y, 2), ROUND(distance, 2), timestamp, STRFTIME('%S', 'now') - STRFTIME('%S', timestamp)
        FROM drones
        WHERE timestamp > datetime('now', '-10 minutes')
        ORDER BY timestamp DESC
    """)

    drones: list[Drone] = []
    rows = result.fetchall()
    for serial_num, x, y, distance, timestamp, passed_time in rows:
        drone = Drone(serial_number=serial_num, position_x=x, position_y=y, distance=distance, timestamp=timestamp)
        drone.delete_after = max(delete_data_after - passed_time, 0)
        drone.pilot = pilots.get(serial_num, default_pilot)
        drones.append(drone)

    return drones


@app.route('/')
def home():
    return render_template('home.html', title="Birdnest")


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('request_cached_violations')
def handle_get_cached_violations():
    violations = fetch_violations()
    violations = [violation.asdict() for violation in violations]
    socketio.emit('on_receive_cached_violations', violations, to=request.sid)


def on_expire(drone: Drone):
    database.db.execute("""
        DELETE FROM drones WHERE serial_number = ?
    """, (drone.serial_number,))

    database.db.commit()
    socketio.emit('on_expire', drone.asdict(), broadcast=True)


def on_violation(drone: Drone):
    database.db.execute("""
        INSERT INTO drones(serial_number, position_x, position_y, distance, timestamp)
        VALUES (?, ?, ?, ?, ?)""", (
        drone.serial_number,
        drone.position_x,
        drone.position_y,
        drone.distance,
        drone.timestamp,
    ))

    if drone.pilot is not None:
        database.db.execute("""
            INSERT INTO pilots(drone_serial_number, first_name, last_name, email, phone_number)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (drone_serial_number) DO NOTHING""", (
            drone.serial_number,
            drone.pilot.first_name,
            drone.pilot.last_name,
            drone.pilot.email,
            drone.pilot.phone_number,
        ))

    database.db.commit()
    drone.delete_after = delete_data_after
    violation_data = drone.asdict()
    violation_data['distance'] = round(violation_data['distance'], 2)
    violation_data['position_x'] = round(violation_data['position_x'], 2)
    violation_data['position_y'] = round(violation_data['position_y'], 2)
    socketio.emit('on_violation', violation_data, broadcast=True)

    delayed_task = DelayedTask(task=on_expire, delay=600, drone=drone)
    delayed_task.start()


if __name__ == '__main__':
    database = Database(":memory:")
    violation_monitor = ViolationMonitor(
        callback=on_violation,
        update_interval=2,
        ndz_origin=(250000, 250000),
        ndz_radius=100
    )

    violation_monitor.start()
    socketio.run(app, allow_unsafe_werkzeug=True)