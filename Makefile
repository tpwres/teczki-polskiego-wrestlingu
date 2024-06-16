ROSTERS=data/roster_ptw.json data/roster_kpw.json data/roster_mzw.json data/roster_ppw.json data/roster_dfw.json
METADATA=data/all_matches.json data/appearances.json data/career.json

all: $(ROSTERS) $(METADATA)

clean:
	rm -rf $(ROSTERS)
	rm -rf $(METADATA)

data/all_matches.json data/appearances.json: content/e/**/*.md
	bin/build_matches.py

data/career.json: content/e/**/*.md
	bin/build_metadata.py

data/roster_ptw.json data/roster_kpw.json data/roster_ppw.json data/roster_dfw.json: content/e/**/*.md
	bin/build_roster.py
