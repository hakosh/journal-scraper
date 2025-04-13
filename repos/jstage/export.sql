with journals(id, name) as (values ('hozen', 'Japanese Journal of Conservation Ecology'),
                                   ('seitai', 'JAPANESE JOURNAL OF ECOLOGY'),
                                   ('hrghsj1999', 'Bulletin of the Herpetological Society of Japan'),
                                   ('mammalianscience', 'Mammalian Science'),
                                   ('jmammsocjapan1952', 'Journal of Mammalogical Society of Japan'),
                                   ('jjo', 'Japanese Journal of Ornithology'),
                                   ('strix', 'Strix'),
                                   ('ece', 'Ecology and Civil Engineering'),
                                   ('jale2004', 'Landscape Ecology and Management'),
                                   ('wildlifeconsjp', 'Wildlife Conservation Japan'),
                                   ('awhswhs', 'Wildlife and Human Society'),
                                   ('jila1925', 'The Journal of the Japanese Landscape Architectural Society'),
                                   ('jila1934', 'Journal of the Japanese Institute of Landscape Architects'),
                                   ('jila', 'Journal of the Japanese Institute of Landscape Architecture'),
                                   ('jilaonline', 'Landscape Research Japan Online'),
                                   ('jjfs1934', 'The Journal of the Japanese Forestry Society'),
                                   ('jjfs1953', 'Journal of the Japanese Forestry Society'),
                                   ('jjfs', 'Journal of the Japanese Forest Society')),

     english as (select a.id                                               as doi,
                        a.title_en,
                        a.pub_year,
                        a.journal,
                        trim(replace(c.content, 'View full abstract', '')) as abstract_en
                 from articles a
                          join contents c on a.id = c.article_id
                 where a.country = 'jpn'
                   and c.lang = 'en'),

     japanese as (select a.id            as doi,
                         a.title         as title_ja,
                         a.pub_year,
                         a.journal,
                         trim(c.content) as abstract_ja
                  from articles a
                           join contents c on a.id = c.article_id
                  where a.country = 'jpn'
                    and c.lang = 'ja')

select en.doi,
       en.pub_year,
       jn.name,
       en.title_en,
       ja.title_ja,
       en.abstract_en,
       ja.abstract_ja
from english en
         join japanese ja on en.doi = ja.doi
         join journals jn on jn.id = en.journal
where title_ja != ''
  and title_en != ''
  and title_en != '[title in Japanese]';