const debounce = (func, wait) => {
    let timeout;

    return function() {
        let context = this;
        let args = arguments;
        clearTimeout(timeout);

        timeout = setTimeout(function() {
            timeout = null;
            func.apply(context, args);
        }, wait);
    };
}

const depolonize = (text, _fieldName) => {
    const chars = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                   'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'};
    return text.replace(/\p{L}/gu, m => chars[m] || m).toLowerCase();
}

const initSearch = () => {
    const searchInput = document.getElementById("search_input");
    const resultsPane = document.querySelector(".search-results");
    const resultsItems = document.querySelector(".search-results-items");

    searchInput.value = '';
    const options = {
        boost: { 'title': 1.6 },
        combineWith: 'AND'
    };
    const MAX_ITEMS = 16;
    let currentTerm;
    let index;


    const initIndex = async () => {
        if (index === undefined) {
            index = fetch("/minisearch_index.json").then(async (response) => {
                let minisearch = MiniSearch.loadJSON(await response.text(), {
                    fields: ['title', 'text'],
                    storeFields: ['title', 'category', 'path'],
                    processTerm: depolonize
                });
                return minisearch;
            });
        }
        let res = await index;
        return res;
    };

    const formatSearchResultItem = (item, terms) => {
        let path = item.path.replace('_', '-');
        let result_type = undefined;
        if (path.startsWith('/e/') && path.length > 3)
            result_type = 'Event';
        else if (path.startsWith('/w/') && path.length > 3)
            result_type = 'Talent';
        else if (path.startsWith('/o/') && path.length > 3)
            result_type = 'Organization';
        else if (path.startsWith('/a/') && path.length > 3)
            result_type = 'Article';
        else if (path.startsWith('/v/') && path.length > 3)
            result_type = 'Venue';
        else if (path.startsWith('/c/') && path.length > 3)
            result_type = 'Championship';
        else
            result_type = 'Page';

        return ` <a class="search-result" href="${path}"><strong>${result_type}:</strong> ${item.title}</a>`;

    };

    const handleListResultKey = (event) => {
        const focused = resultsItems.querySelector('li:focus');
        if (!focused) return false;
        switch (event.key) {
            case 'ArrowDown':
                const next = focused.nextElementSibling;
                if (next) next.focus();
                break;
            case 'ArrowUp':
                const prev = focused.previousElementSibling;
                if (prev) {
                    prev.focus();
                } else {
                    // Back to search input
                    searchInput.focus();
                }
                break;
            case 'Enter':
                focused.querySelector('a').click();
        }
        return false;
    };

    // NOTE: must be keydown not keyup, otherwise page scrolls
    resultsItems.onkeydown = handleListResultKey;

    const handleDownArrow = (event) => {
        const firstResult = resultsItems.querySelector('li:first-child');
        if (firstResult) {
            firstResult.focus();
        }
        event.stopPropagation();
        return false;
    };

    searchInput.addEventListener("keyup", debounce(async (event) => {
        let term = searchInput.value.trim();

        if (event.key == 'ArrowDown' && resultsPane.style.display != 'none')
            return handleDownArrow(event);

        if (term === currentTerm) return;

        resultsPane.style.display = (term === "" ? 'none' : 'block');
        let wide = matchMedia('only screen and (min-width: 540px)').matches;
        if (wide)
            resultsPane.style.left = `${searchInput.getBoundingClientRect().left}px`;
        else {
            resultsPane.style.left = '0px';
            resultsPane.style.width = '100%';
        }
        resultsItems.innerHTML = '';
        currentTerm = term;
        if (term === '') return;

        let search_results = (await initIndex()).search(term, options);

        if (search_results.length === 0) {
            resultsPane.style.display = "none";
            return;
        }
        for (let i = 0; i < Math.min(search_results.length, MAX_ITEMS); i++) {
            var item = document.createElement("li");
            item.className = "results-item";
            item.tabIndex = -1;
            item.innerHTML = formatSearchResultItem(search_results[i], term.split(" "));
            resultsItems.appendChild(item);
        }
    }, 150));

    window.addEventListener('click', (e) => {
        if (resultsPane.style.display == 'block' && !resultsPane.contains(e.target))
            resultsPane.style.display = 'none';
    });
}
document.addEventListener("DOMContentLoaded", initSearch);
