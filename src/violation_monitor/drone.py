from time import time
from src.violation_monitor.pilot import Pilot


class Drone:
    def __init__(self,
                 serial_number: str,
                 position_x: float,
                 position_y: float,
                 distance: float = None,
                 timestamp: str = ""
                 ) -> None:
        """
        Stores information about a drone

        :param serial_number: Serial number of the drone
        :param position_x: X coordinate of the drone
        :param position_y: Y coordinate of the drone
        :param distance: Distance from the drone to the nest
        :param timestamp: Timestamp of the drone position
        """
        self.serial_number: str = serial_number
        self.position_x: float = position_x
        self.position_y: float = position_y
        self.distance: float | None = distance
        self.timestamp: str = timestamp
        self.pilot: Pilot | None = None

    def asdict(self) -> dict[str, str | float]:
        return {
            "serial_number": self.serial_number,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "distance": self.distance,
            "timestamp": self.timestamp,
            "pilot": self.pilot.asdict() if self.pilot is not None else None
        }

    def __repr__(self) -> str:
        return f"""Drone(
        serial_number={self.serial_number}, 
        position_x={self.position_x}, 
        position_y={self.position_y})"""