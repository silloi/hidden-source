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
