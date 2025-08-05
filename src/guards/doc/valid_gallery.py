from pathlib import Path
import json
from dataclasses import dataclass
from typing import Any, Optional
import tomllib

from parse import blocks
from guards.main.base import Base

@dataclass
class BucketItem:
    path: str
    modified: str
    size: int
    etag: str

class ValidGallery(Base):
    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        extra = frontmatter.get('extra', {})
        return 'gallery' in extra

    def __init__(self):
        super().__init__()
        self.image_index = self.load_image_index()

    def load_image_index(self):
        path = Path('r2_bucket_index.json')
        if not path.exists():
            return {}

        with path.open('rb') as fp:
            return {
                path: BucketItem(path, modified, size, etag[1:-1])
                for (path, modified, size, etag) in  json.load(fp)
            }

    def load_gallery(self, frontmatter: dict) -> tuple[Optional[Path], dict]:
        # 1. If gallery is empty, try locating the manifest toml in default locations
        # 2. If manifest found, load from manifest, but also set location to manifest file
        # 3. If gallery is not empty, but has the manifest key, load from that manifest
        # 4. If gallery is not empty and has items, load directly from gallery
        extra = frontmatter.get('extra', {})
        gallery_info = extra.get('gallery', {})

        if len(gallery_info) == 0:
            manifest_path, content = self.find_and_load_default_manifest()
            if manifest_path:
                return manifest_path, content or {}
            else:
                return None, {}
        elif 'manifest' in gallery_info:
            manifest_path = convert_at_path(gallery_info['manifest'])
            if manifest_path.exists():
                return manifest_path, self.load_manifest_file(manifest_path) or {}
            else:
                # TODO: flag error if manifest is missing
                return None, {}
        else:
            return self.path, gallery_info

    def validate_frontmatter(self, frontmatter: dict, block: blocks.FrontMatterBlock):
        content_path, gallery = self.load_gallery(frontmatter)
        if not gallery:
            return

        with self.logger.parsing_context('ValidGallery', content_path.as_posix()):
            for key, entry in gallery.items():
                self.validate_gallery_entry(key, entry)

    def validate_gallery_entry(self, key: str, entry: dict):
        match entry:
            case {'path': str(path), 'caption': str(caption), 'source': str(_)}:
                # TODO: Caption needs to go through a ContentLinks validation process
                img_path = (self.path.parent / self.path.stem / path).relative_to('content')
                if img_path.as_posix() not in self.image_index:
                    self.report_missing_entry(key, entry, img_path.parent.as_posix())
            case {'path': str(_), 'caption': str(_)}:
                self.logger.log_error(f"Missing source for gallery item {key}")
            case {'path': str(_), 'source': str(_)}:
                self.logger.log_error(f"Missing caption for gallery item {key}")
            case {'path': str(_)}:
                self.logger.log_error(f"Missing source and caption for gallery item {key}")

    def report_missing_entry(self, key, entry, parent):
        filename = entry['path']
        self.logger.log_error(f"File `{filename}` not found under `{parent}`. Ensure the file has been uploaded, and the extension is correct.")

    def find_and_load_default_manifest(self) -> tuple[Optional[Path], Optional[dict]]:
        # TODO: I need my path, and guardian doesn't provide it yet
        default_manifest_locations = (
            self.path.with_suffix('.toml'),
            self.path.with_name(self.path.stem + '-gallery').with_suffix('.toml')
        )

        manifest = next((loc for loc in default_manifest_locations if loc.exists()), None)
        if manifest:
            return manifest, self.load_manifest_file(manifest)

        return None, None

    def load_manifest_file(self, pathname: Path) -> Optional[dict]:
        with pathname.open('rb') as fp:
            return tomllib.load(fp)

def convert_at_path(at_path: str) -> Path:
    return Path(at_path.replace('@/', 'content/'))
