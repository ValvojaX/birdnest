from src.violation_monitor.violation_monitor import ViolationMonitor, Drone, Pilot
from src.violation_manager.structs import ViolationData
from src.utils.delayed_task import DelayedTask
from src.database.database import Database
from typing import Callable


class ViolationManager:
    def __init__(self,
                 database: Database,
                 delete_data_after: int = 0,
                 ) -> None:
        """
        Stores violations in database and notifies listeners

        :param database: Database object
        :param delete_data_after: Time in seconds after which the violation data will be deleted from the database
        """

        self.database: Database = database
        self.delete_data_after: int = delete_data_after
        self.on_expire: Callable[[ViolationData], None] | None = None
        self.on_violation: Callable[[ViolationData], None] | None = None
        self.violation_monitor: ViolationMonitor | None = None

    def fetch_violations(self) -> list[ViolationData]:
        """
        Fetches all violations from the database

        :return: List of violations
        """

        result = self.database.db.execute("""
            SELECT drone_serial_number, first_name, last_name, email, phone_number
            FROM pilots
        """)

        rows = result.fetchall()
        pilots: dict[str, Pilot] = {}
        default_pilot = Pilot(first_name="Unknown", last_name="Unknown", email="Unknown", phone_number="Unknown")
        for serial_num, first, last, email, phone in rows:
            pilots[serial_num] = Pilot(first_name=first, last_name=last, email=email, phone_number=phone)

        result = self.database.db.execute("""
            SELECT serial_number, ROUND(position_x, 2), ROUND(position_y, 2), ROUND(distance, 2), timestamp, STRFTIME('%S', 'now') - STRFTIME('%S', timestamp)
            FROM drones
            WHERE timestamp > datetime('now', '-10 minutes')
            ORDER BY timestamp ASC
        """)

        violations: list[ViolationData] = []
        rows = result.fetchall()
        for serial_num, x, y, distance, timestamp, passed_time in rows:
            drone = Drone(serial_number=serial_num, position_x=x, position_y=y, distance=distance, timestamp=timestamp)
            drone.pilot = pilots.get(serial_num, default_pilot)

            delete_after = max(self.delete_data_after - passed_time, 0)
            violation_data = ViolationData(delete_after=delete_after)
            violation_data.from_drone(drone)
            violations.append(violation_data)

        return violations

    def _on_expire(self, drone: Drone) -> None:
        """
        Deletes expired violation data from the database and notifies listeners

        :param drone: Drone object
        :return: None
        """

        cursor = self.database.db.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM drones
                WHERE serial_number = ? AND STRFTIME('%S', 'now') - STRFTIME('%S', timestamp) > ?
            );
            """, (drone.serial_number, self.delete_data_after / 60))

        # Handle case where drone violation has been updated since the violation was created
        has_expired = cursor.fetchone()[0]
        if not has_expired:
            return

        self.database.db.execute("""
            DELETE FROM drones WHERE serial_number = ?
            """, (drone.serial_number,))

        self.database.db.execute("""
            DELETE FROM pilots WHERE drone_serial_number = ?
            """, (drone.serial_number,))

        self.database.db.commit()

        violation_data = ViolationData()
        violation_data.from_drone(drone)
        if self.on_expire is not None:
            self.on_expire(violation_data)

    def _on_violation(self, drone: Drone):
        """
        Stores violation data in the database and notifies listeners

        :param drone:
        :return: None
        """

        self.database.db.execute("""
            INSERT OR REPLACE INTO drones(serial_number, position_x, position_y, distance, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (
            drone.serial_number,
            drone.position_x,
            drone.position_y,
            drone.distance,
            drone.timestamp
        ))

        if drone.pilot is not None:
            self.database.db.execute("""
                INSERT INTO pilots(drone_serial_number, first_name, last_name, email, phone_number)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (drone_serial_number) DO NOTHING""", (
                drone.serial_number,
                drone.pilot.first_name,
                drone.pilot.last_name,
                drone.pilot.email,
                drone.pilot.phone_number,
            ))

        self.database.db.commit()
        violation_data = ViolationData(delete_after=self.delete_data_after)
        violation_data.from_drone(drone)

        if self.on_violation is not None:
            self.on_violation(violation_data)

        if self.delete_data_after > 0:
            delayed_task = DelayedTask(task=self._on_expire, delay=self.delete_data_after, drone=drone)
            delayed_task.start()

    def create_monitor(self, update_interval: int, ndz_origin: tuple[float, float], ndz_radius: int) -> None:
        """
        Creates a violation monitor object for manager

        :param update_interval: interval in seconds between drone position updates
        :param ndz_origin: origin of the no drone zone
        :param ndz_radius: radius of the no drone zone
        :return: None
        """

        self.violation_monitor = ViolationMonitor(callback=self._on_violation, update_interval=update_interval,
                                                  ndz_origin=ndz_origin, ndz_radius=ndz_radius)

    def start_monitor(self) -> None:
        """
        Starts the violation monitor

        :return: None
        """

        if self.violation_monitor is not None:
            self.violation_monitor.start()