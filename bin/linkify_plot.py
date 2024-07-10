#! /usr/bin/env python3

from xml.etree import ElementTree as ET
from sys import stdin, stdout
from pathlib import Path
from page import Page

def main(input_stream, output_stream, orgs):
    ns = dict(
        svg = 'http://www.w3.org/2000/svg'
    )
    ET.register_namespace('', ns['svg']) # Don't output ns0:svg, browser gets confused

    tree = ET.parse(input_stream)
    root = tree.getroot()
    # Etree doesn't do upwards navigation
    parent_map = {child: parent for parent in tree.iter() for child in parent}
    # TODO: remove all <title> elements
    # Remove fill from text boxes
    for grp in root.findall(".//svg:g[@color='black']", ns):
        grp.attrib['color'] = 'currentColor'
        for el in grp:
            if 'fill' not in el.attrib: continue
            el.attrib['fill'] = 'currentColor'

    # Replace text in tspan elements with links
    for span in root.findall('.//svg:tspan', ns):
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
    main(stdin, stdout, orgs)
