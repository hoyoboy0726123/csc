from datetime import date
from utils.data_utils import connect_to_db, execute_query

class Assignee:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @classmethod
    def create_assignee(cls, id: int, name: str):
        db = connect_to_db()
        query = "INSERT INTO assignees (id, name) VALUES (?, ?)"
        execute_query(db, query, (id, name))
        db.commit()
        db.close()

    @classmethod
    def get_assignee(cls, id: int):
        db = connect_to_db()
        query = "SELECT * FROM assignees WHERE id = ?"
        result = execute_query(db, query, (id,))
        db.close()
        if result:
            return Assignee(result[0][0], result[0][1])
        else:
            return None

    @classmethod
    def update_assignee(cls, id: int, **kwargs):
        db = connect_to_db()
        query = "UPDATE assignees SET "
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
    def delete_assignee(cls, id: int):
        db = connect_to_db()
        query = "DELETE FROM assignees WHERE id = ?"
        execute_query(db, query, (id,))
        db.commit()
        db.close()