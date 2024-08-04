ROSTERS=data/roster_ptw.json \
        data/roster_kpw.json \
        data/roster_mzw.json \
        data/roster_ppw.json \
        data/roster_dfw.json \
        data/roster_wws.json \
        data/roster_wwe.json
METADATA=data/all_matches.json data/appearances.json data/crew_appearances.json data/career.json
PLOTS=data/chronology-hyperlinked.svg
CAL=static/calendar.ics
MINISEARCH_INDEX=static/minisearch_index.json

all: $(ROSTERS) $(METADATA) $(CAL) $(MINISEARCH_INDEX)
plot: $(PLOTS)
index: $(MINISEARCH_INDEX)

clean:
	rm -rf $(ROSTERS) $(METADATA) $(PLOTS) $(CAL) $(MINISEARCH_INDEX)

data/all_matches.json data/appearances.json data/crew_appearances.json: content/e/**/*.md
	bin/build_matches.py

data/career.json: content/e/**/*.md
	bin/build_metadata.py

data/roster_ptw.json data/roster_kpw.json data/roster_ppw.json data/roster_dfw.json: content/e/**/*.md
	bin/build_roster.py

data/roster_mzw.json data/roster_wws.json data/roster_wwe.json: content/e/**/*.md
	bin/build_roster.py

clean-plot:
	rm -rf data/chronology-hyperlinked.svg data/chronology-plot.svg

data/chronology-plot.svg: const/chronology.csv
	bin/plot-chronology.py $^ > $@

data/chronology-hyperlinked.svg: data/chronology-plot.svg bin/linkify_plot.py
	bin/linkify_plot.py < $< > $@

$(CAL): content/e/**/*.md
	bin/build_calendar.py > $@

$(MINISEARCH_INDEX): content/**/*.md
	node bin/build_index.mjs > $@
