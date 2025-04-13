with english as (select a.id,
                        a.title,
                        a.journal,
                        a.pub_year,
                        a.country,
                        abs.content as abstract,
                        cc.lang_cnf as conf,
                        cc.content  as body
                 from articles a
                          left join contents abs on a.id = abs.article_id and abs.type = 'abstract' and abs.lang = 'en'
                          left join contents_clean cc
                                    on a.id = cc.article_id and cc.lang = 'en' and cc.lang_det = 'en'),

     spanish as (select a.id,
                        a.title,
                        a.journal,
                        a.pub_year,
                        a.country,
                        abs.content as abstract,
                        cc.content  as body,
                        cc.lang_cnf as conf
                 from articles a
                          left join contents abs on a.id = abs.article_id and abs.type = 'abstract' and abs.lang = 'es'
                          left join contents_clean cc on a.id = cc.article_id and cc.lang = 'es' and cc.lang_det = 'es')

select eng.id,
       eng.title,
       eng.journal,
       eng.pub_year,
       eng.country,
       eng.abstract as abstract_en,
       eng.body     as body_en,
       eng.conf     as body_en_conf,
       esp.abstract as abstract_es,
       esp.body     as body_es,
       esp.conf     as body_es_conf
from english eng
         join spanish esp on esp.id = eng.id
where esp.body is not null
  and esp.conf >= 0.85
order by esp.pub_year desc;