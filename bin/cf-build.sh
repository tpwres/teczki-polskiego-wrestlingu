#! /bin/bash
set -x

deps() {
    pip3 install pyyaml
}

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


build() {
    python3 bin/build_metadata.py
    python3 bin/build_roster.py
    python3 bin/build_matches.py

    zola -c build_cloudflare_config.toml build
}

deps
lint
create_config
build
