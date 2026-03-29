from datetime import date
from typing import Optional
from utils.data_utils import connect_to_db, execute_query

class Case:
    def __init__(self, id: int, client_name: str, product_number: str, summary: str, suggested_close_date: date, status: str, assignee: int):
        self.id = id
        self.client_name = client_name
        self.product_number = product_number
        self.summary = summary
        self.suggested_close_date = suggested_close_date
        self.status = status
        self.assignee = assignee

    @classmethod
    def create_case(cls, id: int, client_name: str, product_number: str, summary: str, suggested_close_date: date, status: str, assignee: int):
        db = connect_to_db()
        query = "INSERT INTO cases (id, client_name, product_number, summary, suggested_close_date, status, assignee) VALUES (?, ?, ?, ?, ?, ?, ?)"
        execute_query(db, query, (id, client_name, product_number, summary, suggested_close_date, status, assignee))
        db.commit()
        db.close()

    @classmethod
    def get_case(cls, id: int):
        db = connect_to_db()
        query = "SELECT * FROM cases WHERE id = ?"
        result = execute_query(db, query, (id,))
        db.close()
        if result:
            return Case(*result)
        else:
            return None

    @classmethod
    def update_case(cls, id: int, **kwargs):
        db = connect_to_db()
        query = "UPDATE cases SET "
        params = []
        for key, value in kwargs.items():
            query += f"{key} = ?, "
            params.append(value)
        query = query.rstrip(", ") + " WHERE id = ?"
        params.append(id)
        execute_query(db, query, tuple(params))
        db.commit()
        db.close()

    @classmethod
    def delete_case(cls, id: int):
        db = connect_to_db()
        query = "DELETE FROM cases WHERE id = ?"
        execute_query(db, query, (id,))
        db.commit()
        db.close()