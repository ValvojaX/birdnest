from src.violation_monitor.violation_monitor import ViolationMonitor, Drone, Pilot
from src.violation_manager.structs import ViolationData
from src.utils.delayed_task import DelayedTask
from src.database.database import Database
from datetime import datetime, timezone
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
            SELECT P.pilot_id, P.first_name, P.last_name, P.email, P.phone_number, 
                    D.serial_number, D.position_x, D.position_y, D.distance, DATETIME(D.timestamp, 'localtime')
            FROM pilots AS P
            INNER JOIN drones AS D ON P.pilot_id = D.pilot_id
            ORDER BY D.timestamp ASC
        """)

        rows = result.fetchall()
        violations: list[ViolationData] = []
        for pilot_id, first, last, email, phone, serial, pos_x, pos_y, distance, timestamp in rows:
            drone = Drone(serial_number=serial, position_x=pos_x, position_y=pos_y, distance=distance, timestamp=timestamp)
            drone.pilot = Pilot(pilot_id=pilot_id, first_name=first, last_name=last, email=email, phone_number=phone)

            violation_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            delete_after = max(self.delete_data_after - (datetime.now().timestamp() - violation_date.timestamp()), 0)
            if delete_after == 0:
                self._on_expire(drone)
                continue

            violation_data = ViolationData(delete_after=int(delete_after))
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
                WHERE pilot_id = ? AND STRFTIME('%S', 'now') - STRFTIME('%S', timestamp) > ?
            );
            """, (drone.pilot.pilot_id, self.delete_data_after / 60))

        # Handle case where drone violation has been updated since the violation was created
        has_expired = cursor.fetchone()[0]
        if not has_expired:
            return

        self.database.db.execute("""
            DELETE FROM pilots WHERE pilot_id = ?
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

        # Drone pilot information was not found
        if drone.pilot is None:
            return

        self.database.db.execute("""
            INSERT OR REPLACE INTO drones(pilot_id, serial_number, position_x, position_y, distance, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
            drone.pilot.pilot_id,
            drone.serial_number,
            drone.position_x,
            drone.position_y,
            drone.distance,
            drone.timestamp
        ))

        self.database.db.execute("""
            INSERT INTO pilots(pilot_id, first_name, last_name, email, phone_number)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (pilot_id) DO NOTHING""", (
            drone.pilot.pilot_id,
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