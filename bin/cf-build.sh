#! /bin/bash
set -x

lint() {
    python3 bin/lint.py || true
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
