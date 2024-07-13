#! /usr/bin/env python3

from xml.etree import ElementTree as ET
from sys import stdin, stdout, stderr
from pathlib import Path
from page import Page

def main(input_stream, output_stream, orgs):
    ns = dict(
        svg = 'http://www.w3.org/2000/svg',
        xlink = "http://www.w3.org/1999/xlink",
        dc="http://purl.org/dc/elements/1.1/",
        cc="http://creativecommons.org/ns#",
        rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    )
    for key, url in ns.items():
        if key == 'svg':
            # Don't output ns0:svg, browser gets confused
            ET.register_namespace('', url)
        else:
            ET.register_namespace(key, url)

    tree = ET.parse(input_stream)
    root = tree.getroot()
    # Etree doesn't do upwards navigation
    parent_map = {child: parent for parent in tree.iter() for child in parent}
    # TODO: remove all <title> elements

    # Make all text use currentColor
    for fig in root.findall(".//svg:g", ns):
        fig.attrib['fill'] = 'currentColor'

    # Make graph axes use currentColor
    for path in root.findall(".//svg:path", ns):
        style = path.attrib.get('style', '')
        new_style = style.replace('stroke: #000000', 'stroke: currentColor')
        path.attrib['style'] = new_style

    # Make graph ticks use currentColor. This is a bit trickier as they reuse a path element,
    # but apply style to it. The path element was updated in the loop above.
    for use in root.findall(".//svg:use", ns):
        style = use.attrib['style']
        use.attrib['style'] = style.replace('stroke: #000000', 'stroke: currentColor')

    # Replace text in tspan elements with links
    for span in root.findall('.//svg:text', ns):
        text = span.text
        if not (text.startswith('[') or text.endswith(']')):
            continue
        parent = parent_map[span]
        key = text[1:-1]
        if key not in orgs:
            raise ValueError(f"{key} not found in orgs list")
        path = f"/{orgs[key]}".replace(".md", "")

        link = ET.SubElement(parent, "a", {"href": path, "target": "_top"})
        link.append(span)
        span.text = key
        span.attrib['text-decoration'] = 'underline'
        parent.clear()
        parent.append(link)

    tree.write(output_stream, encoding="unicode", default_namespace='')


def load_orgs():
    cwd = Path.cwd()
    content_dir = cwd / 'content'
    orgs_dir = content_dir / "o"
    orgs_pages = {
        Page(p, verbose=False).front_matter['title']: p.relative_to(content_dir)
        for p in orgs_dir.glob("**/*.md")
        if p.name != "_index.md"
    }
    return orgs_pages

if __name__ == "__main__":
    orgs = load_orgs()
    main(open('data/chronology-plot.svg'), stdout, orgs)
