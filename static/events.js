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

export function matchDateOrRange(elem, now) {
    now.setHours(0, 0, 0, 0)

    const dates = elem.querySelectorAll('.t time')
    if (dates.length == 0) {
        let date = elem.dataset.date
        const then = new Date(date)
        then.setHours(0, 0, 0, 0)
        return now.getTime() == then.getTime()
    }
    const [time_from, time_until] = [...dates]
    const from = new Date(time_from.dateTime).setHours(0, 0, 0, 0)
    const until = new Date(time_until.dateTime).setHours(0, 0, 0, 0)
    return (from <= now) && (now <= until)
}
