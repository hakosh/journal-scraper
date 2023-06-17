from db import conn


class Article:
    def __init__(self, id: str):
        self.id = id
        self.title = {}
        self.abstract = {}
        self.body = {}


class RawArticle:
    def __init__(
            self,
            pub_id: str,
            title: str,
            journal: str,
            pub_year: int,
            abstract_en: str,
            abstract_es: str,
            body_en: str,
            body_en_link: str,
            body_es: str,
            body_es_link: str
    ):
        self.id = pub_id
        self.title = title
        self.journal = journal
        self.pub_year = pub_year
        self.abstract_en = abstract_en
        self.abstract_es = abstract_es
        self.body_en = body_en
        self.body_en_link = body_en_link
        self.body_es = body_es
        self.body_es_link = body_es_link


def exists(pub_id: str) -> bool:
    cursor = conn.execute("select count(*) from articles_raw where id = $id", {"id": pub_id})
    res = cursor.fetchone()

    return res[0] > 0


def save_raw(pub: RawArticle):
    conn.execute('''
        insert into articles_raw (id, title, journal, pub_year, abstract_en, abstract_es, body_en, body_en_link, body_es, body_es_link)
        values (:id, :title, :journal, :pub_year, :abstract_en, :abstract_es, :body_en, :body_en_link, :body_es, :body_es_link)
    ''', pub.__dict__)


def save(article: Article):
    conn.execute('''
        insert into articles (
            id,
            title,
            title_lang,
            abstract_en,
            abstract_en_lang,
            abstract_en_conf,
            body_en,
            body_en_lang,
            body_en_conf,
            abstract_es,
            abstract_es_lang,
            abstract_es_conf,
            body_es,
            body_es_lang,
            body_es_conf
        ) values (
            :id,
            :title,
            :title_lang,
            :abstract_en,
            :abstract_en_lang,
            :abstract_en_conf,
            :body_en,
            :body_en_lang,
            :body_en_conf,
            :abstract_es,
            :abstract_es_lang,
            :abstract_es_conf,
            :body_es,
            :body_es_lang,
            :body_es_conf
        )
        on conflict (id) do nothing;
    ''', {
        "id": article.id,
        "title": article.title.get("text"),
        "title_lang": article.title.get("lang"),

        "abstract_en": article.abstract["en"]["text"],
        "abstract_en_lang": article.abstract["en"]["lang"],
        "abstract_en_conf": article.abstract["en"]["conf"],

        "body_en": article.body["en"]["text"],
        "body_en_lang": article.body["en"]["lang"],
        "body_en_conf": article.body["en"]["conf"],

        "abstract_es": article.abstract["es"]["text"],
        "abstract_es_lang": article.abstract["es"]["lang"],
        "abstract_es_conf": article.abstract["es"]["conf"],

        "body_es": article.body["es"]["text"],
        "body_es_lang": article.body["es"]["lang"],
        "body_es_conf": article.body["es"]["conf"],
    })
