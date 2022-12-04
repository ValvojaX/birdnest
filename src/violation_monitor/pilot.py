class Pilot:
    def __init__(self, pilot_id: str, first_name: str, last_name: str, email: str, phone_number: str) -> None:
        """
        Stores information about a pilot

        :param pilot_id: ID of the pilot
        :param first_name: First name of the pilot
        :param last_name: Last name of the pilot
        :param email: Email of the pilot
        :param phone_number: Phone number of the pilot
        """

        self.pilot_id: str = pilot_id
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.email: str = email
        self.phone_number: str = phone_number

    def asdict(self) -> dict[str, str]:
        return {
            "pilot_id": self.pilot_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number
        }

    def __repr__(self) -> str:
        return f"""Pilot(
        pilot_id={self.pilot_id},
        first_name={self.first_name}, 
        last_name={self.last_name}, 
        email={self.email}, 
        phone_number={self.phone_number})"""


