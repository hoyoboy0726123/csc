import streamlit as st
from models.assignee import get_assignee, update_assignee
from components.assignee_table import AssigneeTable

def main():
    st.title("Assignee List")
    assignees = get_assignee()
    assignee_table = AssigneeTable(assignees)
    assignee_table.display()

    with st.form("update_assignee"):
        assignee_id = st.selectbox("Select Assignee", [a.id for a in assignees])
        name = st.text_input("Name")
        submitted = st.form_submit_button("Update")
        if submitted:
            update_assignee(assignee_id, name=name)

if __name__ == "__main__":
    main()