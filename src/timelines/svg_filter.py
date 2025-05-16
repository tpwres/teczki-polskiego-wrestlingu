from xml.etree import ElementTree as ET
from typing import Tuple, Optional
from pathlib import Path
from page import page
import re
from sys import stderr

NS = dict(
        svg = 'http://www.w3.org/2000/svg',
        xlink = "http://www.w3.org/1999/xlink",
        dc = "http://purl.org/dc/elements/1.1/",
        cc = "http://creativecommons.org/ns#",
        rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
)

for key, url in NS.items():
    ET.register_namespace('' if key == 'svg' else key, url)

def parse_styles(text) -> dict[str, str]:
    # Only handles inline styles as produced by matplotlib
    return {keyword.strip(): style.strip() for keyword, _, style in (decl.partition(':') for decl in text.split(";"))}

def pack_styles(style_dict) -> str:
    return ';'.join(f"{keyword}: {style}" for keyword, style in style_dict.items())

class SVGFilter:
    def process(self, input_stream, output_stream):
        tree = ET.parse(input_stream)
        root = tree.getroot()
        self.parent_map = {child: parent for parent in tree.iter() for child in parent}

        self.apply_axis_colors(root)
        self.apply_graph_patch_colors(root)
        self.strip_extra_text_styling(root)
        self.apply_legend_background(root)
        self.create_link_elements(root)

        tree.write(output_stream, encoding='unicode', default_namespace='')
        self.emit_js(output_stream)

    def apply_axis_colors(self, root):
        # Ticks
        axis1 = root.find('.//svg:g[@id="matplotlib.axis_1"]', NS)
        # There is a path element here in defs that is reused
        pathdef = axis1.find('.//svg:g//svg:defs/svg:path', NS)
        self.use_currentcolor(pathdef)


        axis2 = root.find('.//svg:g[@id="matplotlib.axis_2"]', NS)
        pathdef = axis2.find('.//svg:g//svg:defs/svg:path', NS)
        self.use_currentcolor(pathdef)

        # Tick labels
        y_ticks = [el for el in axis2.findall('.//svg:g', NS) if el.attrib.get('id', '').startswith('ytick_')]
        for tick in y_ticks:
            text = tick.find('.//svg:text', NS)
            self.use_currentcolor(text)

        x_ticks = [el for el in axis1.findall('.//svg:g', NS) if el.attrib.get('id', '').startswith('xtick_')]
        for tick in x_ticks:
            text = tick.find('./svg:g/svg:text', NS)
            if text is None:
                continue
            self.use_currentcolor(text)

        # Spines
        spines = [el for el in root.findall('.//svg:g[@id="axes_1"]//svg:g', NS) if '-spine' in el.attrib.get('id', '')]
        for spine in spines:
            # These contain one element, the <path>
            path = spine[0]
            self.use_currentcolor(path)

    def use_currentcolor(self, elem):
        style = elem.attrib.get('style', '')
        style = (style.replace('fill: #ff00ff', 'fill: currentColor')
                        .replace('stroke: #ff00ff', 'stroke: currentColor'))
        elem.attrib['style'] = style

    def apply_graph_patch_colors(self, root):
        patches = [el for el in root.findall('.//svg:g[@id="axes_1"]/svg:g', NS) if el.attrib.get('id', '').startswith('stripe')]
        for patch in patches:
            # Not a typo, there's only one children <path> element
            path = patch[0]
            style = path.attrib.get('style', '')
            style = style.replace('fill: #ff00ff', 'fill: currentColor')
            path.attrib['style'] = style

    def apply_text_color(self, root):
        pass

    def apply_legend_background(self, root):
        legend = root.find('.//svg:g[@id="legend_1"]', NS)
        # First g>path is the background
        bg = legend[0][0]
        style = bg.attrib['style']
        style = style.replace('fill: #ff00ff', 'fill: none')
        bg.attrib['style'] = style

        # All text elements
        for text in legend.findall('.//svg:g//svg:text', NS):
            text.attrib['style'] += '; fill: currentColor' # Lazy but works


    def strip_extra_text_styling(self, root):
        for text in root.findall('.//svg:text', NS):
            styles = parse_styles(text.attrib['style'])
            if 'font' in styles:
                styles['font'] = re.sub(r'^(\d+\s*px).*', '\\1 sans-serif', styles['font'])
            text.attrib['style'] = pack_styles(styles)

    def create_link_elements(self, root):
        for span in root.findall('.//svg:text', NS):
            text = span.text

            if not text:
                continue

            if not (text.startswith('[') or text.endswith(']')):
                continue

            parent = self.parent_map[span]
            key = text[1:-1]
            match self.resolve_link(key):
                case [title, target]:
                    link = ET.SubElement(parent, "a", {"href": target, "target": "_top"})
                    link.append(span)
                    span.text = title
                    span.attrib['text-decoration'] = 'underline'
                    parent.clear()
                    parent.append(link)

    def resolve_link(self, key: str) -> Optional[Tuple[str, str]]:
        # NOTE: Could be cached
        section, _, title = key.partition('/')
        content_root = Path('content')
        for candidate_path in (content_root / section).glob('*.md'):
            doc = page(candidate_path)
            if doc.title == title:
                return (title, f"/{candidate_path.relative_to(content_root).with_suffix('')}")

    def emit_js(self, stream):
        pass
