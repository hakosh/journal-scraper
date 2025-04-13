import html
import re
from html import unescape

from bs4 import BeautifulSoup, Tag
from fasttext.FastText import _FastText
from htmlmin import minify

from models import get_uncleaned_contents, save_clean_content, CleanContent, Content

model_path = 'lid.176.ftz'
model = _FastText(model_path=model_path)


def get_lang(text: str) -> (str, float):
    lang, conf = model.predict(text)
    lang = lang[0].removeprefix('__label__')
    conf = conf[0]

    return lang, conf


def clean_xml(content: Content) -> CleanContent:
    print("CONTENT", content.article_id, content.lang)
    soup = BeautifulSoup(content.content, features="xml")
    bodies = soup.find("article").find_all("body")
    print("COUNT", len(bodies))
    strings = []

    for body_raw in bodies:
        body = unescape(body_raw.get_text())
        # print("PARSING", body)

        body_soup = BeautifulSoup(body, 'html.parser')
        for string in body_soup.stripped_strings:
            strings.append(string)

    # print("extracted body")
    # for string in strings:
    #     print(string)

    clean_body = " ".join(strings)
    print("CLEAN", clean_body)
    lang_det, lang_cnf = get_lang(clean_body)

    return CleanContent(
        article_id=content.article_id,
        lang=content.lang,
        lang_det=lang_det,
        lang_cnf=lang_cnf,
        content=" ".join(strings),
        type="body"
    )


def transform_xml_bodies():
    contents = get_uncleaned_contents("body", "xml")

    for content in contents:
        cleaned = clean_xml(content)
        save_clean_content(cleaned)

    print(f'cleaned {len(contents)} resources')


def remove_citations_tags(doc: Tag):
    links = doc.find_all("a")
    for link in links:
        if link.parent is not None and link.parent.name == "sup":
            link.parent.clear()


def remove_citations_text(string: str) -> str:
    string = re.sub("\([^()]*et\sal\.[^()]*\)", "", string)
    string = re.sub("\([^()]*\d{4}\)", "", string)
    return string


def remove_brackets(body: str) -> str:
    return re.sub("\([;,\s]*\)", "", body)


def construct_paragraphs(doc: BeautifulSoup) -> list[str]:
    strings = []

    for string in doc.stripped_strings:
        strings.append(string)

    return strings


def clean_structured_html(body: BeautifulSoup) -> str:
    # remove header
    head = body.find("p", attrs={"class": "sec"})
    if head is not None:
        head.clear()

    remove_citations_tags(body)
    strings = construct_paragraphs(body)

    return remove_brackets(" ".join(strings))


def clean_messy_html(body: BeautifulSoup) -> str:
    oBody = body
    body = body.find("div", attrs={"class": re.compile("^index,\w{2}")})

    if body is None:
        print("BODY", str(oBody))
        exit(1)

    hrs = body.find_all("hr")
    if len(hrs) >= 2:
        for tag in hrs[1].previous_siblings:
            if isinstance(tag, Tag):
                tag.clear()

    ps = body.find_all("p")
    if len(ps) == 0:
        ps = body.find_all("font", attrs={"size": ["2", "3"]})

    paragraphs = []
    for p in ps:
        if not p.text:
            continue

        head = p.text[0:50].strip().lower()

        if head in ["abstract:", "key words:", "resumen:"]:
            continue
        elif head in ["agradecimientos", "acknowledgments", "references", "referencias"]:
            break
        else:
            remove_citations_tags(p)

            text = str(p).replace("\n", " ").strip()
            text = re.sub("\s+", " ", text)
            text = re.sub("<.*?>", "", text).strip()
            text = html.unescape(text)
            text = remove_citations_text(text)

            paragraphs.append(text)

    bad = ["abstract", "resumen", "key words"]
    for word in bad:
        idx = paragraphs.index(word) if word in paragraphs else None
        if idx is not None:
            paragraphs = paragraphs[:idx] + paragraphs[idx + 2:]

    return remove_brackets(" ".join(paragraphs))


def clean_html(content: Content) -> CleanContent | None:
    mini = minify(content.content, remove_comments=True, remove_all_empty_space=True)
    mini = mini.encode("utf-8", "ignore").decode("utf-8")
    soup = BeautifulSoup(mini, 'lxml')

    print(f'processing: {content.article_id} - {content.lang}')

    if raw := soup.find(id="article-body"):
        print("found article-body")
        body = clean_structured_html(raw)
    elif raw := soup.find(id="s1-body"):
        print("found s1-body")
        body = clean_structured_html(raw)
    elif soup.find("div", {"class": re.compile("index,\w{2}")}):
        print("found messy html")
        body = clean_messy_html(soup)
    else:
        print(f"cannot process content: {content.article_id} ({content.lang})")
        return None

    body = body.replace("\n", " ").strip()
    if body == "":
        print(f"cannot process content (empty): {content.article_id} ({content.lang})")
        return None

    lang_det, lang_cnf = get_lang(body)
    print(content.article_id, lang_det, lang_cnf)

    return CleanContent(
        article_id=content.article_id,
        lang=content.lang,
        lang_det=lang_det,
        lang_cnf=lang_cnf,
        content=body,
        type="body"
    )


def transform_html_bodies():
    contents = get_uncleaned_contents("body", "html")

    for content in contents:
        cleaned = clean_html(content)

        if cleaned is not None:
            save_clean_content(cleaned)

    print(f'cleaned {len(contents)} resources')


def transform_scielo():
    # transform_xml_bodies()
    transform_html_bodies()
    # transform_abstracts()
