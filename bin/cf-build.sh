#! /bin/bash
# set -x
set -euo pipefail

MISE=node_modules/mise/bin/mise

asdf_to_mise() {
  while read -r pkg versions; do
    [[ "$pkg" =~ ^#|^$ ]] && continue # skip comments and empty
    for ver in $versions; do
      path=$(asdf where "$pkg" "$ver" 2>/dev/null) && $MISE ln "$pkg@$ver" "$path"
    done
  done
}
mise_from_nodemodules() {
  sed -i '/^dart-sass-embedded/d' $HOME/.tool-versions
  asdf_to_mise < $HOME/.tool-versions
  $MISE run bootstrap
}

lint() {
    bin/lint || true
}

create_config() {
  envsubst < cloudflare-config.toml > build_cloudflare_config.toml
}

setup_seo() {
  set -x
  # Find the last-modified dates of all files under content/
  # Edit each file inline, inserting updated= into front matter
  git fetch --depth=50 origin $(git branch --show-current)
  git ls-files content/ | \
  grep -Ev '_index\.md$' | \
  while read FILE; do
      git log --pretty="$FILE %as" -1 -- "$FILE"
  done | while read FILE MTIME; do
      sed -i "0,/+++/s//&\nupdated = \"$MTIME\"/" "$FILE"
  done

  if [[ -n "$CF_PAGES" ]]; then
    case $CF_PAGES_BRANCH in
      main)
        export BASE_URL=https://tpwres.pl
        ;;
      *)
        export BASE_URL=$CF_PAGES_URL
        ;;
    esac
  fi
  envsubst < templates/sitemap_template.xml > templates/sitemap.xml
  envsubst < templates/robots_template.txt > templates/robots.txt
}

build() {
  make -j$(nproc) all plot index

  zola -c build_cloudflare_config.toml build
  install -t public data/appearances_v2.json data/all_matches.json data/all_photos.json data/talent_photos.json
  cp data/mapdata.json public/map_objects.json
}


mise_from_nodemodules
# lint
create_config
setup_seo
build

