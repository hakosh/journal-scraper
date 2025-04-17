from fasttext.FastText import _FastText

model_path = 'lid.176.ftz'
model = _FastText(model_path=model_path)


def get_lang(text: str) -> (str, float):
    lang, conf = model.predict(text)
    lang = lang[0].removeprefix('__label__')
    conf = conf[0]

    return lang, conf
