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
  const handler = (ev) => {
    let g = ev.target.closest('g')
    let m = g.id.match(/^bar-(.*)/)
    let ann = svg.querySelector(`#ann-${m[1]}`)
    if (ann) {
      if (ev.type == 'mouseover')
        ann.style.visibility = ''
      else if (ev.type == 'mouseout')
        ann.style.visibility = 'hidden'
    }
    let [row, _] = m[1].split('-')
    let ytick = svg.querySelector(`#ytick_${row}`)
      if (ytick) {
          let text = ytick.querySelector('text')
          if (ev.type == 'mouseover')
              text.style.fontWeight = 'bold'
          else if (ev.type == 'mouseout')
              text.style.fontWeight = 'normal'
      }
  }
  svg.querySelectorAll('[id^=bar]').forEach((el) => {
    el.addEventListener('mouseover', debounce(handler, 300))
    el.addEventListener('mouseout', debounce(handler, 300))
  })
})
