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
         data/all_photos.json \
         data/photo_taggings.json
PLOTS=data/chronology-hyperlinked.svg
CAL=static/calendar.ics \
    static/calendar-ptw.ics \
    static/calendar-kpw.ics \
    static/calendar-mzw.ics \
    static/calendar-ppw.ics \
		static/calendar-low.ics
MINISEARCH_INDEX=static/minisearch_index.json

all: rosters meta aliases atr calendar index plot
rosters: $(ROSTERS)
aliases: data/aliases.json
atr: data/all_time_roster.json
meta: $(METADATA)
calendar: $(CAL)
plot: $(PLOTS)
index: $(MINISEARCH_INDEX)

clean:
	rm -rf $(ROSTERS) $(METADATA) $(PLOTS) $(CAL) $(MINISEARCH_INDEX) data/all_time_roster.json data/aliases.json

data/all_matches.json data/appearances.json data/crew_appearances.json data/appearances_v2.json &: content/e/**/*.md
	bin/build-matches

data/career.json: content/e/**/*.md
	bin/build-metadata

data/aliases.json: content/w/*.md
	bin/build-aliases

data/all_time_roster.json: data/aliases.json data/career.json const/name-to-flag.yaml const/flags-by-code.json const/emojis.yaml
	bin/build-atr

data/all_photos.json data/photo_taggings.json &: content/e/**/*.md
	bin/build-talent-gallery

$(ROSTERS) &: content/e/**/*.md
	bin/build-roster

clean-plot:
	rm -rf data/chronology-hyperlinked.svg data/chronology-plot.svg

data/chronology-plot.svg: const/chronology.csv
	bin/plot-chronology $^ > $@

data/chronology-hyperlinked.svg: data/chronology-plot.svg
	bin/linkify-plot < $< > $@

static/calendar.ics: content/e/**/*.md
	bin/build-calendar > $@

static/calendar-%.ics: ORG = $(patsubst static/calendar-%.ics,%,$@)
static/calendar-%.ics: content/e/%/*.md
	bin/build-calendar \
		-t $(shell grep -Po 'title = \K(.*)' content/e/${ORG}/_index.md) \
		content/e/${ORG} > $@

$(MINISEARCH_INDEX): content/**/*.md
	bin/build-index > $@
