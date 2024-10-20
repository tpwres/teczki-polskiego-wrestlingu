export function extractUpcoming() {
    const now = new Date()
    const eventList = document.querySelector('ul.event-list')
    const upcoming = Array.from(eventList.querySelectorAll('li[data-date]'))
          .filter(el => new Date(el.dataset.date) > now)
          .map(el => eventList.removeChild(el));

    return upcoming
}

export function createSection(events, listElement, headerLevel) {
    if (!events.length) return;

    const top = listElement.parentElement
    const firstHeading = listElement.previousElementSibling
    const header = document.createElement(headerLevel)
    header.textContent = 'Upcoming'

    const upcomingList = document.createElement('ul')
    upcomingList.className = 'event-list'
    events.forEach(el => upcomingList.appendChild(el))

    top.insertBefore(header, firstHeading)
    top.insertBefore(upcomingList, firstHeading)
}

export function cleanEmptyYears(headerLevel) {
    document.querySelectorAll(`${headerLevel} + ul.event-list`)
        .forEach(list => {
            if (list.childElementCount > 0) return
            list.previousElementSibling.remove()
            list.remove()
        })
}
