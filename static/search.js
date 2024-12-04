import { Application, Controller } from "/stimulus.js";


class SearchController extends Controller {
    static targets = ["query", "searchbox", "results", "items", "itemTemplate"]
    static options = {
        boost: { 'title': 1.6 },
        combineWith: 'AND',
        prefix: true
    }

    currentTerm
    index
    focused

    connect() {
        this.show_search()
    }

    show_search() {
        this.searchboxTarget.style.display = ''
    }

    close() {
        this.hide_results()
        this.currentTerm = undefined
        this.focused = undefined
    }

    select_first() {
        const first_result = this.itemsTarget.querySelector('li:first-child')
        if (first_result) {
            first_result.focus()
            this.focused = first_result
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
        if (el) {
            el.focus()
            this.focused = el
        }
    }

    open() {
        if (!this.focused) return
        this.focused.querySelector('a').click()
    }


    depolonize(text, _fieldName) {
        const chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
                       'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                       'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
                       'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'};
        return text.replace(/\p{L}/gu, m => chars[m] || m).toLowerCase();
    }

    async search() {
        // Load index on first use
        if (this.index === undefined)
            await this.load_index()

        let term = this.queryTarget.value.trim()
        if (term === this.currentTerm) return

        let search_results = this.index.search(term, this.options)

        if (search_results.length == 0)
            this.hide_results()
        else
            this.show_results(search_results, term)
        this.currentTerm = term
    }

    async load_index() {
        let response = await fetch("/minisearch_index.json")

        this.index = MiniSearch.loadJSON(await response.text(), {
            fields: ['title', 'text'],
            storeFields: ['title', 'category', 'path'],
            processTerm: this.depolonize
        })
    }

    hide_results() {
        this.resultsTarget.style.display = 'none'
    }

    show_results(results, term) {
        this.itemsTarget.replaceChildren()
        for (let i = 0; i < Math.min(results.length, 16); i++) {
            let item = document.createElement('li')
            item.className = 'results-item'
            item.tabIndex = -1
            item.appendChild(this.format_result(results[i]))
            this.itemsTarget.appendChild(item)
        }
        this.resultsTarget.style.display = 'block'
        this.adjust_position()
    }

    adjust_position() {
        const wide = matchMedia('only screen and (min-width: 540px)').matches;
        if (wide)
            this.resultsTarget.style.left = `${this.queryTarget.getBoundingClientRect().left}px`
        else {
            this.resultsTarget.style.left = '0px'
            this.resultsTarget.style.width = '100%'
        }
    }

    format_result(item, terms) {
        let path = item.path.replace('_', '-')
        let result_type = undefined
        const prefix_map = {
            '/e/': 'Event',
            '/w/': 'Talent',
            '/o/': 'Organization',
            '/a/': 'Article',
            '/v/': 'Venue',
            '/c/': 'Championship'
        }
        const prefix = path.slice(0, 3)
        result_type = prefix_map[prefix] || 'Page'

        let node = this.itemTemplateTarget.content.cloneNode(true)
        node.querySelector('a').href = path
        node.querySelector('#result-type').textContent = `${result_type}:`
        node.querySelector('#result').textContent = item.title

        return node
    }
}


if (window.Stimulus === undefined)
    window.Stimulus = Application.start()
Stimulus.register('search', SearchController)
