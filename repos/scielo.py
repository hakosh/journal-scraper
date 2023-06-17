import asyncio
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from crawler import Crawler
from models import Link, Article, Content, save_article, save_contents

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


def extract_from_item(item) -> (Article, list[Content]):
    article_id = item['id'][:-4]
    country = item['id'].split("-")[-1]

    title = item.find('strong', class_="title").get_text(strip=True)
    source = item.select('div.source span')
    year = int(source[2].get_text(strip=True)[0:4])
    journal = source[0].a.get_text(strip=True)

    article = Article(
        article_id=article_id,
        title=title,
        country=country,
        journal=journal,
        pub_year=year
    )

    abstracts: list[Content] = []

    for abstract_item in item.select('div.abstract'):
        lang = abstract_item['id'][-2:]
        abstract = Content(
            article_id=article_id,
            lang=lang,
            content=abstract_item.get_text(strip=True),
            link=None
        )

        abstracts.append(abstract)

    return article, abstracts


def process_index(body: str) -> list[Link]:
    soup = BeautifulSoup(body, 'html.parser')
    article_items = soup.select('div.item')

    links: list[Link] = []

    for item in article_items:
        article, abstracts = extract_from_item(item)
        save_article(article)
        save_contents(abstracts, "abstract")

        for url in item.select('div.versions > span > a'):
            if "sci_arttext" in url['href']:
                links.append(
                    Link(url=url['href'].replace('http://', 'https://'), resource_type="article", repo="scielo")
                )

    if len(article_items) == 50:
        page_num = int(soup.select_one("input[name='page']").attrs["value"])
        next_page = Link(url=get_page_url(page_num + 1), repo="scielo", resource_type="index")
        links.append(next_page)

    return links


def process_article(link: Link, content_type: str, body: str) -> list[Link]:
    links: list[Link] = []
    url = urllib.parse.urlparse(link.url)
    qs = urllib.parse.parse_qs(url.query)
    pid = qs["pid"][0]

    if content_type == "text/html":
        soup = BeautifulSoup(body, "html.parser")

        if not (soup.find(id="article-body") or soup.find(id="s1-body")):
            print(f'return xml link: {link.url}')
            links.append(Link(
                url=get_xml_url(link),
                resource_type="article",
                repo="scielo"
            ))
        else:
            content = Content(
                article_id=pid,
                lang=qs["tlng"][0],
                link=link.url,
                content=body.encode('utf-8', 'ignore').decode('utf-8')
            )

            print(f'saved html: {pid}')
            save_contents([content], "body")

    else:
        print(f'trying to save xml: {pid}')
        content = Content(
            article_id=pid,
            lang=qs["lang"][0],
            link=link.url,
            content=body.encode("utf-8", "ignore").decode("utf-8")
        )

        print(f'saved xml: {pid}')
        save_contents([content], "body")

    return links


async def visit(session: aiohttp.ClientSession, link: Link) -> list[Link]:
    resp = await session.get(link.url)
    body = await resp.text()

    if link.type == "index":
        return process_index(body)
    elif link.type == "article":
        return process_article(link, resp.headers['content-type'], body)


def get_xml_url(link: Link):
    url = urllib.parse.urlparse(link.url)
    qs = urllib.parse.parse_qs(link.url)

    pid = qs["pid"][0]
    lang = qs["tlng"][0]

    return f'{url.scheme}://{url.hostname}/scieloOrg/php/articleXML.php?pid={pid}&lang={lang}'


def get_page_url(page: int):
    params = base_params.copy()
    params["page"] = page
    params["count"] = page_size
    params["from"] = (page - 1) * page_size + 1

    journals_q = "&".join(map(lambda year: f'filter[year_cluster][]={year}', years))
    years_q = "&".join(map(lambda journal: f'filter[journal_title][]={urllib.parse.quote(journal)}', journals))

    return base_url + "/?" + urllib.parse.urlencode(params) + "&" + journals_q + "&" + years_q


def run():
    crawler = Crawler(repo="scielo", visit=visit, concurrency=5)
    entry = Link(url=get_page_url(65), repo="scielo", resource_type="index")

    asyncio.run(crawler.start(entry), debug=True)
