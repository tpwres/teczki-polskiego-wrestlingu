#! /bin/bash
# set -x

install_zola() {
	asdf plugin add zola https://github.com/salasrod/asdf-zola
	asdf install zola 0.20.0
	asdf global zola 0.20.0
}

lint() {
    bin/lint || true
}

create_config() {
  # This env setup step is useless now - these variables aren't exposed to workers,
  # and there is no replacement. base_url should be set to '/' always
  case $CF_PAGES_BRANCH in
      main)
          export BASE_URL=$PRODUCTION_URL
          ;;
      *)
          export BASE_URL=$CF_PAGES_URL
          ;;
  esac

  envsubst < cloudflare-config.toml > build_cloudflare_config.toml
}

setup_seo() {
  # Find the last-modified dates of all files under content/
  # Edit each file inline, inserting updated= into front matter
  git fetch --unshallow
  git ls-files content/ | \
  grep -Ev '_index\.md$' | \
  while read FILE; do
      git log --pretty="$FILE %as" -1 -- "$FILE"
  done | while read FILE MTIME; do
      sed -i "0,/+++/s//&\nupdated = \"$MTIME\"/" "$FILE"
  done

  export SITEMAP_ROOT=${SITEMAP_ROOT_URL:-$CF_PAGES_URL}
  envsubst < templates/sitemap_template.xml > templates/sitemap.xml
  envsubst < templates/robots_template.txt > templates/robots.txt
}


build() {
  make all plot index

  zola -c build_cloudflare_config.toml build
  cp data/appearances_v2.json public/
  cp data/all_matches.json public/
  cp data/all_photos.json public/
  cp data/talent_photos.json public/
  cp data/mapdata.json public/map_objects.json
}

lint
install_zola
create_config
setup_seo
build
