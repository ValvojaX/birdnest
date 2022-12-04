from flask import Flask, render_template, request
from flask_socketio import SocketIO
from src.violation_manager.violation_manager import ViolationManager, OnViolationData, OnViolationExpiredData
from src.database.database import Database
from os import getenv


class Birdnest(Flask):
    def __init__(self, database: Database, violation_manager: ViolationManager):
        super().__init__(__name__)
        self.database: Database = database
        self.violation_manager: ViolationManager = violation_manager


database = Database(":memory:")
violation_manager = ViolationManager(database=database, delete_data_after=600)
birdnest_app = Birdnest(database=database, violation_manager=violation_manager)
birdnest_app.config['SECRET_KEY'] = getenv('FLASK_SECRET', 'secret')
socketio = SocketIO(birdnest_app)


@birdnest_app.route('/')
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
    violations = birdnest_app.violation_manager.fetch_violations()
    socketio.emit('on_receive_cached_violations', violations, to=request.sid)


def on_expire(data: OnViolationExpiredData) -> None:
    socketio.emit('on_violation_expired', data, broadcast=True)


def on_violation(data: OnViolationData) -> None:
    socketio.emit('on_violation', data, broadcast=True)


def start():
    violation_manager.on_violation = on_violation
    violation_manager.on_violation_expired = on_expire

    violation_manager.create_monitor(
        update_interval=2,
        ndz_origin=(250000, 250000),
        ndz_radius=100
    )

    violation_manager.start_monitor()
    socketio.run(birdnest_app)


# if __name__ == '__main__':
#     start()