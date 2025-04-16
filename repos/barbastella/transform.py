from models import get_uncleaned_contents, save_clean_content, CleanContent
from repos.barbastella.download import get_lang


def transform_abstracts():
    contents = get_uncleaned_contents("abstract", "text", "Journal of Bat Research & Conservation")

    for content in contents:
        abstract = content.content

        # Remove abstract
        abstract = (
            abstract.replace("Abstract:", "")
            .replace("Resumen:", "")
            .strip()
        )

        lang, cnf = get_lang(abstract)

        save_clean_content(CleanContent(
            article_id=content.article_id,
            type="abstract",
            lang=content.lang,
            lang_det=lang,
            lang_cnf=cnf,
            content=abstract,
        ))


def transform_barbastella():
    transform_abstracts()
