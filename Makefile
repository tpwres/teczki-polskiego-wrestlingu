ROSTERS=data/roster_ptw.json \
				data/roster_ddw.json \
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
gem: gemini_files gemini_writer.lua themes/gem/**/*.html

.DELETE_ON_ERROR:

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

gemini_files: public capsule gemini_w gemini_e gemini_a gemini_c gemini_v capsule/index.gmi

public:
	zola build

gemini_e: $(patsubst public/e/kpw/%/index.html, capsule/e/kpw/%.gmi, $(wildcard public/e/kpw/**/*.html))
gemini_e: $(patsubst public/e/ptw/%/index.html, capsule/e/ptw/%.gmi, $(wildcard public/e/ptw/**/*.html))
gemini_e: $(patsubst public/e/ppw/%/index.html, capsule/e/ppw/%.gmi, $(wildcard public/e/ppw/**/*.html))
gemini_e: $(patsubst public/e/mzw/%/index.html, capsule/e/mzw/%.gmi, $(wildcard public/e/mzw/**/*.html))
gemini_e: $(patsubst public/e/low/%/index.html, capsule/e/low/%.gmi, $(wildcard public/e/low/**/*.html))

gemini_w: $(patsubst public/w/%/index.html, capsule/w/%.gmi, $(wildcard public/w/**/*.html))
gemini_a: $(patsubst public/a/%/index.html, capsule/a/%.gmi, $(wildcard public/a/**/*.html))
gemini_c: $(patsubst public/c/%/index.html, capsule/c/%.gmi, $(wildcard public/c/**/*.html))
gemini_v: $(patsubst public/v/%/index.html, capsule/v/%.gmi, $(wildcard public/v/**/*.html))

capsule/index.gmi: public/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule:
	mkdir -p $@

HTML2GEM=pandoc --fail-if-warnings -f html -t gemini_writer.lua

capsule/w/%.gmi: public/w/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/a/%.gmi: public/a/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/c/%.gmi: public/c/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/v/%.gmi: public/v/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/e/kpw/%.gmi: public/e/kpw/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/e/ptw/%.gmi: public/e/ptw/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/e/ppw/%.gmi: public/e/ppw/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/e/mzw/%.gmi: public/e/mzw/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@

capsule/e/low/%.gmi: public/e/low/%/index.html
	@mkdir -p $(@D)
	$(HTML2GEM) < $^ > $@
