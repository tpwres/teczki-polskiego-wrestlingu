document.addEventListener('DOMContentLoaded', (e) => {
  let svg = document.querySelector('.svg-embed svg')
  svg.querySelectorAll('[id^=ann]').forEach((el) => el.style.visibility = 'hidden')
  const debounce = (callback, wait) => {
    let timeoutId = null;
    return (...args) => {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        callback(...args);
      }, wait);
    };
  }
  const barHover = (ev) => {
    let g = ev.target.closest('g')
    let m = g.id.match(/^bar-(.*)/)
    let ann = svg.querySelector(`#ann-${m[1]}`)
    if (ann) {
      if (ev.type == 'mouseover')
        ann.style.visibility = ''
      else if (ev.type == 'mouseout')
        ann.style.visibility = 'hidden'
    }
  }
  svg.querySelectorAll('[id^=bar]').forEach((el) => {
    el.addEventListener('mouseover', debounce(barHover, 100))
    el.addEventListener('mouseout', debounce(barHover, 100))
  })

  let lastBg = undefined;
  const hoverBg = (ev) => {
    const path = ev.target
    path.style.fill = 'var(--accent-bg)'
    if (lastBg && lastBg != ev.target)
      lastBg.style.fill = 'var(--bg)'
    lastBg = ev.target
  }
  svg.querySelectorAll('g[id^=bg] path ').forEach((el) => {
    el.addEventListener('mouseover', hoverBg)
  })
})
