import MiniSearch from 'minisearch';
import { readFile } from 'fs/promises';
import { fdir } from 'fdir';
import { parse as tomlParse } from 'toml';
import { stdout } from 'process';

const depolonize = (text, _fieldName) => {
    const chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                   'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'};
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
    const text = body.slice(fm_end.index + 4);

    const slug = path.replace('content/', '/').replace('.md', '');
    return {
        // id is mandatory and must be unique
        id: slug.replace(/\//g, '-'),
        // requires processing in results - zola will coerce all non-alpha chars to a dash, e.g. underscores
        path: `${slug}/`,
        title: frontmatter.title,
        text: text
    };
}

let index = new MiniSearch({
    fields: ['title', 'text'],
    storeFields: ['title', 'path'],
    processTerm: depolonize
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
