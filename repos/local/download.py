import csv

from models import Article, Content, save_article, save_contents


def download_local():
    # read csv
    positives = open("./manual_articles/positives.csv")
    rows = csv.reader(positives)

    header = next(rows)
    raw_articles = []

    for row in rows:
        article = {}

        for i, col in enumerate(header):
            article[col] = row[i]

        raw_articles.append(article)

    # for each article
    for raw in raw_articles:
        id = raw["id"]

        article = Article(
            id=id,
            title=raw["title"],
            title_en=None,
            country=raw["country"],
            journal=raw["journal"],
            pub_year=int(raw["pub_year"])
        )

        abstract_en = Content(
            article_id=id,
            lang="en",
            link=None,
            format="text",
            content=raw["abstract_en"]
        )

        abstract_es = Content(
            article_id=id,
            lang="es",
            link=None,
            format="text",
            content=raw["abstract_es"]
        )

        body = open("./manual_articles/" + id + ".txt").read()
        body_es = Content(
            article_id=id,
            lang="es",
            link=None,
            format="text",
            content=body
        )

        save_article(article)
        save_contents([abstract_en, abstract_es], "abstract")
        save_contents([body_es], "body")

    # read content
    # call save content
