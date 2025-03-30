import asyncio
import itertools
import re
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

from crawler import Crawler
from models import Link, reset_running, Content, save_article, Article, save_contents
from retry import retry

base_url = "https://www.jstage.jst.go.jp"

journals = [
    "hozen",  # Japanese Journal of Conservation Ecology
    "seitai",  # JAPANESE JOURNAL OF ECOLOGY
    "hrghsj1999",  # Bulletin of the Herpetological Society of Japan
    "mammalianscience",  # Mammalian Science
    "jmammsocjapan1952",  # Journal of Mammalogical Society of Japan
    "jjo",  # Japanese Journal of Ornithology
    "strix",  # Strix
    "ece",  # Ecology and Civil Engineering
    "jale2004",  # Landscape Ecology and Management
    # "" # Bulletion of the International Association for Landscape Ecology-Japan
    "wildlifeconsjp",  # Wildlife Conservation Japan
    "awhswhs",  # Wildlife and Human Society
    "jila1925",  # The Journal of the Japanese Landscape Architectural Society
    "jila1934",  # Journal of the Japanese Institute of Landscape Architects
    "jila",  # Journal of the Japanese Institute of Landscape Architecture
    "jilaonline",  # Landscape Research Japan Online
    "jjfs1934",  # The Journal of the Japanese Forestry Society
    "jjfs1953",  # Journal of the Japanese Forestry Society
    "jjfs"  # Journal of the Japanese Forest Society
]


def get_link(journal: str, lang: str) -> Link:
    url = f"{base_url}/browse/{journal}/list/-char/{lang}"

    return Link(url=url, repo="jstage", resource_type="index")


not_content = re.compile("_(Toc|App|Cover)\d$")


def is_article(doi: str) -> bool:
    return not_content.search(doi) is None


journal_pattern = re.compile("/browse/(\w*)/")
lang_pattern = re.compile("char/(\w{2})$")
pub_year_pattern = re.compile("(\d{4})")


def extract_articles(soup: BeautifulSoup, link: Link) -> (list[Article], list[Content]):
    print(f"extracting articles from {link.url}")
    matches = journal_pattern.search(link.url)
    journal_name = matches.group(1)

    matches = lang_pattern.search(link.url)
    lang = matches.group(1)

    containers = soup.find_all("ul", {"class": "search-resultslisting"})

    articles = []
    contents = []

    for container in containers:
        for item in container.find_all("li"):
            doi = item.find("div", {"class": "searchlist-doi"}).find("a")["href"]
            if not is_article(doi):
                continue

            doi = urlparse(doi)
            article_id = f"{doi.netloc}{doi.path}"

            pub_year_text = item.find("div", {"class": "searchlist-additional-info"}).text
            pub_year = int(pub_year_pattern.search(pub_year_text).group(1))

            article = Article(
                article_id=article_id,
                title="",
                country="jpn",
                journal=journal_name,
                pub_year=pub_year,
                title_en=None
            )

            title = item.find("div", {"class": "searchlist-title"}).get_text().strip()

            if lang == "ja":
                article.title = title
            else:
                article.title_en = title

            articles.append(article)

            # CONTENT
            abstract_item = item.find("div", {"class": "abstract"})
            if abstract_item is None:
                continue

            abstract = abstract_item.get_text().strip()

            contents.append(Content(
                article_id=article_id,
                lang=lang,
                content=abstract,
                format="text",
                link=None
            ))

    return articles, contents


def extract_links(soup: BeautifulSoup) -> list[Link]:
    urls = []

    groups = soup.find_all("ul", attrs={"class": "facetsearch-links"})
    for group in groups:
        for link in group.find_all("a"):
            urls.append(link["href"])

    return [Link(url=url, repo="jstage", resource_type="list") for url in urls]


def process_list(body: str, link: Link) -> list[Link]:
    soup = BeautifulSoup(body, "html.parser")

    articles, contents = extract_articles(soup, link)

    for article in articles:
        save_article(article)

    # for content in contents:
    #     print("SAVE", link.url, content.article_id, content.lang)

    save_contents(contents, "abstract")

    return []


def process_index(body: str) -> list[Link]:
    soup = BeautifulSoup(body, "html.parser")
    return extract_links(soup)


@retry(count=3)
async def visit(session: aiohttp.ClientSession, link: Link) -> list[Link]:
    resp = await session.get(link.url)
    body = await resp.text()

    if link.type == "index":
        return process_index(body)
    elif link.type == "list":
        return process_list(body, link)

    raise ValueError(f"{link.type} is not supported")


def download_jstage():
    crawler = Crawler(repo="jstage", concurrency=6, visit=visit)

    reset_running("jstage")
    entries = [get_link(journal, lang) for (journal, lang) in itertools.product(journals, ["en", "ja"])]

    asyncio.run(crawler.start(entries), debug=False)
