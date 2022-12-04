class Pilot:
    def __init__(self, first_name: str, last_name: str, email: str, phone_number: str) -> None:
        """
        Stores information about a pilot

        :param first_name: First name of the pilot
        :param last_name: Last name of the pilot
        :param email: Email of the pilot
        :param phone_number: Phone number of the pilot
        """

        self.first_name: str = first_name
        self.last_name: str = last_name
        self.email: str = email
        self.phone_number: str = phone_number

    def asdict(self) -> dict[str, str]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number
        }

    def __repr__(self) -> str:
        return f"""Pilot(
        first_name={self.first_name}, 
        last_name={self.last_name}, 
        email={self.email}, 
        phone_number={self.phone_number})"""


