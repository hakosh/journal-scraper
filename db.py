import apsw

conn = apsw.Connection("articles.db")


def setup():
    conn.execute('''
        create table if not exists links (
            url text primary key,
            repo text not null,
            type text not null,
            status text not null
        );
    ''')

    conn.execute('''
        create table if not exists articles (
            id text primary key,
            journal text not null,
            pub_year integer not null
        );
    ''')

    conn.execute('''
        create table if not exists contents (
            article_id text not null references articles (id) on delete cascade,
            type text not null,
            link text not null references links (url),
            lang text not null,
            lang_conf float not null,
            content text not null
        );
    ''')
