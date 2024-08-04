import MiniSearch from 'minisearch';
import { glob, readFile } from 'fs/promises';
import { parse as tomlParse } from 'toml';
import { stdout } from 'process';

const category_from_path = (path) => {
    const rx = /content\/([aceovw])\/.*\.md/;
    let result = rx.exec(path);
    return result[1];
};

const depolonize = (text, _fieldName) => {
    const chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                   'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'};
    return text.replace(/\p{L}/gu, m => chars[m] || m).toLowerCase();
}

let all_docs = glob('content/**/*.md', { exclude: (path) => path.endsWith('_index.md') });
let index = new MiniSearch({
    fields: ['title', 'text'],
    storeFields: ['title', 'category', 'path'],
    processTerm: depolonize
});

for await (const doc_path of all_docs) {
    const body = await readFile(doc_path, { encoding: 'utf-8' });
    const re = /[+]{3}/g;
    const fm_start = re.exec(body);
    const fm_end = re.exec(body);
    const frontmatter = tomlParse(body.slice(fm_start.index + 4, fm_end.index));
    const text = body.slice(fm_end.index + 4);

    const slug = doc_path.replace('content/', '/').replace('.md', '');
    const document = {
        id: slug.replace(/\//g, '-'),
        path: `${slug}/`,
        title: frontmatter.title,
        category: category_from_path(doc_path),
        text: text
    };

    index.add(document);
}
const json = JSON.stringify(index);
stdout.write(json);
