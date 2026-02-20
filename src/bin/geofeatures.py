import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict, cast
from urllib.parse import quote
from content import ZipContentTree, FilesystemTree

from mistletoe import Document, HtmlRenderer  # pyright: ignore[reportMissingTypeStubs]

class Geometry(TypedDict):
    """GeoJSON geometry - supports all geometry types"""

    type: Literal[
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
        "GeometryCollection",
    ]
    # Different structure for different geometry types
    coordinates: Any


class FeatureProperties(TypedDict):
    """Properties for a GeoJSON Feature"""

    slug: str
    name: str
    type: str
    description: str
    city: str | None
    # Additional properties from geodict can be added dynamically


class GeoJSONFeature(TypedDict):
    """GeoJSON Feature structure returned by create_feature_dict"""

    type: Literal["Feature"]
    geometry: Geometry
    properties: FeatureProperties


class ZolaLinkingRenderer(HtmlRenderer):
    @staticmethod
    def escape_url(raw: str) -> str:
        if raw.startswith("@") and raw.endswith(".md"):
            # Strip @ and suffix to make it a relative path,
            # add the domain
            raw = f"//tpwres.pl/{raw[2:-3]}"

        return html.escape(quote(raw, safe="/#:()*?=%@+,&;"))


def eval_markdown(text: str) -> str:
    with ZolaLinkingRenderer() as renderer:
        doc = Document(text)
        return renderer.render(doc)


def create_geojson(page: Page) -> GeoJSONFeature | None:
    """Convert a venue page into a GeoJSON feature"""
    fm = dict(page.front_matter)
    match fm:
        case {"extra": {"geo": dict(geodict)}} if "coordinates" in geodict:
            coord_string = geodict["coordinates"]
        case _:
            # No geodata
            return None

    # Reachability: if the first case statement above matches, then geodict is bound in scope, and available after the match block, and so is coord_string.
    # Otherwise, the code returns early. Therefore, geodict and coord_string are always available here, and this is not unreachable code.
    try:
        sep = "/" if "/" in coord_string else ","
        lat, lon = map(float, coord_string.split(sep))
    except (ValueError, AttributeError):
        raise ValueError(f"Could not parse coordinates {coord_string}")

    return create_feature_dict(lon, lat, geodict, page)


def create_feature_dict(
    lon: float, lat: float, geodict: dict[str, Any], page: Page
) -> GeoJSONFeature:
    mandatory_properties = ("type", "description", "coordinates")
    copy_properties = {
        key: value for key, value in geodict.items() if key not in mandatory_properties
    }
    fm = page.front_matter
    desc = page_description(page)
    doc: GeoJSONFeature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": cast(
            FeatureProperties,
            {
                "slug": page.path.stem,
                "name": str(fm.get("title")),
                "type": str(geodict.get("type", "venue")),
                "description": eval_markdown(desc),
                **copy_properties,
            },
        ),
    }
    if city := fm.get("city"):
        doc["properties"]["city"] = str(city)

    return doc


def page_description(page) -> str:
    fm = page.front_matter
    path = str(page.path).replace("content/", "@/")
    if "description" in fm:
        return fm["description"]

    return f"[{fm['title']}]({path})"


def load_geojson_file(io) -> list[GeoJSONFeature]:
    """Load features from a GeoJSON file"""
    data = json.load(io)
    match data:
        case {"features": list(features)}:
            return features
        case {"type": "Feature"}:
            return [data]
        case {"type": "FeatureCollection"}:
            return [data]
        case _:
            raise ValueError(
                "GeoJSON data must contain either a list of Features or be a single Feature"
            )


def build_features_from(content) -> list[GeoJSONFeature]:
    """
    Scan directory for .md and .geojson files and return a list of GeoJSON features
    """
    features = []

    for pageio in content.glob('content/v/*'):
        file_path = content.to_path(pageio)
        match file_path:
            case Path(suffix=".md", stem=stem) if stem != "_index":
                venue = content.page(pageio)
                feature = create_geojson(venue)
                if not feature:
                    continue
                features.append(feature)
            case Path(suffix=".geojson"):
                new_features = load_geojson_file(pageio)
                for i, feature in enumerate(new_features, start=1):
                    props = feature.get("properties", {})
                    desc = props.get("description")
                    if desc:
                        props["description"] = eval_markdown(desc)
                    if "slug" not in props:
                        props["slug"] = (
                            file_path.stem if i == 1 else f"{file_path.stem}-{i}"
                        )
                features.extend(new_features)

    return features


def parse_args():
    parser = argparse.ArgumentParser(description="GeoFeatures")
    parser.add_argument(
        "output_file",
        type=str,
        nargs="?",
        help="Output GeoJSON file (default is stdout)",
    )
    parser.add_argument('-z', '--zipfile')
    return parser.parse_args()


def main():
    args = parse_args()
    cwd = Path.cwd()

    if args.zipfile:
        content = ZipContentTree(Path(args.zipfile.strip()))
    else:
        content = FilesystemTree(cwd)

    features = build_features_from(content)
    output_file = Path(args.output_file).open("w") if args.output_file else sys.stdout
    json.dump(features, output_file)


if __name__ == "__main__":
    main()
