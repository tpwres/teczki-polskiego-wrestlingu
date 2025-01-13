import MiniSearch from 'minisearch';
import { readFile } from 'fs/promises';
import { fdir } from 'fdir';
import { parse as tomlParse } from 'toml';
import { stdout } from 'process';

const deaccent = (text, _fieldName) => {
    const chars = {
        // Polish
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z',
        // Czech, Slovak, Hungarian
        'č': 'c', 'ď': 'd', 'ě': 'e', 'é': 'e', 'í': 'i', 'ľ': 'l', 'ň': 'n', 'ř': 'r', 'š': 's', 'ť': 't', 'ú': 'u', 'ž': 'z',
        'Č': 'C', 'Ď': 'D', 'Ě': 'E', 'É': 'E', 'Í': 'I', 'Ľ': 'L', 'Ň': 'N', 'Ř': 'R', 'Š': 'S', 'Ť': 'T', 'Ú': 'U', 'Ž': 'Z',
        // Danish, German, Swedish, Finnish, Norwegian
        'å': 'a', 'ä': 'a', 'ö': 'o', 'ü': 'u',
        'Å': 'A', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
        // French, Spanish
        'à': 'a', 'â': 'a', 'è': 'e', 'ê': 'e', 'ë': 'e', 'ï': 'i', 'ô': 'o', 'û': 'u', 'ü': 'u', 'ñ': 'n',
        'À': 'A', 'Â': 'A', 'È': 'E', 'Ê': 'E', 'Ë': 'E', 'Ï': 'I', 'Ô': 'O', 'Û': 'U', 'Ü': 'U', 'Ñ': 'N'
    };
    // \p{L} is a unicode category, matching Letters (like [A-Za-z] but with all the alphabets)
    // requires the 'u' flag on regexp
    return text.replace(/\p{L}/gu, m => chars[m] || m).toLowerCase();
}

const build_document = async (path) => {
    const body = await readFile(path, { encoding: 'utf-8' });
    // Frontmatter is delimited by three plus signs on a line alone
    const re = /[+]{3}/g;
    // JS's glob regex semantics allow us to exec it twice to find both appearances
    const fm_start = re.exec(body);
    const fm_end = re.exec(body);
    // +4 to eat the endlines
    const frontmatter = tomlParse(body.slice(fm_start.index + 4, fm_end.index));
    const title = frontmatter.title
    const text = body.slice(fm_end.index + 4);

    const slug = path.replace('content/', '/').replace('.md', '');
    let info = undefined;
    const date_match = /^content\/e\/(?:\w+)\/(\d{4}-\d{2}-\d{2})/.exec(path);
    if (date_match)
        info = date_match[1];
    else if (/^content\/w/.test(path)) {
        const aliases = find_aliases(path);
        if (aliases) {
            aliases.delete(title)
            info = [...aliases].join(" | ")
        }
    }

    return {
        // id is mandatory and must be unique
        id: slug.replace(/\//g, '-'),
        // requires processing in results - zola will coerce all non-alpha chars to a dash, e.g. underscores
        path: `${slug}/`,
        title,
        text,
        info
    };
}

let alias_map = JSON.parse(await readFile("data/aliases.json"))
const inverse_alias_map = {};
for (const [name, path] of Object.entries(alias_map)) {
  if (!inverse_alias_map[path]) {
    inverse_alias_map[path] = [];
  }
  inverse_alias_map[path].push(name);
}

const find_aliases = (path) => {
    const aliases = inverse_alias_map[path.replace('content/', '')]
    return aliases ? new Set(aliases) : null
}


let index = new MiniSearch({
    fields: ['title', 'text', 'info'],
    storeFields: ['title', 'path', 'info'],
    processTerm: deaccent
});

// Index everything in content
let all_docs = new fdir().glob('**/*.md').withRelativePaths().crawl('content/').sync();
for await (const doc_path of all_docs) {
    if (doc_path.endsWith('_index.md')) continue;
    const document = await build_document(`content/${doc_path}`);
    index.add(document);
}

// Output index to stdout
const json = JSON.stringify(index);
stdout.write(json);
