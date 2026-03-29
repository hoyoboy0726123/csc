import streamlit as st
import pandas as pd
from models.assignee import get_assignee, update_assignee
from utils.data_utils import connect_to_db, execute_query

def get_assignee_table():
    db_connection = connect_to_db()
    assignees = execute_query("SELECT * FROM assignees", ())
    assignees_df = pd.DataFrame(assignees, columns=['id', 'name'])
    return assignees_df

def update_assignee_table(assignee_id, new_name):
    update_assignee(assignee_id, name=new_name)

def render_assignee_table():
    assignees_df = get_assignee_table()
    st.write(assignees_df)

    with st.form("update_assignee"):
        assignee_id = st.selectbox("選擇負責人", options=assignees_df['id'].tolist())
        new_name = st.text_input("輸入新名稱")
        submitted = st.form_submit_button("更新")

        if submitted:
            update_assignee_table(assignee_id, new_name)
            st.success("負責人名稱已更新")

if __name__ == "__main__":
    render_assignee_table()