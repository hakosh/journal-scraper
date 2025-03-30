import asyncio
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from articles import exists
from crawler import Crawler
from models import Link, Article, Content, save_article, save_contents, reset_running, get_first_pending
from retry import retry

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

years = list(range(1998, 2025))

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
            link=None,
            format="text",
            content=abstract_item.get_text(strip=True),
        )

        abstracts.append(abstract)

    return article, abstracts


def process_index(body: str) -> list[Link]:
    soup = BeautifulSoup(body, 'html.parser')
    article_items = soup.select('div.item')

    links: list[Link] = []

    for item in article_items:
        article, abstracts = extract_from_item(item)

        if exists(article.id):
            print(f"{article.id} already downloaded")
            continue

        save_article(article)
        save_contents(abstracts, "abstract")

        for url in item.select('div.versions > span > a'):
            if "sci_arttext" in url['href']:
                links.append(
                    Link(url=url['href'], resource_type="article", repo="scielo")
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

    if "text/html" in content_type:
        soup = BeautifulSoup(body, "html.parser")
        content = Content(
            article_id=pid,
            lang=qs["tlng"][0],
            link=link.url,
            format="html",
            content=body.encode('utf-8', 'ignore').decode('utf-8')
        )

        print(f'saved html: {pid}')
        save_contents([content], "body")

        # if not (soup.find(id="article-body") or soup.find(id="s1-body")):
        #     print(f'return xml link: {link.url}')
        #     links.append(Link(
        #         url=get_xml_url(link),
        #         resource_type="article",
        #         repo="scielo"
        #     ))

    else:
        print(f'trying to save xml: {pid}')
        content = Content(
            article_id=pid,
            lang=qs["lang"][0],  # error suppressed
            link=link.url,
            format="xml",
            content=body
        )

        print(f'saved xml: {pid}')
        save_contents([content], "body")

    return links


@retry(count=3)
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

    return f'{url.scheme}://{url.hostname}/scielo.org/php/articleXML.php?pid={pid}&lang={lang}'


def get_page_url(page: int):
    params = base_params.copy()
    params["page"] = page
    params["count"] = page_size
    params["from"] = (page - 1) * page_size + 1

    journals_q = "&".join(map(lambda year: f'filter[year_cluster][]={year}', years))
    years_q = "&".join(map(lambda journal: f'filter[journal_title][]={urllib.parse.quote(journal)}', journals))

    return base_url + "/?" + urllib.parse.urlencode(params) + "&" + journals_q + "&" + years_q


def download_scielo():
    crawler = Crawler(repo="scielo", visit=visit, concurrency=6)

    reset_running("scielo")
    entry = get_first_pending("scielo")
    if entry is None:
        entry = Link(url=get_page_url(1), repo="scielo", resource_type="index")

    print("ENTRY", entry.url)

    asyncio.run(crawler.start([entry]), debug=False)
