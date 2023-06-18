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
            ORDER BY ROWID
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


def reset_running():
    db.conn.execute('''
        UPDATE links
        SET status = 'pending'
        WHERE status = 'running'
    ''')


def get_first_pending():
    rows = db.conn.execute('''
        SELECT url, repo, type, status
        FROM links
        WHERE status = 'pending'
        LIMIT 1
    ''')

    url, repo, resource_type, status = list(rows)[0]
    return Link(url=url, repo=repo, resource_type=resource_type)


class Article:
    def __init__(self, article_id: str, title: str, country: str, journal: str, pub_year: int):
        self.id = article_id
        self.title = title
        self.country = country
        self.journal = journal
        self.pub_year = pub_year


count = 0


def save_article(article: Article):
    global count

    db.conn.execute('''
        INSERT INTO articles (id, journal, title, country, pub_year)
        VALUES (:id, :journal, :title, :country, :pub_year)
    ''', {
        "id": article.id,
        "title": article.title,
        "country": article.country,
        "journal": article.journal,
        "pub_year": article.pub_year
    })

    count += 1
    print(f'saved article #{count}')


class Content:
    def __init__(self, article_id: str, lang: str, link: str | None, content: str, format: str):
        self.article_id = article_id
        self.lang = lang
        self.link = link
        self.format = format
        self.content = content


def save_contents(contents: list[Content], content_type: str):
    for abstract in contents:
        db.conn.execute('''
            INSERT INTO contents (article_id, type, lang, link, content, format)
            VALUES (:article_id, :type, :lang, :link, :content, :format)
        ''', {
            "article_id": abstract.article_id,
            "lang": abstract.lang,
            "type": content_type,
            "content": abstract.content,
            "link": abstract.link,
            "format": abstract.format
        })
