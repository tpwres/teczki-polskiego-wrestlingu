import MiniSearch from 'minisearch';
import { Marked } from 'marked';
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

const build_document = async (path, renderer) => {
    const body = await readFile(path, { encoding: 'utf-8' });
    // Frontmatter is delimited by three plus signs on a line alone
    const re = /[+]{3}/g;
    // JS's glob regex semantics allow us to exec it twice to find both appearances
    const fm_start = re.exec(body);
    const fm_end = re.exec(body);
    // +4 to eat the endlines
    const frontmatter = tomlParse(body.slice(fm_start.index + 4, fm_end.index));
    const text = body.slice(fm_end.index + 4);
    // The text may contain a <!-- more --> HTML comment that delimits the intro text
    const more = text.indexOf('<!-- more -->');
    const intro = more != -1 ? text.slice(0, more) : undefined;

    const slug = path.replace('content/', '/').replace('.md', '');
    return {
        // id is mandatory and must be unique
        id: slug.replace(/\//g, '-'),
        // requires processing in results - zola will coerce all non-alpha chars to a dash, e.g. underscores
        path: `${slug}/`,
        title: frontmatter.title,
        text,
        intro: intro ? renderer.parseInline(intro) : ''
    };
}

const transform_path = (path) => {
    return path.replace(/^@(.*)\/(.*)\.md$/, (match, dir, filename) => {
        return `${dir}/${filename.replace(/[_]/g, '-')}`;
    });
}

const convert_links = (html) => {
    return html.replace(/href="([^"]*)"/g, (match, p1) => {
        if (p1.startsWith('@')) {
            return `href="${transform_path(p1)}"`;
        }
        return match;
    });
}

let index = new MiniSearch({
    fields: ['title', 'text'],
    storeFields: ['title', 'path', 'intro'],
    processTerm: deaccent
});

// Index everything in content
let all_docs = new fdir().glob('**/*.md').withRelativePaths().crawl('content/').sync();
let renderer = new Marked({hooks: { postprocess: convert_links }});
for await (const doc_path of all_docs) {
    if (doc_path.endsWith('_index.md')) continue;
    const document = await build_document(`content/${doc_path}`, renderer);
    index.add(document);
}

// Output index to stdout
const json = JSON.stringify(index);
stdout.write(json);
