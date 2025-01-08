class SearchController {
    options = {
        boost: { 'title': 1.6 },
        combineWith: 'AND',
        prefix: true
    }

    minisearch_ready = false
    currentTerm
    index
    focused

    constructor(root, results) {
        this.searchboxTarget = root
        this.queryTarget = root.querySelector('input[type=search]')
        this.resultsTarget = results
        this.itemsTarget = results.querySelector('ul.search-results-items')
        this.itemTemplateTarget = results.querySelector('template')
        this.connect()
    }

    connect() {
        function debounced_search() {
            if (this.debounce_search) clearTimeout(this.debounce_search)
            this.debounce_search = setTimeout(this.search.bind(this), 300)
        }
        this.queryTarget.addEventListener('input', debounced_search.bind(this))
        this.queryTarget.addEventListener('keydown', this.search_keydown.bind(this))
        this.queryTarget.addEventListener('keyup', this.search_keyup.bind(this))
        this.resultsTarget.addEventListener('keydown', this.results_keydown.bind(this))
        document.body.addEventListener('click', this.close.bind(this))
        this.show_search()
    }

    search_keydown(event) {
        switch (event.key) {
        case 'Escape':
            this.close()
            break
        case 'Enter':
            this.open()
            event.preventDefault()
            break
        }
    }

    search_keyup(event) {
        switch (event.key) {
        case 'ArrowDown':
            this.select_first()
            break
        }
    }

    results_keydown(event) {
        switch (event.key) {
        case 'ArrowDown':
            this.next()
            event.preventDefault()
            break
        case 'ArrowUp':
            this.prev()
            event.preventDefault()
            break
        case 'Enter':
            this.open()
            break
        case 'Escape':
            this.close()
            break
        }
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

    spin(enabled) {
        const svg = this.searchboxTarget.querySelector('button > svg')
        const icon = svg.querySelector('use')
        const url = new URL(icon.href.baseVal, document.location.href)
        if (enabled) {
            url.hash = '#loader'
            svg.classList.add('spin')
        } else {
            url.hash = '#search'
            svg.classList.remove('spin')
        }

        icon.href.baseVal = url.toString()


    }

    async search() {
        // Load index on first use
        if (this.index === undefined) {
            await this.load_minisearch()
            await this.load_index()
            this.spin(false)
        }

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
        this.spin(true)

        this.index = MiniSearch.loadJSON(await response.text(), {
            fields: ['title', 'text', 'date'],
            storeFields: ['title', 'path', 'date'],
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
        if (wide) {
            const bounds = this.queryTarget.getBoundingClientRect()
            this.resultsTarget.style.left = `${bounds.left}px`
            this.resultsTarget.style.minWidth = `${bounds.width}px`
        }
        else {
            this.resultsTarget.style.left = '0px'
            this.resultsTarget.style.width = '100%'
        }
    }

    format_result(item, terms) {
        let path = item.path.replace('_', '-')
        const prefix_map = {
            '/e/': ['Event', '#calendar'],
            '/w/': ['Talent', '#user'],
            '/o/': ['Organization', 'globe'],
            '/a/': ['Article', 'book'],
            '/v/': ['Venue', 'map-pin'],
            '/c/': ['Championship', 'award']
        }
        const prefix = path.slice(0, 3)
        const [result_flavor, result_icon] = prefix_map[prefix] || ['Page', '#file-text']

        const node = this.itemTemplateTarget.content.cloneNode(true)
        const link = node.querySelector('a')
        link.href = path
        const svg = node.querySelector('#result-type-icon');
        const icon = svg.querySelector('use')
        const url = new URL(icon.href.baseVal, document.location.href)
        url.hash = result_icon
        link.title = `${result_flavor}: ${item.title}`

        icon.href.baseVal = url.toString()
        const result = node.querySelector('#result')
        if (item.date)
            result.textContent = `${item.title} (${item.date})`
        else
            result.textContent = item.title

        return node
    }
}

const root = document.querySelector('.header-search')
const results = document.querySelector('.search-results')
new SearchController(root, results)

