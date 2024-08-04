import MiniSearch from 'minisearch';
import { glob, readFile } from 'fs/promises';
import { parse as tomlParse } from 'toml';
import { stdout } from 'process';

const depolonize = (text, _fieldName) => {
    const chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                   'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'};
    // \p{L} is a unicode category, matching Letters (like [A-Za-z] but with all the alphabets)
    // requires the 'u' flag on regexp
    return text.replace(/\p{L}/gu, m => chars[m] || m).toLowerCase();
}

let index = new MiniSearch({
    fields: ['title', 'text'],
    storeFields: ['title', 'path'],
    processTerm: depolonize
});

// Index everything in content
let all_docs = glob('content/**/*.md', { exclude: (path) => path.endsWith('_index.md') });
for await (const doc_path of all_docs) {
    const body = await readFile(doc_path, { encoding: 'utf-8' });
    // Frontmatter is delimited by three plus signs on a line alone
    const re = /[+]{3}/g;
    // JS's glob regex semantics allow us to exec it twice to find both appearances
    const fm_start = re.exec(body);
    const fm_end = re.exec(body);
    // +4 to eat the endlines
    const frontmatter = tomlParse(body.slice(fm_start.index + 4, fm_end.index));
    const text = body.slice(fm_end.index + 4);

    const slug = doc_path.replace('content/', '/').replace('.md', '');
    const document = {
        // id is mandatory and must be unique
        id: slug.replace(/\//g, '-'),
        // requires processing in results - zola will coerce all non-alpha chars to a dash, e.g. underscores
        path: `${slug}/`,
        title: frontmatter.title,
        text: text
    };

    index.add(document);
}

// Output index to stdout
const json = JSON.stringify(index);
stdout.write(json);
