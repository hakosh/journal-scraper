import re

from bs4 import BeautifulSoup
from fasttext.FastText import _FastText

import articles
import db
from articles import Article

model_path = 'lid.176.ftz'
model = _FastText(model_path=model_path)

abstract_pattern = re.compile('^(abstract|resumen)', re.IGNORECASE)


def get_lang(text: str) -> (str, float):
    lang, conf = model.predict(text)
    lang = lang[0].removeprefix('__label__')
    conf = conf[0]

    return lang, conf


def process_abstract(raw: str):
    if not raw:
        return {
            "text": None,
            "lang": None,
            "conf": None,
        }

    clean = abstract_pattern.sub('', raw).strip()
    lang, conf = get_lang(clean)

    return {
        "text": clean,
        "lang": lang,
        "conf": conf
    }


def process_body(raw: str, target_lang: str):
    if not raw:
        return {
            "text": None,
            "lang": None,
            "conf": None
        }

    raw = raw.replace('\udbc0', "").replace("\udd34", "").replace("\n", " ")
    doc = BeautifulSoup(raw, 'html.parser')

    if doc.find(id='article-body'):
        body_text = " ".join(doc.find(id='article-body').stripped_strings)
    elif doc.find(id='s1-body'):
        body_text = " ".join(doc.find(id='s1-body').stripped_strings)
    else:
        blocks = []
        for strings in [x.stripped_strings for x in doc.find_all('p')]:
            block = " ".join(strings)
            lang, conf = get_lang(block)

            if lang == target_lang:
                blocks.append(block)

        body_text = " ".join(blocks)

    if not body_text:
        return {
            "text": None,
            "lang": None,
            "conf": None
        }

    txt = body_text.replace("\n", " ")
    lang, conf = get_lang(txt)

    return {
        "text": txt,
        "lang": lang,
        "conf": conf
    }


def process_title(title: str):
    if not title:
        return {
            "text": None,
            "lang": None
        }

    title = title.strip()
    lang, _ = get_lang(title)

    return {
        "text": title,
        "lang": lang
    }


def run():
    # fetch record
    articles_raw = db.conn.execute('''
        select ar.id, ar.title, ar.abstract_en, ar.abstract_es, ar.body_en, ar.body_es
        from articles_raw ar
            left join articles a on a.id = ar.id
        where a.id is null
            
    ''')

    for idx, row in enumerate(articles_raw):
        article = Article(id=row[0])

        article.title = process_title(row[1])

        article.abstract["en"] = process_abstract(row[2])
        article.abstract["es"] = process_abstract(row[3])

        article.body["en"] = process_body(row[4], "en")
        article.body["es"] = process_body(row[5], "es")

        articles.save(article)
