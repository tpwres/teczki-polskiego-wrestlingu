# Table of contents

Organization pages and talent pages can have a table of contents automatically generated from the header structure. This can be later added to more pages.
To display the table of contents (TOC), set `toclevel` to a value between 1 and 3 in the `[extra]` section of the page's front matter.
If `toclevel` is set to zero or missing, no TOC will be displayed.

## Structure

Given the following example structure:

```markdown
## Pellentesque dapibus
### Suscipit ligula
### Donec posuere augue
#### Etiam vel tortor
##### Sodales tellus ultricies commode
## Suspendisse potenti
```

here's how the generated table of contents will look at different `toclevel` values:

### `toclevel=1`

Only the first level of headers will be listed.

```
1. Pellentesque dapibus
2. Suspendisse potenti
```

### `toclevel=2`

The first and second level of headers will be listed.

```
1. Pellentesque dapibus
  1.1 Suscipit ligula
  1.2 Donec posuere augue
2. Suspendisse potenti
```

### `toclevel=3`

Headers down to the third level will be listed. Note that headers four and five deep will never be listed, this is by design.

```
1. Pellentesque dapibus
  1.1 Suscipit ligula
  1.2 Donec posuere augue
    1.2.1 Etiam vel tortor
2. Suspendisse potenti
```

## Event entry structure

To keep the event entries consistent, follow this structure:

```
## Storyline overview
## Build-up
### Additional details
## Card
### Recap
#### Additional details
## References
```

This is a guideline rather than a strict rule - not every point will be necessary or even possible. The most important ones are Card, Recap and References, and they always should start with `##`; the rest should fall where it makes the most sense.

In the vast majority of cases `toclevel=2` is the best choice for events. There's no need for `toclevel=1` even if the entry has no `###`, and `toclevel=3` might result in overly crowded TOC, depending on the structure (such as would be the case of Ewenement Haze). To get a better idea, see:

- [PTW #5 Gold Rush](https://tpwres.pl/e/ptw/2024-02-03-ptw-5-gold-rush/)
- [PpW Ewenement Haze](https://tpwres.pl/e/ppw/2024-04-20-ppw-ewenement-haze/)
- [PTW #6 Total Blast From The Past](https://tpwres.pl/e/ptw/2024-05-11-ptw-6/)
- [PpW Ledwo Legalne IV](https://tpwres.pl/e/ppw/2024-06-08-ppw-ledwo-legalne-4/)
- [PpW Co Za Noc](https://tpwres.pl/e/ppw/2024-10-26-ppw-co-za-noc/)
- [PpW Chcemy Krwi!](https://tpwres.pl/e/ppw/2024-10-30-ppw-chcemy-krwi/)
- [PpW Ostatnia Prosta](https://tpwres.pl/e/ppw/2025-04-30-ppw-ostatnia-prosta/)
- [PpW Lucha Libre Extravaganza](https://tpwres.pl/e/ppw/2025-05-16-ppw-lucha-libre-extravaganza/)
