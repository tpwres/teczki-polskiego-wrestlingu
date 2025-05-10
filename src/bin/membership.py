import sys
from pathlib import Path
srcdir = Path(__file__).resolve().parent / '..'
sys.path.insert(0, str(srcdir))
from io import BytesIO
import argparse
from sys import stdin, stdout
from types import SimpleNamespace
from timelines import Grapher, SVGFilter


def main():
    options = parse_args()
    grapher = Grapher()
    grapher.process(options.input_file, raw_svg := BytesIO())
    raw_svg.seek(0)
    filter = SVGFilter(metadata=grapher.extra_metadata)
    filter.process(raw_svg, options.output_file)

def parse_args():
  parser = argparse.ArgumentParser(description="Process some input")
  parser.add_argument("input", help="Input file (optional)", default='-', nargs='?')
  parser.add_argument("output", help="Output file (optional)", default='-', nargs='?')
  args = parser.parse_args()

  input_file = stdin if args.input == '-' else Path(args.input).open('r')
  output_file = stdout if args.output == '-' else Path(args.output).open('w')

  return SimpleNamespace(input_file=input_file, output_file=output_file)

if __name__ == "__main__":
    main()
