from pathlib import Path
import re
from sys import stderr
from typing import Tuple, Optional
from xml.etree import ElementTree as ET

from page import page

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
    def __init__(self, metadata={}):
        self.metadata = metadata

    def process(self, input_stream, output_stream):
        tree = ET.parse(input_stream)
        root = tree.getroot()
        self.parent_map = {child: parent for parent in tree.iter() for child in parent}

        self.apply_axis_colors(root)
        self.apply_graph_patch_colors(root)
        self.apply_vline_text_color(root)
        self.strip_extra_text_styling(root)
        self.apply_legend_background(root)
        self.apply_legend_colors(root)
        self.style_and_hide_annotations(root)
        self.create_link_elements(root)
        self.style_bg_stripes(root)

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
        y_ticks = [el for el in axis2.findall('.//svg:g', NS) if el.get('id', '').startswith('ytick_')]
        for tick in y_ticks:
            text = tick.find('.//svg:text', NS)
            self.use_currentcolor(text)

        x_ticks = [el for el in axis1.findall('.//svg:g', NS) if el.get('id', '').startswith('xtick_')]
        for tick in x_ticks:
            text = tick.find('./svg:g/svg:text', NS)
            if text is None:
                continue
            self.use_currentcolor(text)

        # Spines
        spines = [el for el in root.findall('.//svg:g[@id="axes_1"]//svg:g', NS) if '-spine' in el.get('id', '')]
        for spine in spines:
            # These contain one element, the <path>
            path = spine[0]
            self.use_currentcolor(path)

    def apply_graph_patch_colors(self, root):
        patches = [el for el in root.findall('.//svg:g[@id="axes_1"]/svg:g', NS) if el.get('id', '').startswith('stripe')]
        for patch in patches:
            # Not a typo, there's only one children <path> element
            path = patch[0]
            style = path.get('style', '')
            style = style.replace('fill: #ff00ff', 'fill: currentColor')
            path.set('style', style)

    def apply_vline_text_color(self, root):
        # Add filter to defs
        groups = [el for el in root.findall('.//svg:g[@id="axes_1"]/svg:g', NS) if el.get('id', '').startswith('vline-text')]
        for group in groups:
            box = group[0][0]
            self.edit_style(box, ('fill: #ff00fe', 'fill: var(--accent-bg)'), ('stroke: #ff00ff', 'stroke: currentColor'))
            text = group[-1]
            self.use_currentcolor(text)

    def apply_legend_background(self, root):
        legend = root.find('.//svg:g[@id="legend_1"]', NS)
        if legend is None:
            return
        # First g>path is the background
        bg = legend[0][0]
        style = bg.get('style')
        style = style.replace('fill: #ff00ff', 'fill: none')
        bg.set('style', style)

        # All text elements
        for text in legend.findall('.//svg:g//svg:text', NS):
            text.attrib['style'] += '; fill: currentColor' # Lazy but works

    def apply_legend_colors(self, root):
        groups = [el for el in root.findall('.//svg:g[@id="legend_1"]/svg:g', NS) if el.get('id', '').startswith('patch_')]
        for group in groups:
            path = group[0]
            self.use_currentcolor(path)

    def strip_extra_text_styling(self, root):
        for text in root.findall('.//svg:text', NS):
            styles = parse_styles(text.get('style'))
            if 'font' in styles:
                styles['font'] = re.sub(r'^(\d+\s*px).*', '\\1 sans-serif', styles['font'])
            text.set('style', pack_styles(styles))

    def style_and_hide_annotations(self, root):
        anns = [el for el in root.findall('.//svg:g[@id="axes_1"]/svg:g', NS) if el.get('id').startswith('ann-')]
        for ann in anns:
            ann.set('style', 'visibility: hidden')
            patch, text = ann[0][0], ann[1]
            self.edit_style(patch, ('fill: #ff00ff', 'fill: var(--accent-bg)'))
            self.use_currentcolor(text)


    def create_link_elements(self, root):
        for span in root.findall('.//svg:text', NS):
            text = span.text

            if not text:
                continue

            parent = self.parent_map[span]
            match self.resolve_link(text, span, parent):
                case [title, target]:
                    parent.remove(span)
                    link = ET.SubElement(parent, "a", {"href": target, "target": "_top"})
                    link.append(span)
                    span.text = title
                    span.attrib['text-decoration'] = 'underline'
                    parent.append(link)

    def style_bg_stripes(self, root):
        bgstripes = [el for el in root.findall(".//svg:g[@id='figure_1']//svg:g", NS) if el.get('id', '').startswith('bg-')]
        for el in bgstripes:
            path = el[0]
            self.edit_style(path, ('stroke: #ff00ff', 'stroke: none'), ('fill: #ff00ff', 'fill: transparent'))

    def resolve_link(self, key: str, elem, parent) -> Optional[Tuple[str, str]]:
        # TODO: All of this can be replaced with the metadata links lookup
        if key.startswith('[') and key.endswith(']'):
            return self.resolve_simple_link(key[1:-1])
        elif parent.get('id') in self.metadata:
            return self.resolve_metadata_link(key, elem, parent)
        elif 'links' in self.metadata and key in self.metadata['links']:
            return self.resolve_explicit_link(key)

    def resolve_explicit_link(self, key: str) -> Optional[Tuple[str, str]]:
        links = self.metadata['links']
        return (key, links[key]['href'])

    def resolve_metadata_link(self, key: str, elem, parent) -> Optional[Tuple[str, str]]:
        gid = parent.get('id')
        attrs = self.metadata.get(gid, {})
        if not attrs:
            return

        href = attrs.get('href')
        if href:
            return (key, href)

    def resolve_simple_link(self, key: str) -> Optional[Tuple[str, str]]:
        # NOTE: Could be cached
        section, _, title = key.partition('/')
        content_root = Path('content')
        for candidate_path in (content_root / section).glob('*.md'):
            doc = page(candidate_path)
            if doc.title == title:
                return (title, f"/{candidate_path.relative_to(content_root).with_suffix('')}")

    def edit_style(self, elem, *replacements):
        if not hasattr(elem, 'attrib'):
            return
        style = elem.attrib.get('style', '')
        for before, after in replacements:
            style = style.replace(before, after)

        elem.attrib['style'] = style

    def use_currentcolor(self, elem):
        self.edit_style(elem,
                        ('fill: #ff00ff', 'fill: currentColor'),
                        ('stroke: #ff00ff', 'stroke: currentColor'))


    def emit_js(self, stream):
        res = Path(__file__).resolve().parent / 'graph.js'
        jscode = res.read_text()
        stream.write(f'<script type="module">\n{jscode}\n</script>')
