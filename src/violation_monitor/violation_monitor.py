import requests
from threading import Thread
from xml.etree import ElementTree
from typing import Callable
from time import sleep

from src.violation_monitor.drone import Drone
from src.violation_monitor.pilot import Pilot
from src.violation_monitor.exceptions import PilotNotFoundException


class ViolationMonitor(Thread):
    def __init__(self,
                 callback: Callable[[Drone], None],
                 update_interval: int = 2,
                 ndz_origin: tuple[float, float] = (0, 0),
                 ndz_radius: float = 100
                 ) -> None:
        """
        :param callback: Callback function to call when drone is in No-Drone-Zone
        :param update_interval: Interval in seconds to check for drones in No-Drone-Zone
        :param ndz_origin: Origin of No-Drone-Zone
        :param ndz_radius: Radius of No-Drone-Zone
        """

        super().__init__()

        self.update_interval: int = update_interval
        self.ndz_origin: tuple[float, float] = ndz_origin
        self.ndz_radius: float = ndz_radius
        self.callback: Callable[[Drone], None] = callback
        self.__stopped: bool = False

    @staticmethod
    def fetch_pilot_info(serial_number: str) -> Pilot:
        """
        Fetch pilot information by drone serial number.

        :param serial_number: Serial number of the drone
        :return: Pilot: Pilot information

        :raises PilotNotFoundException: If pilot information is not found
        """
        response = requests.get(f"https://assignments.reaktor.com/birdnest/pilots/{serial_number}")
        if response.status_code == 200:
            data = response.json()
            return Pilot(
                pilot_id=data["pilotId"],
                first_name=data["firstName"],
                last_name=data["lastName"],
                email=data["email"],
                phone_number=data["phoneNumber"]
            )

        elif response.status_code == 404:
            raise PilotNotFoundException

        raise PilotNotFoundException(f"Unknown error: {response.status_code}")

    @staticmethod
    def fetch_drone_positions() -> list[Drone]:
        """
        Fetch drone positions from the drone API.

        :return: list[Drone]: List of drones
        """
        drones = []
        response = requests.get("https://assignments.reaktor.com/birdnest/drones")
        if response.status_code == 200:
            xml_string = response.text
            device_information, capture = ElementTree.fromstring(xml_string)
            for drone in capture:
                drones.append(Drone(
                    serial_number=drone.find("serialNumber").text,
                    position_x=float(drone.find("positionX").text),
                    position_y=float(drone.find("positionY").text),
                    timestamp=capture.attrib.get("snapshotTimestamp")
                ))

        return drones

    def calculate_distance(self, drone: Drone) -> float:
        """
        Calculate distance between drone and NDZ origin.

        :param drone: Drone to calculate distance from
        :return: float: Distance
        """
        return (((drone.position_x - self.ndz_origin[0]) ** 2 + (
                    drone.position_y - self.ndz_origin[1]) ** 2) ** 0.5) / 1000

    def is_drone_in_ndz(self, drone: Drone) -> bool:
        """
        Check if drone is in the no-drone-zone (NDZ).

        :param drone: Drone to check
        :return: bool: True if drone is in NDZ, False otherwise
        """

        return drone.distance <= self.ndz_radius

    def stop(self) -> None:
        """
        Stop the violation monitor.

        :return: None
        """
        self.__stopped = True

    def run(self) -> None:
        while not self.__stopped:
            drones = self.fetch_drone_positions()
            for drone in drones:
                drone.distance = self.calculate_distance(drone)
                if self.is_drone_in_ndz(drone):
                    try:
                        drone.pilot = self.fetch_pilot_info(drone.serial_number)
                    except PilotNotFoundException:
                        drone.pilot = None

                    self.callback(drone)

            sleep(self.update_interval)
