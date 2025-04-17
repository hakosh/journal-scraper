import re

from lang import get_lang
from models import get_uncleaned_contents, save_clean_content, CleanContent

abstract_pattern = r"(?i)^(Abstract|Resumen)\W?"


def transform_abstracts():
    contents = get_uncleaned_contents("abstract", "text", "Galemys")

    for content in contents:
        abstract = content.content

        # Remove DOI
        pos_doi = abstract.find("DOI:")
        if pos_doi != -1:
            abstract = abstract[:pos_doi]

        pos_palabras = abstract.find("Palabras clave")
        if pos_palabras != -1:
            abstract = abstract[:pos_palabras]

        pos_keywords = abstract.find("Keywords")
        if pos_keywords != -1:
            abstract = abstract[:pos_keywords]

        abstract = re.sub(abstract_pattern, "", abstract)
        abstract = re.sub(r"\r\n|\n|\r", ' ', abstract)
        abstract = re.sub(r" {2,}", " ", abstract)
        abstract = abstract.strip()

        lang_det, lang_cnf = get_lang(abstract)

        save_clean_content(CleanContent(
            article_id=content.article_id,
            lang=content.lang,
            lang_det=lang_det,
            lang_cnf=lang_cnf,
            content=abstract,
            type="abstract"
        ))


def transform_galemys():
    transform_abstracts()
