from lang import get_lang
from models import CleanContent, get_uncleaned_contents, save_clean_content


def transform_local():
    contents = get_uncleaned_contents("body", "text")
    for content in contents:
        body = content.content.replace("\n", " ")
        lang, conf = get_lang(body)

        save_clean_content(CleanContent(
            article_id=content.article_id,
            content_type="text",
            lang="es",
            lang_det=lang,
            lang_cnf=conf,
            content=body
        ))
