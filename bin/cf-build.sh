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
  cp cf-headers.txt public/_headers
}

lint
create_config
setup_seo
build
