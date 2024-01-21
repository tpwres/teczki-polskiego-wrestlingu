#! /bin/bash

deps() {
    pip install pyyaml
}

lint() {
    bin/lint.py || true
}

build() {
    bin/build_metadata.py
    bin/build_roster.py
    bin/build_matches.py
}

deps
lint
build
