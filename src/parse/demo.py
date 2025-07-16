import sys
from pathlib import Path
from .rich_doc import RichDoc
from .parser import RichDocParser
from pprint import pprint

if __name__ == "__main__":
    page = Path(sys.argv[1])
    doc = RichDocParser().parse_file(page)
    pprint(doc)
    breakpoint()
