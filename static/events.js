export function extractUpcoming(selector) {
    const now = new Date(new Date().toDateString())
    const upcoming = []
    document.querySelectorAll(selector || 'ul.event-list').forEach((eventList) => {
        Array.from(eventList.querySelectorAll('li[data-date]'))
            .filter(el => new Date(el.dataset.date) >= now)
            .map(el => eventList.removeChild(el))
            .forEach(el => upcoming.push(el));
    })

    return upcoming
}

export function createSection(events, listElement, headerLevel) {
    if (!events.length) return;

    const top = listElement.parentElement
    const firstHeading = listElement.previousElementSibling
    const header = document.createElement(headerLevel)
    header.textContent = 'Upcoming'

    const upcomingList = document.createElement('ul')
    upcomingList.className = listElement.className
    events.forEach(el => upcomingList.appendChild(el))

    top.insertBefore(header, firstHeading)
    top.insertBefore(upcomingList, firstHeading)
}

export function cleanEmptyYears(headerLevel, listSelector) {
    document.querySelectorAll(`${headerLevel} + ${listSelector || "ul.event-list"}`)
        .forEach(list => {
            if (list.childElementCount > 0) return
            list.previousElementSibling.remove()
            list.remove()
        })
}
