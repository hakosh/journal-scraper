import sys

import db
from repos.scielo.download import download_scielo
from repos.scielo.transform import transform

if len(sys.argv) <= 1:
    print("arguments required")
    sys.exit(1)

mode = sys.argv[1]

match mode:
    case "sync":
        print("run scielo")
        download_scielo()

    case "transform":
        print("run transform")
        transform()

    case "setup-db":
        print("setup db")
        db.setup()

    case "export-csv":
        print("export csv")

    case _:
        print(f'unknown mode: {mode}')
