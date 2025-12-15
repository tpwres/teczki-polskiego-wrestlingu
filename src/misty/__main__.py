import sys
from misty import emit_tokens_with_lines

def main():
    if len(sys.argv) > 1:
        stream = open(sys.argv[1], 'r')
    else:
        stream = sys.stdin

    for tok in emit_tokens_with_lines(stream):
        kls, (row, col), content = tok
        colstr = ':01' if col is None else f':{col:02d}'
        print(f"{row}{colstr} | {kls} {content}")

if __name__ == "__main__":
    main()
