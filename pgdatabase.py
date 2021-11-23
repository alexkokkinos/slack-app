import os
import psycopg2
import logging

logging.basicConfig(level=logging.DEBUG)

class PGDatabase():
  def __init__(
    self,
    database=os.environ.get("DBNAME"),
    user=os.environ.get("DBUSER"),
    host=os.environ.get("DBHOST"),
    port=os.environ.get("PORT"),
    password=os.environ.get("DBPASSWORD")
  ):
    self.conn = psycopg2.connect(
      database=database,
      user=user,
      host=host,
      port=port,
      password=password
    )
    self.cursor = self.conn.cursor()

  def query(self, query, data=None):
    logging.debug(query)
    logging.debug(data)
    self.cursor.execute(query, data)

  def commit(self):
    self.conn.commit()

  def rollback(self):
    self.conn.rollback()

  def close(self):
    self.conn.commit()
    self.cursor.close()
    self.conn.close()

  def close_rollback(self):
    self.conn.rollback()
    self.cursor.close()
    self.conn.close()
