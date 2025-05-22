# Theme songs template

In order to properly link to a wrestler's theme songs, use the following template:

```
## In wrestling

* Entrance music:
  - "Title 1" by Artist 1
    {{ org_badge(orgs=['ppw']) }} (20??-20???) <br>
    {{ music(yt='')}}
    {{ music(spot='')}}
    {{ music(apple='')}}
  - "Title 2" by Artist 2
    {{ org_badge(orgs=['mzw', 'low', 'kpw']) }} (20??-present, in tag team with This Guy) <br>
    {{ music(yt='')}}
    {{ music(spot='')}}
    {{ music(apple='')}}
  - "Title 3" by Artist 3
    {{ org_badge(orgs=['ppw']) }} (20??, as Early Gimmick) <br>
    {{ music(yt='')}}
    {{ music(apple='')}}
```

* Place the template in the _In wrestling_ section of the article; in the section is not present, go ahead and add it. It should be placed near the end of the article, after the wrestler's bio but before _Internet presence_ (which in turn comes before _References_).
* Please pay attention to the spaces af the beginning of individual lines. There are two spaces before the line with the title/artist and four spaces before each line beginning with curly brackets.
* Each badge needs to be separately enclosed in apostrophes. Badges and apostrophes are inside square brackets.
* For a single badge, you can use ```org=```. For multiple badges, however, it's always ```orgs=```, and the list elements must be quoted properly: `orgs=['A', 'B', 'C']`.  Otherwise, the links won't render properly, and the preview will be broken.
* Put the date range after the badges. If a song is still in use, mark it as "-present". If there's additional information, e.g. a song is used in tag team only, or it accompanied a wrestler's particular gimmick, put that inside the bracket after the date.
* Make sure to put ```<br>``` after the date range to force a line break. This ensures that the links are displayed in the next line, making for a much cleaner look - especially when the title and/or artist name are on the long side.
* Currently supported services are YouTube, Spotify and Apple Music. Use all three if possible. Omit the given entry if a song is unavailable on that platform.
* Only paste the relevant portions of URLs.
* For YouTube: https://www.youtube.com/watch?v= **YJQz73IPCyI**
* For Spotify: https://open.spotify.com/track/ **6LGDsu52kzsb7p802GsmtH** ?si=b8144a5aec5c4675
* For Apple Music: https://music.apple.com/us/album/new-witch-666-the-rising/ **1476554740?i=1476555600**
* If the song cannot be found on the major platforms, but there is a version online that can be linked to, use the form `{% music(link='https://link.to/song') %}text{% end %}`.
  For example, Zefir and Leon's tune on Bandcamp:
  ```
  {% music(link="https://scandroid.bandcamp.com/track/neo-tokyo-dance-with-the-dead-remix") %}
    Bandcamp
  {% end %}
  ```
