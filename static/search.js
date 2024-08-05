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

const initSearch = () => {
    const searchInput = document.getElementById("search_input");
    const resultsPane = document.querySelector(".search-results");
    const resultsItems = document.querySelector(".search-results-items");

    searchInput.value = '';
    const options = {
        bool: 'AND',
        fields: {
            title: { boost: 2 },
            body: { boost: 1 }
        }
    };
    const MAX_ITEMS = 16;
    let currentTerm;
    let index;


    const initIndex = async () => {
        if (index === undefined) {
            index = fetch("/search_index.en.json").then(async (response) => {
                return await elasticlunr.Index.load(await response.json());
            });
        }
        let res = await index;
        return res;
    };

    const formatSearchResultItem = (item, terms) => {
        let path;
        if (item.ref.startsWith("http")) {
            const url = new URL(item.ref);
            path = url.pathname;
        } else if (item.ref.startsWith("/")) {
            path = item.ref;
        }
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

        return ` <a class="search-result" href="${item.ref}"><strong>${result_type}:</strong> ${item.doc.title}</a>`;

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
