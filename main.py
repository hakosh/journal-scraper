import sys

import db
import scielo
import transform

if len(sys.argv) <= 1:
    print("arguments required")
    sys.exit(1)

mode = sys.argv[1]

match mode:
    case "sync":
        if len(sys.argv) >= 3:
            page_from = int(sys.argv[2])
            scielo.sync(page_from)
        else:
            scielo.sync()

    case "transform":
        print("run transform")
        transform.run()

    case "setup-db":
        print("setup db")
        db.setup()

    case "export-csv":
        print("export csv")

    case _:
        print(f'unknown mode: {mode}')

text1 = ""
