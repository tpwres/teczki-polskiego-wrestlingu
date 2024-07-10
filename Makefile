ROSTERS=data/roster_ptw.json data/roster_kpw.json data/roster_mzw.json data/roster_ppw.json data/roster_dfw.json
METADATA=data/all_matches.json data/appearances.json data/career.json
PLOTS=data/chronology-plot.svg data/chronology-hyperlinked.svg

all: $(ROSTERS) $(METADATA)
plot: $(PLOTS)

clean:
	rm -rf $(ROSTERS)
	rm -rf $(METADATA)

data/all_matches.json data/appearances.json: content/e/**/*.md
	bin/build_matches.py

data/career.json: content/e/**/*.md
	bin/build_metadata.py

data/roster_ptw.json data/roster_kpw.json data/roster_ppw.json data/roster_dfw.json: content/e/**/*.md
	bin/build_roster.py

data/chronology-plot.svg: const/chronology.csv
	bin/plot-chronology.sh svg < $^ > $@

data/chronology-hyperlinked.svg: data/chronology-plot.svg bin/linkify_plot.py
	bin/linkify_plot.py < $< > $@
