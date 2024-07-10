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

