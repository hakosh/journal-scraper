import asyncio
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

from articles import exists
from crawler import Crawler
from models import reset_running, Link, save_article, Article, save_contents, Content
from retry import retry


def process_index(body: str, link: Link) -> list[Link]:
    soup = BeautifulSoup(body, "html.parser")

    # div.view-galemys-issues span.views-field-title a
    issues = soup.find("div", {"class": "view-galemys-issues"})
    titles = issues.find_all("span", {"class": "views-field-title"})

    base_url = urlparse(link.url)
    url = f"{base_url.scheme}://{base_url.netloc}"

    links = []
    for title in titles:
        links.append(Link(
            url=url + title.find("a")["href"],
            repo="galemys",
            type="journal"
        ))

    return links


def process_article(body: str, link: Link) -> list[Link]:
    # div.container
    soup = BeautifulSoup(body, "html.parser").find("div", {"id": "section-content"})

    doi = soup.find("div", {"class": "field--name-field-doi"})
    doi = doi.find("a")["href"]
    doi_url = urlparse(doi)
    article_id = f"{doi_url.netloc}{doi_url.path}"

    if exists(article_id):
        return []

    title = soup.find("div", {"class": "field--name-field-title"}).get_text()
    titles = title.split("/")

    if len(titles) > 1:
        title_en, title_es = titles
    else:
        title_en, title_es = None, titles[0]

    pub_year = soup.find("div", {"class": "field--name-field-copyrightyear"}).get_text()

    article = Article(
        id=article_id,
        title=title_es,
        title_en=title_en,
        journal="Galemys",
        pub_year=int(pub_year),
        country="esp"
    )

    contents = []
    abstract = soup.find("div", {"class": "field--name-field-abstract"})
    if not abstract:
        return []

    abstract = abstract.find("div", {"class": "field--item"})
    if not abstract:
        return []

    # Split abstracts
    abstract = abstract.get_text()

    pos_en = abstract.find("Abstract")
    pos_es = abstract.find("Resumen")

    if abstract.count("Resumen") >= 2:
        pos_en = abstract.find("Resumen", pos_es + 7)

    if pos_en != -1:
        end = pos_es if pos_es > pos_en else len(abstract)
        contents.append(Content(
            article_id=article_id,
            lang="en",
            link=None,
            format="text",
            content=abstract[pos_en:end]
        ))

    if pos_es != -1:
        end = pos_en if pos_en > pos_es else len(abstract)
        contents.append(Content(
            article_id=article_id,
            lang="es",
            link=None,
            format="text",
            content=abstract[pos_es:end]
        ))

    if len(contents) > 0:
        save_article(article)
        save_contents(contents, "abstract")

    return []


def process_journal(body: str, link: Link) -> list[Link]:
    soup = BeautifulSoup(body, "html.parser")

    # div.view-galemys-articles div.views-field-field-title a
    articles = soup.find("div", {"class": "view-galemys-articles"})
    titles = articles.find_all("div", {"class": "views-field-field-title"})

    links = []

    for title in titles:
        links.append(Link(
            url=title.find("a")["href"],
            repo="galemys",
            type="article"
        ))

    # PAGINATION
    pagination = soup.find("div", {"class": "pagination"})
    if not pagination:
        return links

    pages = pagination.find_all("a")

    hrefs = set()
    for page in pages:
        if page.has_attr("aria-current"):
            continue

        href = page["href"]
        if href == "?page=0":
            continue

        hrefs.add(href)

    for href in hrefs:
        links.append(Link(
            url=link.url + href,
            repo="galemys",
            type="journal"
        ))

    return links


@retry(count=3)
async def visit(session: aiohttp.ClientSession, link: Link) -> list[Link]:
    resp = await session.get(link.url)
    body = await resp.text()

    if link.type == "index":
        return process_index(body, link)
    if link.type == "journal":
        return process_journal(body, link)
    elif link.type == "article":
        return process_article(body, link)
    else:
        raise ValueError("unknown type:" + link.type)


def download_galemys():
    crawler = Crawler(repo="galemys", concurrency=4, visit=visit)

    reset_running("galemys")
    entries = [
        Link(url="https://secem.es/galemys", repo="galemys", type="index")
    ]

    asyncio.run(crawler.start(entries), debug=False)
