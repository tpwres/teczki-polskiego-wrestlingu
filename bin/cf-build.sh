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
  # In CF Workers, the base url in previews is either
  # <sha-prefix>-<workername>.<domain>.workers.dev or <branchname>-<workername>.<domain>.workers.dev
  # where the prefix is usually 8 hexdigits long. The branch name is found in $WORKERS_CI_BRANCH,
  # and the worker name in $WRANGLER_CI_OVERRIDE_NAME, both provided by Workers Builds env.
  case $WORKERS_CI_BRANCH in
      main)
          export BASE_URL=https://$PRODUCTION_URL
          ;;
      *)
          export BASE_URL=https://$WORKERS_CI_BRANCH-$WRANGLER_CI_OVERRIDE_NAME.$WORKERS_DOMAIN
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

  export SITEMAP_ROOT=${SITEMAP_ROOT_URL:-$BASE_URL}
  envsubst < templates/sitemap_template.xml > templates/sitemap.xml
  envsubst < templates/robots_template.txt > templates/robots.txt
}

build() {
  make -j$(nproc) all plot index

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
