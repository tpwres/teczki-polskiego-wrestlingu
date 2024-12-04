#! /bin/bash
# set -x

lint() {
    bin/lint || true
}

create_config() {
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
  #python3 bin/build_metadata.py
  #python3 bin/build_roster.py
  #python3 bin/build_matches.py
  make all plot index

  zola -c build_cloudflare_config.toml build
}

lint
create_config
setup_seo
build
