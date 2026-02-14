import sys
from misty import emit_tokens_with_lines

def main():
    if len(sys.argv) > 1:
        stream = open(sys.argv[1], 'r')
    else:
        stream = sys.stdin

    toks = list(emit_tokens_with_lines(stream))
    for tok in toks:
        kls, (row, col), content = tok
        colstr = ':01' if col is None else f':{col:02d}'
        print(f"{row}{colstr} | {kls} {content}")

    breakpoint()

if __name__ == "__main__":
    main()
