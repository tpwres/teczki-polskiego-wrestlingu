import xml.etree.ElementTree as ET
from pathlib import Path
from sys import stdout
from textwrap import dedent
import pandoc
from pandoc import types as pt
from unidecode import unidecode
from typing import Callable, Optional

ppw_dump = Path('plppwofficial_pages_full.xml')

ignore_prefixes = ['Plik:', 'Szablon:', 'Kategoria:', 'Moduł:']

safe_alphabet = str.maketrans({
    '/': '_',
    ':': '_',
    ' ': '_'
})

zola_safe_alphabet = str.maketrans({
    '(': None,
    ')': None,
    '"': None,
    '_': '-'
})

def safe_chars(title):
    return title.translate(safe_alphabet)

def format_page(title, html):
    return f"""
    <html>
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>{title}</title
      </head>
      <body>
        {html}
      <body>
    </html>
    """

def add_frontmatter(title, text):
    return dedent(f"""\
    +++
    title = {title!r}
    template = "wiki.html"
    +++\n
    """) + text

def html_linkmaker(attr, contents, target):
    dest, kind = target
    if kind != 'wikilink':
        return None
    return (f"{dest}.html", '')

def zola_linkmaker(attr, contents, target):
    dest, kind = target
    if kind != 'wikilink':
        return None
    dest = unidecode(dest).lower().translate(zola_safe_alphabet)
    return (f"/{dest}", '')

def rewrite_ast(block, link_maker):
    match block:
        case pt.Pandoc(_, blocks):
            for blk in blocks:
                rewrite_ast(blk, link_maker)
        case pt.Para(blocks) | pt.Strong(blocks) | pt.Plain(blocks) | pt.Emph(blocks) | pt.BlockQuote(blocks):
            for blk in blocks:
                rewrite_ast(blk, link_maker)
        case pt.Link(attr, contents, target):
            replacement = link_maker(attr, contents, target)
            if replacement:
                block[:] = [attr, contents, replacement]
        case pt.Code(_, _):
            pass
        case pt.RawInline() | pt.RawBlock():
            pass
        case pt.Space() | pt.SoftBreak() | pt.LineBreak():
            pass
        case pt.Str(_):
            pass
        case pt.Header(_, _, contents):
            for blk in contents:
                rewrite_ast(blk, link_maker)
        case pt.BulletList(elem_blocks):
            for elem in elem_blocks:
                for blk in elem:
                    rewrite_ast(blk, link_maker)
        case pt.OrderedList(_attr, elem_blocks):
            for elem in elem_blocks:
                for blk in elem:
                    rewrite_ast(blk, link_maker)
        case _:
            raise RuntimeError(f"{block}")

def make_index_page(all_pages):
    page_links = [f'<li><a href="{safe_chars(title)}.html">{title}</a></li>' for title in all_pages]
    newline = "\n"
    return f"""
    <ul>
      {newline.join(page_links)}
    </ul>
    """

FormatterCallback = Callable[[str, object], str]

def save_to_file(dest: Path, title: str, doc: str, suffix: str, formatter: Optional[FormatterCallback] = None):
    path = (dest / safe_chars(title)).with_suffix(suffix)
    print(f"Saving {path.as_posix()}")
    with path.open('w') as fp:
        if formatter:
            fp.write(formatter(title, doc))
        else:
            fp.write(doc)


def main(dest: Path):
    doc = ET.parse(ppw_dump.open('r'))
    root = doc.getroot()
    ns = '{http://www.mediawiki.org/xml/export-0.11/}'

    all_pages = []
    for page in root.iter(f'{ns}page'):
        title = page.find(f'{ns}title').text
        if any(title.startswith(prefix) for prefix in ignore_prefixes):
            continue

        revisions = page.findall(f'{ns}revision')
        latest = revisions[-1]
        text = latest.find(f'{ns}text').text
        body = pandoc.read(text, format="mediawiki")
        rewrite_ast(body, zola_linkmaker)
        # html = pandoc.write(body, format="html")
        md = pandoc.write(body, format="markdown")
        # save_to_file(dest, title, html, '.html', formatter=format_page)
        save_to_file(dest, str(title), md, '.md', formatter=add_frontmatter)
        all_pages.append(title)

    # save_to_file('index', make_index_page(all_pages), '.html')
    save_to_file(dest, 'All Pages', make_index_page(all_pages), '.md', formatter=add_frontmatter)

if "__main__" == __name__:
    out = Path('pages/content')
    out.mkdir(exist_ok=True)

    main(out)
