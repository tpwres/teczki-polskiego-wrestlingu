import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict, Literal
from page import page, Page
import html
from urllib.parse import quote
from mistletoe import Document, HtmlRenderer


class Geometry(TypedDict):
    """GeoJSON geometry - supports all geometry types"""
    type: Literal["Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon", "GeometryCollection"]
    coordinates: Any  # Different structure for different geometry types


class FeatureProperties(TypedDict, total=False):
    """Properties for a GeoJSON Feature"""
    slug: str
    name: Optional[str]
    type: str
    description: str
    city: Optional[str]
    # Additional properties from geodict can be added dynamically


class GeoJSONFeature(TypedDict):
    """GeoJSON Feature structure returned by create_feature_dict"""
    type: Literal["Feature"]
    geometry: Geometry
    properties: FeatureProperties


class ZolaLinkingRenderer(HtmlRenderer):
    @staticmethod
    def escape_url(raw: str) -> str:
        if raw.startswith('@') and raw.endswith('.md'):
            # Strip @ and suffix to make it a relative path,
            # add the domain
            raw = f"//tpwres.pl/{raw[2:-3]}"

        return html.escape(quote(raw, safe='/#:()*?=%@+,&;'))

def eval_markdown(text: str) -> str:
    with ZolaLinkingRenderer() as renderer:
        doc = Document(text)
        return renderer.render(doc)

def create_geojson(page: Page) -> Optional[GeoJSONFeature]:
    """Convert a venue page into a GeoJSON feature"""
    fm = page.front_matter
    match fm:
        case {'extra': {'geo': dict(geodict)}} if 'coordinates' in geodict:
            coord_string = geodict['coordinates']
        case _:
            return None

    try:
        sep = '/' if '/' in coord_string else ','
        lat, lon = map(float, coord_string.split(sep))
    except (ValueError, AttributeError):
        raise ValueError(f"Could not parse coordinates {coord_string}")

    return create_feature_dict(lon, lat, geodict, page)

def create_feature_dict(lon: float, lat: float, geodict: Dict[str, Any], page: Page) -> GeoJSONFeature:
    mandatory_properties = ('type', 'description', 'coordinates')
    copy_properties = {key: value for key, value in geodict.items() if key not in mandatory_properties}
    fm = page.front_matter
    desc = page_description(page)
    doc: GeoJSONFeature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "slug": page.path.stem,
            "name": fm.get('title'),
            "type": geodict.get('type', 'venue'),
            "description": eval_markdown(desc),
            **copy_properties
        }
    }
    if city := fm.get('city'):
        doc['properties']['city'] = city

    return doc

def page_description(page) -> str:
    fm = page.front_matter
    path = str(page.path).replace('content/', '@/')
    if 'description' in fm:
        return fm['description']

    return f"[{fm['title']}]({path})"


def load_geojson_file(path: Path) -> List[GeoJSONFeature]:
    """Load features from a GeoJSON file"""
    with path.open('r') as f:
        data = json.load(f)
        match data:
            case {'features': list(features)}:
                return features
            case {'type': 'Feature'}:
                return [data]
            case {'type': 'FeatureCollection'}:
                return [data]
            case _:
                raise ValueError("GeoJSON data must contain either a list of Features or be a single Feature")

def build_features_from(path: Path) -> List[GeoJSONFeature]:
    """
    Scan directory for .md and .geojson files and return a list of GeoJSON features
    """
    features = []

    for file_path in path.glob('*'):
        match file_path:
            case Path(suffix='.md', stem=stem) if stem != '_index':
                venue = page(file_path)
                feature = create_geojson(venue)
                if not feature: continue
                features.append(feature)
            case Path(suffix='.geojson'):
                new_features = load_geojson_file(file_path)
                for i, feature in enumerate(new_features, start=1):
                    props = feature.get('properties', {})
                    desc = props.get('description')
                    if desc:
                        props['description'] = eval_markdown(desc)
                    if 'slug' not in props:
                        props['slug'] = file_path.stem if i == 1 else f'{file_path.stem}-{i}'
                features.extend(new_features)

    return features

def parse_args():
    parser = argparse.ArgumentParser(description='GeoFeatures')
    parser.add_argument('output_file', type=str, nargs='?', help='Output GeoJSON file (default is stdout)')
    return parser.parse_args()

def main():
    args = parse_args()

    features = build_features_from(Path('content/v'))
    output_file = Path(args.output_file).open('w') if args.output_file else sys.stdout
    json.dump(features, output_file)

if __name__ == '__main__':
    main()
