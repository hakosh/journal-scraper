from db import conn


def exists(pub_id: str) -> bool:
    cursor = conn.execute("select count(*) from articles where id = $id", {"id": pub_id})
    res = cursor.fetchone()

    return res[0] > 0
