import apsw

conn = apsw.Connection("articles.db")


def setup():
    conn.execute('''
        create table if not exists articles_raw (
            id           string primary key,
            title        text not null,
            journal      text not null,
            pub_year     integer not null,
            abstract_en  text,
            abstract_es  text,
            body_en      text,
            body_en_link text,
            body_es      text,
            body_es_link text
        ) without rowid;
    ''')

    conn.execute('''
        create table if not exists articles (
            id string primary key references articles_raw (id),
            title text,
            title_lang text,
            
            abstract_en text,
            abstract_en_lang text,
            abstract_en_conf float,
            
            abstract_es text,
            abstract_es_lang text,
            abstract_es_conf float,
            
            body_en text,
            body_en_lang text,
            body_en_conf float,
            
            body_es text,
            body_es_lang text,
            body_es_conf float
        ) without rowid;
    ''')
