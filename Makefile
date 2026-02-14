ROSTERS=data/roster_ptw.json \
				data/roster_ddw.json \
        data/roster_kpw.json \
        data/roster_mzw.json \
        data/roster_ppw.json \
        data/roster_dfw.json \
        data/roster_wws.json \
        data/roster_wwe.json
METADATA=data/all_matches.json \
				 data/appearances.json \
         data/crew_appearances.json \
         data/career.json \
				 data/career_v2.json \
         data/team_careers.json \
         data/all_photos.json \
         data/photo_taggings.json \
         data/mapdata.json
PLOTS=data/zieloni.svg data/chronology-2.svg data/ptw-exits.svg
CAL=static/calendar.ics \
    static/calendar-ptw.ics \
    static/calendar-kpw.ics \
    static/calendar-mzw.ics \
    static/calendar-ppw.ics \
		static/calendar-low.ics
MINISEARCH_INDEX=static/minisearch_index.json

all: rosters meta aliases full-flags atr calendar index plot recent
rosters: $(ROSTERS)
aliases: data/aliases.json
full-flags: data/full_flags.json
atr: data/all_time_roster.json
meta: $(METADATA)
calendar: $(CAL)
plot: $(PLOTS)
index: $(MINISEARCH_INDEX)

clean:
	rm -rf $(ROSTERS) $(METADATA) $(PLOTS) $(CAL) $(MINISEARCH_INDEX) data/all_time_roster.json data/aliases.json

data/all_matches.json data/appearances.json data/crew_appearances.json data/appearances_v2.json &: content/e/**/*.md
	bin/build-matches

data/career.json data/career_v2.json data/team_careers.json &: content/e/**/*.md
	bin/build-metadata

data/aliases.json: content/w/*.md
	bin/build-aliases

data/full_flags.json: const/name-to-flag.yaml const/aliases.yaml
	bin/build-fullflags

data/mapdata.json: content/v/
	bin/build-geojson $@

data/all_time_roster.json: data/aliases.json data/career.json const/name-to-flag.yaml const/flags-by-code.json const/emojis.yaml
	bin/build-atr

data/all_photos.json data/photo_taggings.json &: content/e/**/*.md
	bin/build-talent-gallery

$(ROSTERS) &: content/e/**/*.md
	bin/build-roster

clean-plot:
	rm -rf $(PLOTS)

data/chronology-2.svg: const/chronology_2.csv
	bin/build-mg  $< $@

data/zieloni.svg: const/zieloni.csv
	bin/build-mg  $< $@

data/ptw-exits.svg: const/ptw-exits.csv
	bin/build-mg $< $@

static/calendar.ics: content/e/**/*.md
	bin/build-calendar > $@

static/calendar-%.ics: ORG = $(patsubst static/calendar-%.ics,%,$@)
static/calendar-%.ics: content/e/%/*.md
	bin/build-calendar \
		-t $(shell grep -Po 'title = \K(.*)' content/e/${ORG}/_index.md) \
		content/e/${ORG} > $@

recent:
	git restore content/recent-changes.md
	python src/commit_summarizer.py >> content/recent-changes.md

$(MINISEARCH_INDEX): content/**/*.md data/aliases.json
	bin/build-index > $@

requirements.txt: pyproject.toml uv.lock
	uv export -o $@
