import streamlit as st


def render_navbar():
    st.markdown(
        """
        <style>
        .navbar {
            background-color: #f8f9fa;
            padding: 0.5rem 1rem;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar-brand {
            font-size: 1.25rem;
            font-weight: 600;
            color: #212529;
        }
        .navbar-links {
            display: flex;
            gap: 1rem;
        }
        .navbar-links a {
            text-decoration: none;
            color: #495057;
            font-weight: 500;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        .navbar-links a:hover {
            background-color: #e9ecef;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="navbar">
            <div class="navbar-brand">AI-CSM</div>
            <div class="navbar-links">
                <a href="?page=dashboard">Dashboard</a>
                <a href="?page=kanban">Kanban</a>
                <a href="?page=new_ticket">New Ticket</a>
                <a href="?page=analytics">Analytics</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )