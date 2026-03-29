import os
import uuid
from datetime import date
from typing import Dict

import streamlit as st
from streamlit import caching
from streamlit.scriptrunner import script_runner

from models.case import Case
from utils.data_utils import connect_to_db, execute_query

class OutlookService:
    def __init__(self):
        self.db_connection = connect_to_db()

    def send_email(self, case_id: int, recipient: str, subject: str, body: str) -> None:
        # Implement email sending logic here
        case = Case.get_case(case_id)
        if case:
            # Use case information to construct the email
            st.write(f"Sending email for case {case_id} to {recipient}")
        else:
            st.error(f"Case {case_id} not found")

    def get_draft_folder(self) -> Dict:
        # Implement logic to retrieve draft folder
        draft_folder = {}
        return draft_folder

def main():
    st.title("Outlook Service")
    outlook_service = OutlookService()

    case_id = st.number_input("Enter case ID", min_value=1)
    recipient = st.text_input("Enter recipient email")
    subject = st.text_input("Enter email subject")
    body = st.text_area("Enter email body")

    if st.button("Send Email"):
        outlook_service.send_email(int(case_id), recipient, subject, body)

if __name__ == "__main__":
    main()