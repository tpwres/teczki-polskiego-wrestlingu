export function extractEvents(containerSelector, predicate) {
    const extracted = []
    document.querySelectorAll(containerSelector || 'ul.event-list')
        .forEach((eventList) => {
            Array.from(eventList.querySelectorAll('li[data-date]'))
                .filter(el => predicate(el))
                .map(el => eventList.removeChild(el))
                .forEach(el => extracted.push(el))
        })

    return extracted
}

export function createSection(events, title, listElement, headingTag) {
    if (!events.length) return [null, null]

    const top = listElement.parentElement
    const firstHeading = listElement.previousElementSibling
    const header = document.createElement(headingTag)
    header.textContent = title

    const newList = document.createElement('ul')
    newList.className = listElement.className
    events.forEach(el => newList.appendChild(el))

    top.insertBefore(header, firstHeading)
    top.insertBefore(newList, firstHeading)

    return [header, newList]
}

export function cleanEmptyYears(headerLevel, listSelector) {
    document.querySelectorAll(`${headerLevel} + ${listSelector || "ul.event-list"}`)
        .forEach(list => {
            if (list.childElementCount > 0) return
            list.previousElementSibling.remove()
            list.remove()
        })
}

// This does not handle timezones at all.
export const sameDate = (a, b) => ( a.setHours(0, 0, 0, 0) === b.setHours(0, 0, 0, 0) )
