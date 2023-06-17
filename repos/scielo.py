import asyncio
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from crawler import Crawler
from models import Link

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


def process_index(body: str) -> list[Link]:
    soup = BeautifulSoup(body, 'html.parser')
    article_items = soup.select('div.item')

    links: list[Link] = []

    for article in article_items:
        for url in article.select('div.versions > span > a'):
            if "sci_arttext" in url['href']:
                links.append(
                    Link(url=url['href'].replace('http://', 'https://'), resource_type="article", repo="scielo")
                )

    if len(article_items) == 50:
        page_num = int(soup.select_one("input[name='page']").attrs["value"])
        next_page = Link(url=get_page_url(page_num + 1), repo="scielo", resource_type="index")
        links.append(next_page)

    return links


def process_article(content_type: str, body: str) -> list[Link]:
    print("visited article")
    # test body for ids
    # return xml if not found
    return []


async def visit(session: aiohttp.ClientSession, link: Link) -> list[Link]:
    resp = await session.get(link.url)
    body = await resp.text("utf-8")

    if link.type == "index":
        return process_index(body)
    elif link.type == "article":
        return process_article(resp.headers['content-type'], body)


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
    entry = Link(url=get_page_url(1), repo="scielo", resource_type="index")

    asyncio.run(crawler.start(entry), debug=True)
