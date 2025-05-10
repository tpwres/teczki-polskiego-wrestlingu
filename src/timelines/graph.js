document.addEventListener('DOMContentLoaded', () => {
  const svg = document.querySelector('.svg-embed svg')
  const hideTimeouts = new Map()
  const HIDE_DELAY = 150 // Time in ms before hiding annotations

  // Show annotation with given ID
  const showAnnotation = (id) => {
    const ann = svg.querySelector(`#ann-${id}`)
    if (!ann) return

    // Clear any pending hide timeout
    if (hideTimeouts.has(id)) {
      clearTimeout(hideTimeouts.get(id))
      hideTimeouts.delete(id)
    }

    ann.style.visibility = ''

    // Add hover listeners to annotation (once)
    if (!ann.dataset.hoverable) {
      ann.dataset.hoverable = 'true'

      ann.addEventListener('mouseenter', () => {
        // Cancel any pending hide operation
        if (hideTimeouts.has(id)) {
          clearTimeout(hideTimeouts.get(id))
          hideTimeouts.delete(id)
        }
      })

      ann.addEventListener('mouseleave', () => {
        // Set timeout to hide annotation
        const timeoutId = setTimeout(() => {
          ann.style.visibility = 'hidden'
          hideTimeouts.delete(id)
        }, HIDE_DELAY)

        hideTimeouts.set(id, timeoutId)
      })
    }
  }

  // Handle hover on stripe elements
  const handleStripeHover = (event) => {
    const stripe = event.currentTarget
    const id = stripe.id.replace('stripe-', '')

    if (event.type === 'mouseover') {
      showAnnotation(id)
      const barnum = id.split('-')[0]
      const bgbar = svg.querySelector(`g[id=bg-${barnum}] path`)
      hoverBg(bgbar)
    } else {
      // Set timeout to hide annotation
      const timeoutId = setTimeout(() => {
        const ann = svg.querySelector(`#ann-${id}`)
        if (ann) ann.style.visibility = 'hidden'
        hideTimeouts.delete(id)
      }, HIDE_DELAY)

      hideTimeouts.set(id, timeoutId)
    }
  }

  // Set up hover listeners for stripes
  svg.querySelectorAll('[id^=stripe-]').forEach(stripe => {
    stripe.addEventListener('mouseover', handleStripeHover)
    stripe.addEventListener('mouseout', handleStripeHover)
  })

  // Background hover effect (unchanged)
  let lastBg = undefined
  const hoverBg = (el) => {
    el.style.fill = 'var(--accent-bg)'
    if (lastBg && lastBg !== el)
      lastBg.style.fill = 'var(--bg)'
    lastBg = el
  }
  svg.querySelectorAll('g[id^=bg] path').forEach(path => {
    path.addEventListener('mouseover', (ev) => hoverBg(ev.target))
  })
})
