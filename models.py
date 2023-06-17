import db


class Link:
    def __init__(self, url: str, resource_type: str, repo: str):
        self.url = url
        self.repo = repo
        self.type = resource_type


def save_link(link: Link):
    db.conn.execute('''
        INSERT INTO links (url, type, repo, status)
        VALUES (:url, :type, :repo, 'pending')
        ON CONFLICT DO NOTHING 
    ''', {
        "url": link.url,
        "type": link.type,
        "repo": link.repo,
    })


def get_links(repo: str, count: int) -> list[Link]:
    links = []

    if count == 0:
        return links

    cursor = db.conn.execute('''
        UPDATE links
        SET status = 'running'
        WHERE url IN (
            SELECT url
            FROM links
            WHERE repo = :repo AND status = 'pending'
            LIMIT :count
        )
        RETURNING url, type, repo
    ''', {"repo": repo, "count": count})

    for link in cursor:
        url, resource_type, repo = link
        links.append(Link(url=url, resource_type=resource_type, repo=repo))

    return links


def count_pending(repo: str) -> int:
    res = list(db.conn.execute('''
        SELECT COUNT(*)
        FROM links
        WHERE repo = :repo AND status = 'pending'
    ''', {"repo": repo}))

    return res[0][0]


def save_link_status(link: Link, status: str):
    db.conn.execute('''
        UPDATE links
        SET status = :status
        WHERE url = :url
    ''', {"url": link.url, "status": status})
