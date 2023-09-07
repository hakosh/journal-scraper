from fasttext.FastText import _FastText

from models import CleanContent, get_uncleaned_contents, save_clean_content

model_path = 'lid.176.ftz'
model = _FastText(model_path=model_path)


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


def get_lang(text: str) -> (str, float):
    lang, conf = model.predict(text)
    lang = lang[0].removeprefix('__label__')
    conf = conf[0]

    return lang, conf
