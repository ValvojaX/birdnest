from src.violation_monitor.drone import Drone


class ViolationData:
    def __init__(self, delete_after: int = 0) -> None:
        """
        Contains information about a violation

        :param delete_after: Seconds after which the violation data will be deleted from the database. 0 means it will not be deleted.
        """

        # drone data
        self.serial_number: str = "Unknown"
        self.position_x: float | None = None
        self.position_y: float | None = None
        self.distance: float | None = None
        self.timestamp: str | None = None

        # pilot data
        self.first_name: str = "Unknown"
        self.last_name: str = "Unknown"
        self.email: str = "Unknown"
        self.phone_number: str = "Unknown"

        # violation data
        self.delete_after: int = delete_after

    def from_drone(self, drone: Drone) -> None:
        self.serial_number = drone.serial_number
        self.position_x = round(drone.position_x, 2)
        self.position_y = round(drone.position_y, 2)
        self.distance = round(drone.distance, 2)
        self.timestamp = drone.timestamp

        if drone.pilot is not None:
            self.first_name = drone.pilot.first_name
            self.last_name = drone.pilot.last_name
            self.email = drone.pilot.email
            self.phone_number = drone.pilot.phone_number

    def asdict(self) -> dict:
        return {
            "drone": {
                "serial_number": self.serial_number,
                "position_x": self.position_x,
                "position_y": self.position_y,
                "distance": self.distance,
            },
            "pilot": {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "email": self.email,
                "phone_number": self.phone_number
            },
            "delete_after": self.delete_after,
            "timestamp": self.timestamp
        }