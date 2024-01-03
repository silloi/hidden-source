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
                "INSERT INTO summaries (message_id, date, timestamp) VALUES (:message_id, :date, :timestamp);",
                params=dict(message_id=message_id, date=date, timestamp=now)
            )
            s.commit()

def update_pinned(conn, id, value):
    with conn.session as s:
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

def convert_messages_to_log(conn, client, st, messages, has_ymd=False):
    events = []

    if len(messages) == 0:
        st.warning("No messages to export.")
        return

    for message in messages:
        if message["role"] == "user":
            if has_ymd:
                events += "\n".join([message["timestamp"].strftime("%Y-%m-%d %H:%M:%S"), message["content"]])
            else:
                events += "\n".join([message["timestamp"].strftime("%H:%M:%S"), message["content"]])

    return "\n\n".join(events)

def generate_summary(conn, client, st, project_id=None, project_name=None, date=None):
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        message_history_all = st.session_state.messages.copy()
        message_history = list(filter(lambda m: not m["archived"], message_history_all))

        if project_id and project_name:
            history_log = convert_messages_to_log(conn, client, st, message_history, has_ymd=True)
            prompt = f"""The following text is a formatted log in the project named {project_name}. Considering that, summarize it briefly. Do not use English unless the original text is written in it.
===
Log:
{history_log}
===
Summary:
"""
        elif date:
            history_log = convert_messages_to_log(conn, client, st, message_history, has_ymd=False)
            prompt = f"""The following text is a formatted log in the journal on {date}. Considering that, summarize it briefly. Do not use English unless the original text is written in it.
===
Log:
{history_log}
===
Summary:
"""
        prompt_message = ({"role": "user", "content": prompt })

        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[prompt_message],
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
    elif date:
        insert_message(conn, full_response, role="assistant")
        insert_summary(conn, latest_message_id + 1, date=date)
