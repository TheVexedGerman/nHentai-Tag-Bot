import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import psycopg2
import time

import postgres_credentials

class Database:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(Database)
            return cls.instance
        return cls.instance

    def __init__(self):
        # self._conn = psycopg2.connect(
        #     host = postgres_credentials.HOST,
        #     database = postgres_credentials.DATABASE,
        #     user = postgres_credentials.USER,
        #     password = postgres_credentials.PASSWORD
        # )
        # self._cursor = self._conn.cursor()
        self.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit()
        self.connection.close()
    
    def connect(self):
        while True:
            try:
                self._conn = psycopg2.connect(
                    host = postgres_credentials.HOST,
                    database = postgres_credentials.DATABASE,
                    user = postgres_credentials.USER,
                    password = postgres_credentials.PASSWORD
                )
                self._cursor = self._conn.cursor()
                return
            except (psycopg2.OperationalError):
                time.sleep(30)
                continue

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        try:
            self.connection.commit()
        except (AttributeError, psycopg2.OperationalError):
            self.connect()
            self.connection.commit()

    def execute(self, sql, params=None):
        try:
            self.cursor.execute(sql, params or ())
        except (AttributeError, psycopg2.OperationalError):
            self.connect()
            self.cursor.execute(sql, params or ())

    def fetchall(self):
        try:
            return self.cursor.fetchall()
        except (AttributeError, psycopg2.OperationalError):
            self.connect()
            return self.cursor.fetchall()

    def fetchone(self):
        try:
            return self.cursor.fetchone()
        except (AttributeError, psycopg2.OperationalError):
            self.connect()
            return self.cursor.fetchone()

    def query(self, sql, params=None):
        try:
            self.cursor.execute(sql, params or ())
            return self.fetchall()
        except (AttributeError, psycopg2.OperationalError):
            self.connect()
            self.cursor.execute(sql, params or ())
            return self.fetchall()