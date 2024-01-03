from datetime import datetime

def insert_message(conn, message, role="user", project_id=None):
    now = datetime.now()

    if project_id:
        with conn.session as s:
            s.execute(
                "INSERT INTO messages (content, role, project_id, timestamp) VALUES (:message, :role, :project_id, :timestamp);",
                params=dict(message=message, role=role, project_id=int(project_id), timestamp=now)
            )
            s.commit()
    else:
        with conn.session as s:
            s.execute(
                "INSERT INTO messages (content, role, timestamp) VALUES (:message, :role, :timestamp);",
                params=dict(message=message, role=role, timestamp=now)
            )
            s.commit()

def insert_summary(conn, message_id, project_id=None, date=None):
    now = datetime.now()

    if project_id:
        with conn.session as s:
            s.execute(
                "INSERT INTO summaries (message_id, project_id, timestamp) VALUES (:message_id, :project_id, :timestamp);",
                params=dict(message_id=message_id, project_id=int(project_id), timestamp=now)
            )
            s.commit()
    else:
        with conn.session as s:
            s.execute(
                "INSERT INTO summaries (message_id, timestamp) VALUES (:message_id, :timestamp);",
                params=dict(message_id=message_id, timestamp=now)
            )
            s.commit()

def update_pinned(conn, id, value):
    with conn.session as s:
        print(id, value)
        s.execute(
            "UPDATE messages SET pinned = :value WHERE id = :id;",
            params=dict(value=value, id=id)
        )
        s.commit()

def update_archived(conn, id, value):
    with conn.session as s:
        s.execute(
            "UPDATE messages SET archived = :value WHERE id = :id;",
            params=dict(value=value, id=id)
        )
        s.commit()

def generate_summary(conn, client, st, project_id=None, project_name=None, date=None):
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        message_history_all = st.session_state.messages.copy()
        message_history = filter(lambda m: not m["archived"], message_history_all)

        if project_id and project_name:
            messages_history = [{"role": m["role"], "content": m["content"]} for m in message_history]
            messages_history.append({"role": "system", "content": f"Based on the user's previous message logs, summarize the contents of the project named {project_name}."})
        elif date:
            messages_history = [{"role": m["role"], "content": m["timestamp"].strftime("%Y-%m-%d %H:%M:%S") + "\n" + m["content"]} for m in message_history]
            messages_history.append({"role": "user", "content": f"Considering the timestamp placed in each first line of contents, summarize the day {date}."})

        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # get the latest message id
    latest_message_id = conn.query("SELECT * FROM messages ORDER BY id DESC LIMIT 1").iloc[0]["id"]
    latest_message_id = int(latest_message_id)
    if project_id:
        insert_message(conn, full_response, role="assistant", project_id=project_id)
        insert_summary(conn, latest_message_id + 1, project_id=project_id)
    else:
        insert_message(conn, full_response, role="assistant")
        insert_summary(conn, latest_message_id + 1)
