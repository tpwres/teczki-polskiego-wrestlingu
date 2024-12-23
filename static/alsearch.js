import { Alpine } from '/alpine.mjs'

class SearchController {
    static options = {
        boost: { 'title': 1.6 },
        combineWith: 'AND',
        prefix: true
    }
    static prefix_map = {
        '/e/': 'Event',
        '/w/': 'Talent',
        '/o/': 'Organization',
        '/a/': 'Article',
        '/v/': 'Venue',
        '/c/': 'Championship'
    }

    visible = false
    minisearch_ready = false
    query_text
    search_results = []
    focused
    index

    init() {
        this.visible = true
    }

    close() {
        this.search_results = []
        this.query_text = ''
    }

    go() {
        const first = this.$refs.results.querySelector('li:first-of-type')
        first.querySelector('a').click()
    }

    select_first() {
        // Not first-child, because there's a <template> in there
        const first = this.$refs.results.querySelector('li:first-of-type')
        if (first) {
            first.focus()
            this.focused = first
        }
    }

    next() {
        if (!this.focused) return
        const el = this.focused.nextElementSibling
        if (el) {
            el.focus()
            this.focused = el
        }
    }

    prev() {
        if (!this.focused) return
        const el = this.focused.previousElementSibling
        if (el && el.nodeName != 'TEMPLATE') {
            el.focus()
            this.focused = el
        }
    }

    open() {
        if (!this.focused) return
        this.focused.querySelector('a').click()
    }

    async search(term) {
        if (this.index === undefined) {
            await this.load_minisearch()
            await this.load_index()
        }

        this.search_results = this.index.search(term, SearchController.options)
    }

    set query(query) {
        this.query_text = query
        this.search(query)
    }

    get query() { return this.query_text }

    result_type(result) {
        const prefix = result.path.slice(0, 3)
        return SearchController.prefix_map[prefix] || 'Page'
    }

    async load_index() {
        let response = await fetch("/minisearch_index.json")

        this.index = MiniSearch.loadJSON(await response.text(), {
            fields: ['title', 'text'],
            storeFields: ['title', 'category', 'path'],
            processTerm: this.depolonize
        })
    }

    async load_minisearch() {
        if (this.minisearch_ready) return

        const resp = await fetch('/minisearch.js')
        const blob = await resp.blob()
        const url = URL.createObjectURL(blob)
        const script = document.createElement('script')
        script.src = url
        document.body.appendChild(script)
        this.minisearch_ready = true
        try {
            URL.revokeObjectURL(url)
            document.body.removeChild(script)
        } catch (err) {
            console.error(err)
        }
    }

    depolonize(text, _fieldName) {
        const chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
                       'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                       'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
                       'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'};
        return text.replace(/\p{L}/gu, m => chars[m] || m).toLowerCase();
    }
}
document.addEventListener('alpine:init', () => {
    Alpine.data('search', () => new SearchController())
})

window.Alpine = Alpine
Alpine.start()
