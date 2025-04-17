import asyncio
import hashlib
import re

import aiohttp
from bs4 import BeautifulSoup

from crawler import Crawler
from lang import get_lang
from models import reset_running, Link, Article, Content, save_article, save_contents
from retry import retry

year_by_issue = {}


def process_issue(body: str, link: Link) -> list[Link]:
    soup = BeautifulSoup(body, 'html.parser')
    main = soup.find('article')

    for row in main.find_all('div', {"class": "et_pb_row"}):
        title = row.find("h3")
        if not title:
            continue

        title = title.get_text().strip()
        title_en = ""

        article_id = "barbastella-" + hashlib.md5(title.encode('utf-8')).hexdigest()[:12]

        lang, _ = get_lang(title)
        if lang == "en":
            title, title_en = title_en, title

        article = Article(
            id=article_id,
            title=title,
            title_en=title_en,
            pub_year=year_by_issue[link.url],
            journal="Journal of Bat Research & Conservation",
            country="esp",
        )

        contents = []

        for p in row.find_all('p'):
            text = p.get_text().strip()
            if text.startswith('Resumen:'):
                contents.append(Content(
                    article_id=article_id,
                    content=text,
                    link=None,
                    lang="es",
                    format="text"
                ))
            elif text.startswith('Abstract:'):
                contents.append(Content(
                    article_id=article_id,
                    content=text,
                    link=None,
                    lang="en",
                    format="text"
                ))

        if contents:
            save_article(article)
            save_contents(contents, content_type="abstract")

    return []


def process_index(body: str) -> list[Link]:
    soup = BeautifulSoup(body, "html.parser")
    main = soup.find("article")

    links = []
    for link in main.find_all("a"):
        url = link["href"]
        if re.search("\d{1,2}/$", url):
            title = link.parent.parent.find("h4")
            year = re.search("\d{4}", title.text)
            if not year:
                continue

            year_by_issue[url] = int(year[0])
            links.append(Link(url=url, repo="barbastella", type="issue"))

    return links


@retry(count=3)
async def visit(session: aiohttp.ClientSession, link: Link) -> list[Link]:
    resp = await session.get(link.url)
    body = await resp.text()

    if link.type == "index":
        return process_index(body)
    elif link.type == "issue":
        return process_issue(body, link)
    else:
        raise ValueError("unknown type: " + link.type)


def download_barbastella():
    crawler = Crawler(repo="barbastella", concurrency=4, visit=visit)

    reset_running("galemys")
    entries = [
        Link(url="https://secemu.org/en/journal/all-issues/", repo="barbastella", type="index"),
    ]

    asyncio.run(crawler.start(entries), debug=False)
