# TODO: Add a button to pin a message
def toggle_pinned(conn, id, value):
    with conn.session as s:
        print(id, value)
        s.execute(
            "UPDATE messages SET pinned = :value WHERE id = :id;",
            params=dict(value=not value, id=id)
        )
        s.commit()

# TODO: Add a button to archive a message
def toggle_archived(conn, id, value):
    with conn.session as s:
        s.execute(
            "UPDATE messages SET archived = :value WHERE id = :id;",
            params=dict(value=not value, id=id)
        )
        s.commit()
