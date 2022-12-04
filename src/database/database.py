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
            CREATE TABLE IF NOT EXISTS pilots (
                pilot_id TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone_number TEXT,
                
                PRIMARY KEY (pilot_id)
            );""")

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS drones (
                pilot_id TEXT,
                serial_number TEXT,
                position_x REAL,
                position_y REAL,
                distance REAL,
                timestamp TIMESTAMP         NOT NULL,

                PRIMARY KEY (pilot_id),
                FOREIGN KEY (pilot_id) REFERENCES pilots (pilot_id) ON DELETE CASCADE
            );""")

        self.db.commit()
