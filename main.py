import sys

import db
from repos.galemys.download import download_galemys
from repos.galemys.transform import transform_galemys
from repos.jstage.download import download_jstage
from repos.jstage.transform import transform_jstage
from repos.local.download import download_local
from repos.local.transform import transform_local
from repos.scielo.download import download_scielo
from repos.scielo.transform import transform_scielo

if len(sys.argv) <= 1:
    print("arguments required")
    sys.exit(1)

mode = sys.argv[1]

match mode:
    case "sync-galemys":
        print("sync-galemys")
        download_galemys()

    case "transform-galemys":
        print("transform-galemys")
        transform_galemys()

    case "sync-jstage":
        print("sync-jstage")
        download_jstage()

    case "sync-scielo":
        print("sync scielo")
        download_scielo()

    case "sync-local":
        print("sync local")
        download_local()

    case "transform-jstage":
        print("transform-jstage")
        transform_jstage()

    case "transform-scielo":
        print("run transform-scielo")
        transform_scielo()

    case "transform-local":
        print("run transform-local")
        transform_local()

    case "setup-db":
        print("setup db")
        db.setup()

    case "export-csv":
        print("export csv")

    case _:
        print(f'unknown mode: {mode}')
