def initialize_and_create_connection(st):
    # Create the SQL connection to messages_db as specified in your secrets file.
    conn = st.connection("messages_db", type="sql", ttl=None)

    create_message_table(conn)
    create_project_table(conn)
    create_note_table(conn)

    # Flush the cache to ensure that the data is up to date
    st.cache_data.clear()

    return conn

def create_message_table(conn):
    with conn.session as s:
        s.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            role TEXT,
            project_id INTEGER,
            pinned BOOLEAN DEFAULT FALSE,
            archived BOOLEAN DEFAULT FALSE,
            timestamp DATETIME
        )""")
        s.commit()

def create_project_table(conn):
    with conn.session as s:
        s.execute("""CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            timestamp DATETIME
        )""")
        s.commit()

def create_note_table(conn):
    with conn.session as s:
        s.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            date DATE,
            project_id INTEGER,
            timestamp DATETIME
        )""")
        s.commit()
