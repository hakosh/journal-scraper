with articles as (select id,
                         title,
                         title_en,
                         journal,
                         pub_year,
                         country
                  from main.articles
                  where country != 'jpn'),

     abstracts as (select a.id                                                     as article_id,
                          coalesce(abstract_es_clean.content, abstract_es.content) as abstract_es,
                          coalesce(abstract_en_clean.content, abstract_en.content) as abstract_en
                   from articles a
                            left join contents abstract_es
                                      on a.id = abstract_es.article_id and abstract_es.type = 'abstract' and
                                         abstract_es.lang = 'es'
                            left join contents abstract_en
                                      on a.id = abstract_en.article_id and abstract_en.type = 'abstract' and
                                         abstract_en.lang = 'en'
                            left join contents_clean abstract_es_clean
                                      on a.id = abstract_es_clean.article_id and abstract_es_clean.type = 'abstract' and
                                         abstract_es_clean.lang = 'es'
                            left join contents_clean abstract_en_clean
                                      on a.id = abstract_en_clean.article_id and abstract_en_clean.type = 'abstract' and
                                         abstract_en_clean.lang = 'en'),

     corpus as (select a.title,
                       a.title_en,
                       a.journal,
                       a.pub_year,
                       a.country,
                       abstracts.abstract_en,
                       abstracts.abstract_es,
                       body_en.content  as body_en,
                       body_en.lang_cnf as body_en_conf,
                       body_es.content  as body_es,
                       body_es.lang_cnf as body_es_conf
                from articles a
                         join abstracts on a.id = abstracts.article_id
                         left join contents_clean body_es
                                   on a.id = body_es.article_id and body_es.type = 'body' and body_es.lang = 'es'
                         left join contents_clean body_en
                                   on a.id = body_en.article_id and body_en.type = 'body' and body_en.lang = 'en'
                where ((body_es is null and body_en is null) or body_es_conf >= 0.8))

select *
from corpus
where (length(abstract_en) > 0)
   or (length(abstract_es) > 0);