import apsw

conn = apsw.Connection("articles.db")
conn.execute('''
    PRAGMA foreign_keys = ON;
''')


def setup():
    conn.execute('''
        drop table contents_clean;
        drop table contents;
        drop table articles;
        drop table links;
    ''')

    conn.execute('''
        create table links (
            url text primary key,
            repo text not null,
            type text not null,
            status text not null
        );
    ''')

    conn.execute('''
        create table articles (
            id text primary key,
            title text not null,
            country text,
            journal text not null,
            pub_year integer not null
        );
    ''')

    conn.execute('''
        create table contents (
            article_id text not null references articles (id) on delete cascade,
            type text not null,
            lang text not null,
            content text not null,
            link text references links (url)
        );
    ''')

    conn.execute('''
        create table contents_clean (
            article_id text not null references articles (id) on delete cascade,
            type text not null,
            lang text not null,
            lang_conf float not null,
            content text not null
        );
    ''')
