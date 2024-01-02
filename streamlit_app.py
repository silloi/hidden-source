import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from helper.db import initialize_and_create_connection

#
# Initialization
# 

st.set_page_config(page_title="HiddenSource", initial_sidebar_state="auto", page_icon="🧪")

conn = initialize_and_create_connection(st)


#
# Side bar
#

st.sidebar.header("📅 Journal")

# NOTE: Journal - daily / weekly / monthly
is_filtered_by_date = st.sidebar.checkbox("Filter by date")

date_selected = st.sidebar.date_input("Dates", "today")

# if is_filtered_by_date and date_selected:
#     st.session_state.messages = messages[messages.timestamp.dt.date == date_selected].to_dict(orient="records")

st.sidebar.divider()

st.sidebar.header("📝 Project")

# NOTE: Project - open / closed / archived
is_filtered_by_project = st.sidebar.checkbox("Filter by project")

with st.sidebar.expander("Create new project"):
    with st.form("new_project", border=False):
        project_name_input = st.text_input("Project name")
        project_submit_button = st.form_submit_button("Create")

    if project_submit_button and project_name_input:
        with conn.session as s:
            s.execute(
                "INSERT INTO projects (name, timestamp) VALUES (:name, :timestamp);",
                params=dict(name=project_name_input, timestamp=datetime.now())
            )
            s.commit()

        # st.session_state.projects.insert(0, {"id": "random", "name": project_name_input, "timestamp": datetime.now()})

# Sort descending by timestamp
projects = conn.query("SELECT * FROM projects ORDER BY timestamp DESC")

if not projects.empty:
    st.session_state.projects = projects.to_dict(orient="records")
else:
    st.session_state.projects = []

# filter messages by project
project_id_selected = st.sidebar.radio("Projects", [project["id"] for project in st.session_state.projects], format_func=lambda id: projects[projects.id == id].iloc[0]["name"] if not projects[projects.id == id].empty else "")

# Area - other tag

# Resource - closed tag

st.sidebar.divider()


#
# Tags
#

# if "selected_tags" not in st.session_state:
#     st.session_state.selected_tags = []

# # with st.sidebar.expander("Tags", expanded=False):
# with st.sidebar.expander("Areas", expanded=False):
#     # is_tag_selected = st.sidebar.checkbox("#work", key="work")
#     st.checkbox("#work", key="work")

# if is_tag_selected:
#     st.session_state.selected_tags.append("#work")
# elif "#work" in st.session_state.selected_tags:
#     st.session_state.selected_tags.remove("#work")

# st.sidebar.divider()


#
# Pinned & Archived
#

# is_filtered_by_pinned = st.sidebar.checkbox("📌 Pinned")
# is_filtered_by_archived = st.sidebar.checkbox("🗑️ Archived")


#
# Main content
#

if is_filtered_by_project and project_id_selected:
    st.title(projects.get(project_id_selected))
elif is_filtered_by_date and date_selected:
    st.title(date_selected.strftime("%Y/%m/%d"))
# elif len(st.session_state.selected_tags) > 0:
#     st.title(" ".join(st.session_state.selected_tags))
else:
    st.title("🧪 HiddenSource")


# Query and display the data you inserted
if is_filtered_by_date and date_selected:
    messages = conn.query("SELECT * FROM messages WHERE timestamp >= :today AND timestamp < :next", params={"today": date_selected, "next": date_selected + timedelta(days=1)})
else:
    messages = conn.query("SELECT * FROM messages")

# Convert the 'timestamp' column to a datetime type
messages['timestamp'] = pd.to_datetime(messages['timestamp'])

# Populate project by project_id
messages['project'] = messages["project_id"].apply(lambda id: (conn.query("SELECT * FROM projects WHERE id = :id", params={"id": id}).iloc[0].to_dict() if not conn.query("SELECT * FROM projects WHERE id = :id", params={"id": id}).empty else None) if id else None)

if not messages.empty:
    if is_filtered_by_project:
        messages = messages[messages.project.apply(lambda project: project["id"] == project_id_selected if project else False)]
    # if is_filtered_by_archived:
    #     messages = messages[messages.archived == True]
    # if is_filtered_by_pinned:
    #     messages = messages[messages.pinned == True]

    st.session_state.messages = messages.to_dict(orient="records")
else:
    st.session_state.messages = []

# dates = messages.timestamp.dt.date.unique()


#
# Main content
# 

# Summary

if not is_filtered_by_date and not is_filtered_by_project:
    st.info("Welcome to HiddenSource! This is a demo of a chat app built with Streamlit. Feel free to send a message to get started.")
    st.info("""
            - 📅 Filter by date
            - 📝 Filter by project
            - 📌 (Unimplemented) Pin a message to keep it at the top of the chat
            - 🗑️ (Unimplemented) Archive a message to hide it from the chat
    """)
elif len(st.session_state.messages) > 0:
    st.button("Generate Summary", on_click=lambda: st.sidebar.success("(Unimplemented) Summary generated!"))
else:
    st.info("No activities found.")


# Chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["timestamp"]:
            then = message["timestamp"].strftime('%H:%M:%S') if is_filtered_by_date and date_selected else message["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
            st.markdown(f"`{then}`")
        st.markdown(message["content"])
        # # checkbox in chat_message is not working
        # st.checkbox("📌", value=message["pinned"], key=f"pinned-{message['id']}", on_change=toggle_pinned(message["id"], message["pinned"]))
        # st.checkbox("🗑️", value=message["archived"], key=f"archived-{message['id']}", on_change=toggle_archived(message["id"], message["archived"]))


# Chat input
post = ""
if not is_filtered_by_date or date_selected == date.today():
    post = st.chat_input("What happened?")

if post:
    now = datetime.now()

    with st.chat_message("user"):
        st.markdown(f"`{now.strftime('%H:%M:%S')}`")
        st.markdown(post)
        # st.checkbox("Pin", value=False)
        # st.checkbox("Archive", value=False)

    # project_id = conn.query("SELECT * FROM projects WHERE id = :id", params={"id": project_id_selected}).iloc[0]["id"] if is_filtered_by_project and project_id_selected else ""
    st.session_state.messages.append({"content": post, "timestamp": now, "role": "user", "project_id": project_id_selected, "archived": False, "pinned": False})

    # Insert some data with conn.session
    if is_filtered_by_project and project_id_selected:
        with conn.session as s:
            s.execute(
                "INSERT INTO messages (content, role, project_id, timestamp) VALUES (:message, :role, :project_id, :timestamp);",
                params=dict(message=post, role="user", project_id=int(project_id_selected), timestamp=now)
            )
            s.commit()
    else:
        with conn.session as s:
            s.execute(
                "INSERT INTO messages (content, role, timestamp) VALUES (:message, :role, :timestamp);",
                params=dict(message=post, role="user", timestamp=now)
            )
            s.commit()
