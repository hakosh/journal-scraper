import sys

import db
import transform
from repos import scielo

if len(sys.argv) <= 1:
    print("arguments required")
    sys.exit(1)

mode = sys.argv[1]

match mode:
    case "sync":
        scielo.run()

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
