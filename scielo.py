import urllib.parse

import requests
from bs4 import BeautifulSoup

import articles
from articles import RawArticle

session = requests.Session()

base_url = "https://search.scielo.org"

journals = [
    "Revista de Biología Tropical",
    "Revista mexicana de biodiversidad",
    "Acta zoológica mexicana",
    "Revista chilena de historia natural",
    "Mastozoología neotropical",
    "Revista mexicana de ciencias forestales",
    "Madera y bosques",
    "Ecología austral",
    "Therya",
    "Ecología Aplicada",
    "Huitzil",
    "Quebracho (Santiago del Estero)"
]

years = list(range(1998, 2020))

base_params = {
    "q": "*",
    "format": "summary",
    "count": 50,
    "from": 1,
    "page": 1,
    "lang": "en",
    "output": "site",
    "sort": "YEAR_DESC",
}

page_size = 50


def fetch_list_page(page: int):
    params = base_params.copy()
    params["page"] = page
    params["count"] = page_size
    params["from"] = (page - 1) * page_size + 1

    journals_q = "&".join(map(lambda year: f'filter[year_cluster][]={year}', years))
    years_q = "&".join(map(lambda journal: f'filter[journal_title][]={urllib.parse.quote(journal)}', journals))
    url = base_url + "/?" + urllib.parse.urlencode(params) + "&" + journals_q + "&" + years_q

    return session.get(url)


def fetch_articles(page_from=1):
    page_num = page_from
    len_articles = 50

    while len_articles == 50:
        print(f'fetching page {page_num}')
        page = fetch_list_page(page_num)
        soup = BeautifulSoup(page.text, 'html.parser')
        article_items = soup.select('div.item')

        for article in article_items:
            len_articles += 1
            yield article

        len_articles = len(article_items)
        page_num += 1


def extract_abstract(article: BeautifulSoup):
    en, es = "", ""

    for abstract in article.select('div.abstract'):
        tail = abstract['id'][-3:]

        if tail == "_en":
            en = abstract.get_text(strip=True)
        elif tail == "_es":
            es = abstract.get_text(strip=True)

    return en, es


class FetchArticleException(BaseException):
    pass


MAX_RETRIES = 1


def fetch_article(link: str) -> str:
    num_tries = 1

    while True:
        if num_tries > 1:
            print(f'retry {num_tries}: {link}')

        try:
            resp = session.get(link, timeout=30)
            resp.encoding = "UTF-8"

            if resp.status_code >= 400:
                raise FetchArticleException

        except (requests.ConnectionError, requests.ReadTimeout):
            if num_tries <= MAX_RETRIES:
                num_tries += 1
                continue
            else:
                raise FetchArticleException

        return resp.text.encode('utf-8', 'ignore').decode('utf-8')


def extract_body(article: BeautifulSoup):
    body = {
        "en": {
            "text": "",
            "link": "",
        },
        "es": {
            "text": "",
            "link": ""
        }
    }

    for link in article.select('div.versions > span > a'):
        if "sci_arttext" in link['href']:
            lang = link['href'][-2:]

            body[lang] = {
                "text": fetch_article(link['href'].replace('http://', 'https://')),
                "link": link['href']
            }

    return body["en"]["text"], body["en"]["link"], body["es"]["text"], body["es"]["link"]


def sync(page_from=1):
    for article in fetch_articles(page_from):
        article_id = article['id']

        if articles.exists(article_id):
            print(f'skip {article_id}')
            continue

        title = article.find('strong', class_="title").get_text(strip=True)
        source = article.select('div.source span')
        year = int(source[2].get_text(strip=True)[0:4])
        journal = source[0].a.get_text(strip=True)

        try:
            abstract_en, abstract_es = extract_abstract(article)
            body_en, body_en_link, body_es, body_es_link = extract_body(article)
        except FetchArticleException:
            print(f'skipped {article_id}')
            continue

        pub = RawArticle(article_id, title, journal, year, abstract_en, abstract_es, body_en, body_en_link, body_es,
                         body_es_link)
        articles.save_raw(pub)
        print(f'saved {article_id}')
