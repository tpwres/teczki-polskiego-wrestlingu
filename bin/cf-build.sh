#! /bin/bash

deps() {
    pip install pyyaml
}

lint() {
    python3 bin/lint.py || true
}

build() {
    python3 bin/build_metadata.py
    python3 bin/build_roster.py
    python3 bin/build_matches.py

    zola build
}

deps
lint
build
