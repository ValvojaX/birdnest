import sqlite3


class Database:
    def __init__(self, db_dsn: str) -> None:
        """
        Database wrapper for sqlite3..
        """

        self.db: sqlite3.Connection = sqlite3.connect(db_dsn, check_same_thread=False)
        self.ensure_tables()

    def ensure_tables(self) -> None:
        """
        Ensure that the database has the required tables.

        :return: None
        """
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS drones (
                serial_number TEXT,
                position_x REAL,
                position_y REAL,
                distance REAL,
                timestamp TIMESTAMP,
                delete_at TIMESTAMP,
                
                PRIMARY KEY (serial_number, timestamp)
            );""")

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS pilots (
                drone_serial_number TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone_number TEXT,
                timestamp TIMESTAMP,
                
                PRIMARY KEY (drone_serial_number),
                FOREIGN KEY (drone_serial_number) REFERENCES drones(serial_number)
            );""")

        self.db.commit()
