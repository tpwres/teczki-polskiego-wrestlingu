import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from page import page, Page

def create_geojson(page: Page) -> Optional[Dict[str, Any]]:
    """Convert a venue page into a GeoJSON feature"""
    fm = page.front_matter
    match fm:
        case {'extra': {'geo': dict(geodict)}} if 'coordinates' in geodict:
            coord_string = geodict['coordinates']
        case _:
            return None

    try:
        lon, lat = map(float, coord_string.split(','))
    except (ValueError, AttributeError):
        raise ValueError(f"Could not parse coordinates {coord_string}")

    return create_feature_dict(lon, lat, geodict, title=fm.get('title'), city=fm.get('city'))

def create_feature_dict(lon: float, lat: float, geodict: Dict[str, Any], /, title, city) -> Dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lat, lon]
        },
        "properties": {
            "name": title,
            "type": geodict.get('type', 'venue'),
            "city": city,
            "description": geodict.get('description')
        }
    }

def load_geojson_file(path: Path) -> List[Dict[str, Any]]:
    """Load features from a GeoJSON file"""
    with path.open('r') as f:
        data = json.load(f)
        if 'features' in data:
            return data['features']
        elif 'type' in data and data['type'] == 'Feature':
            return [data]
        return []

def build_features_from(path: Path) -> List[Dict[str, Any]]:
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
                features.extend(load_geojson_file(file_path))

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
