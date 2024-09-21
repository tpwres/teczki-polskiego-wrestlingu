ROSTERS=data/roster_ptw.json \
        data/roster_kpw.json \
        data/roster_mzw.json \
        data/roster_ppw.json \
        data/roster_dfw.json \
        data/roster_wws.json \
        data/roster_wwe.json
METADATA=data/all_matches.json data/appearances.json data/crew_appearances.json data/career.json
PLOTS=data/chronology-hyperlinked.svg
CAL=static/calendar.ics \
    static/calendar-ptw.ics \
    static/calendar-kpw.ics \
    static/calendar-mzw.ics \
    static/calendar-ppw.ics
MINISEARCH_INDEX=static/minisearch_index.json

all: rosters meta calendar index plot
rosters: $(ROSTERS)
meta: $(METADATA)
calendar: $(CAL)
plot: $(PLOTS)
index: $(MINISEARCH_INDEX)

clean:
	rm -rf $(ROSTERS) $(METADATA) $(PLOTS) $(CAL) $(MINISEARCH_INDEX)

data/all_matches.json data/appearances.json data/crew_appearances.json: content/e/**/*.md
	bin/build-matches

data/career.json: content/e/**/*.md
	bin/build-metadata

data/roster_ptw.json data/roster_kpw.json data/roster_ppw.json data/roster_dfw.json: content/e/**/*.md
	bin/build-roster

data/roster_mzw.json data/roster_wws.json data/roster_wwe.json: content/e/**/*.md
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
