# PPW Wiki Converter

This is a project to restore the lost PPW-Fandom wiki into a usable state. The project contains only the code and templates, and the wiki export required to use it remains separate.

The intended way to use this is to convert the export into static pages, using a template similar to Mediawiki/Wikipedia's, and publish it.

The project is based on Zola, a static site generator.

## Usage

1. Install [zola](https://getzola.org) and [pipenv](https://pipenv.pypa.io/en/latest/)
2. Run `pipenv`, then `pipenv install`. If it complains about Python version, you may need to run it as `pipenv --python 3.x.y`, specifying whatever version you want to run it on.
3. Copy the export file (`plppwofficial_pages_full.xml`) into the project directory
4. Run the converter: `pipenv run python load.py`. This will produce a set of files under pages/content
5. `cd pages && zola serve`. This will run a local http server on some port (typically 1111). Open `http://localhost:1111` to view the content.

To produce a set of html files to upload, run `zola build` in the `pages` directory instead. This creates or updates the `pages/public` folder, which can be used for publishing.

## Architecture

[Pandoc](https://pandoc.org/) can read basic mediawiki markup. It does 90% of the job required to convert and publish this site.
The export format is internal to MediaWiki, and there are some tools that parse it, like Python-MWXML which we don't use. Internally, it's a fairly straightforward xml tree:

```
root
|-- <page>
    |-- <title>
    |-- <revision>
```

Revisions are ordered chronologically, the last one is newest. We extract all articles by looking at all pages in the export, discarding pages which start with certain prefixes (see `ignore_prefixes` in `load.py`). For the remaining pages, the title is used as filename to output.
Pandoc can output various formats, including HTML and Markdown. For this project, Markdown was chosen, so it's what gets written to the output files.

### AST walking

Pandoc loads any markup it supports into an AST. In order to generate useful links, the most important part of any wiki, the loader needs to transform the AST.
The toplevel object is a list of _blocks_, each of which is roughly equivalent to a HTML element or entity. Most blocks are passed through unmodified. However, blocks that themselves are containers of other blocks are visited recursively. Once a link is reached, it is rewritten: from a wiki page name `[[Welcome Page]]` to a lowercase slug `welcome-page` fitting the conventions used by Zola.

See the `rewrite_ast` function for details.


### Zola

Zola is used as a static site builder, which takes a set of Markdown files and emits or serves html. The template used `"templates/wiki_base.html"` is adapted from [html5-templates.com](https://html5-templates.com/preview/wikipedia.html).


## Alternative: Running this inside mediawiki

1. Pull the official mediawiki image `podman pull docker.io/mediawiki`
2. Run it, with a volume to store the html root: `podman run -v some_dir:/var/www/html mediawiki`
3. Go to the root page and complete installation. Choose sqlite. To find the ip address, use podman inspect: `podman inspect <containerid> | jq '.[0].NetworkSettings.IpADdress'`
4. The config will download a `LocalSettings.php` file. Copy it to your root volume.
5. Shell into the instance: `podman exec -it <containerid> /bin/bash`. Go to `/usr/local/etc/php`, copy or link `php.ini-development` into `php.ini` and edit it.
6. Set `memory_limit=1G` `post_max_size=200M` `upload_max_filesize=100M`
7. Enable Scribunto: edit `LocalSettings.php` back in the html root, and add
   ```
    wfLoadExtension( 'Scribunto' );
    $wgScribuntoDefaultEngine = 'luastandalone'; 
   ```
8. Reload apache: `/etc/init.d/apache2 reload`
9. Login as root, open `Special:Import`
10. Proceed with importing the file. You need some interwiki prefix, otherwise leave everything else default.
