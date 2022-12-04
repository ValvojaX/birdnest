from src.violation_monitor.drone import Drone


class OnViolationData(dict):
    def __init__(self, drone: Drone | None = None):
        super().__init__()
        if drone is not None:
            drone_data = drone.asdict()
            for key, value in drone_data.items():
                self[key] = value


class OnViolationExpiredData(dict):
    def __init__(self, drone: Drone | None = None):
        super().__init__()
        if drone is not None:
            drone_data = drone.asdict()
            for key, value in drone_data.items():
                self[key] = value
