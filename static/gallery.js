class LightboxController {
    paginator
    maximised

    constructor(dialog) {
        const q = (sel) => dialog.querySelector(sel)
        this.dialogTarget = dialog
        this.closeTarget = q('button.closebtn')
        this.prevTarget = q('button.prev')
        this.nextTarget = q('button.next')
        this.maximizeTarget = q('button.maximize')
        this.minimizeTarget = q('button.minimize')
        this.containerTarget = q('div.img-container')
        this.imgTarget = q('figure img')
        this.captionTarget = q('figcaption')
        this.descTarget = q('figcaption p')
        this.attributionTarget = q('figcaption small')
        this.connect()
    }

    connect() {
        // TODO: Attach events
        this.dialogTarget.addEventListener('keydown', this.keyevent.bind(this))
        this.maximizeTarget.addEventListener('click', this.toggle_maximize.bind(this))
        this.minimizeTarget.addEventListener('click', this.toggle_maximize.bind(this))
        this.prevTarget.addEventListener('click', this.prev.bind(this))
        this.nextTarget.addEventListener('click', this.next.bind(this))
        this.imgTarget.addEventListener('load', this.adjust.bind(this))
    }

    keyevent(event) {
        switch (event.key) {
        case 'ArrowLeft':
            this.prev()
            break;
        case 'ArrowRight':
            this.next()
            break
        }
    }
    next() {
        if (!this.nextFigure) return

        this.populate(this.nextFigure)
    }

    prev() {
        if (!this.prevFigure) return

        this.populate(this.prevFigure)
    }

    toggle_maximize() {
        if (this.maximised) {
            this.reset_zoom()
            this.zoom_buttons({ maximize: true, minimize: false})
        } else {
            // this.imgTarget.style.objectFit = 'none'
            this.imgTarget.style.removeProperty('max-height')
            this.imgTarget.style.removeProperty('height')
            this.imgTarget.style.setProperty('max-width', 'unset', 'important')
            this.imgTarget.style.setProperty('height', 'unset', 'important')
            this.zoom_buttons({ maximize: false, minimize: true})
            this.containerTarget.classList.add('maximised')
            this.captionTarget.style.visibility = 'collapse'
            this.maximised = true
        }
    }

    reset_zoom() {
        const img = this.imgTarget
        img.style.height = '100%'
        img.style.removeProperty('zoom')
        img.style.removeProperty('max-width')
        this.maximised = false
    }

    zoom_buttons(options) {
        this.maximizeTarget.style.display = options.maximize ? 'initial' : 'none'
        this.minimizeTarget.style.display = options.minimize ? 'initial' : 'none'
        this.captionTarget.style.visibility = 'initial'
        this.containerTarget.classList.remove('maximised')
    }

    populate(figure) {
        const caption = figure.querySelector('figcaption').innerHTML
        const attribution = figure.querySelector('data.attribution').innerHTML

        this.imgTarget.src = figure.dataset.path
        this.reset_zoom()
        this.zoom_buttons({ maximize: true, minimize: false})
        this.descTarget.innerHTML = caption

        if (attribution)
            this.attributionTarget.innerHTML = 'Source: ' + attribution
        else
            this.attributionTarget.innerText = ''

        const [prevFig, nextFig] = this.paginator(figure)
        this.update_controls(prevFig, nextFig)
    }

    update_controls(prevFig, nextFig) {
        this.prevTarget.style.display = prevFig ? 'initial' : 'none'
        this.prevFigure = prevFig

        this.nextTarget.style.display = nextFig ? 'initial' : 'none'
        this.nextFigure = nextFig
    }

    adjust(event) {
        this.imgTarget.style.maxHeight = '100%'
        // Note: previously used naturalWidth
        this.captionTarget.style.width = `clamp(50vw, ${this.imgTarget.width}px, 76vw)`
    }

    show() {
        this.dialogTarget.showModal()
    }
}

class GalleryController {
    constructor(gallery_list, lightbox) {
        this.root = gallery_list
        this.lightbox = lightbox
        this.connect(gallery_list)
    }

    connect(root) {
        this.lightbox.paginator = this.find_sibling_figures
        root.querySelectorAll('figure > a.tn').forEach((el) => {
            el.addEventListener('click', this.open.bind(this))
        })
    }

    open(event) {
        const figure = event.currentTarget.closest('figure')
        const [prevFig, nextFig] = this.find_sibling_figures(figure)

        this.lightbox.populate(figure)
        this.lightbox.show()
        event.preventDefault()
    }

    find_sibling_figures(figure) {
        // Find next and previous <li> elements and figures inside them
        const nextItem = figure.parentElement.nextElementSibling
        const nextFig = nextItem ? nextItem.querySelector('figure') : null
        const prevItem = figure.parentElement.previousElementSibling
        const prevFig = prevItem ? prevItem.querySelector('figure') : null
        return [prevFig, nextFig]
    }

    collapse_main() {
        if (!this.root.classList.contains('main-gallery')) return
        const when = this.root.dataset.collapseGallery
        if (!when) return

        const thumbs = this.root.querySelectorAll('li')
        const total_photo_count = thumbs.length
        if (when == 'auto' && total_photo_count < 12) return

        Array.from(thumbs).slice(6).forEach((el) => el.style.display = 'none')

        const keep_visible = 6
        const hidden_text = this.pluralize('photos hidden', total_photo_count - keep_visible)
        const display_more = this.display_more_link(hidden_text)
        const el = document.createElement('li')
        el.classList.add('expand-gallery')
        el.appendChild(display_more)
        display_more.addEventListener('click', () => {
            Array.from(thumbs).slice(6).forEach((el) => el.style.display = 'initial')
            el.remove()
        })
        this.root.appendChild(el)
    }

    display_more_link(text) {
        const link = document.createElement('a')
        const span = document.createElement('span')
        span.textContent = `Expand gallery (${text})`
        const tail_icon = this.create_icon('chevron-down')
        link.append(head_icon, span, tail_icon)
        return link
    }

    create_icon(symbol) {
        const svg_ns = "http://www.w3.org/2000/svg"
        const xlink_ns = "http://www.w3.org/1999/xlink"
        const icon = document.createElementNS(svg_ns, 'svg')
        icon.classList.add('feather', 'feather-nav')
        const sprite = document.createElementNS(svg_ns, 'use')
        sprite.setAttributeNS(xlink_ns, 'href', `${SPRITE_URL}#${symbol}`)
        icon.append(sprite)
        return icon
    }

    pluralize(term, n) {
        const rules = JSON.parse(document.querySelector('#pluralization-rules').textContent)
        const matching_rule = rules[term]
        if (!matching_rule)
            return `${n} ${term}`
        switch (n) {
        case 1:
            return matching_rule.one.replace('$n', n)
        default:
            return matching_rule.other.replace('$n', n)
        }
    }
}

const dialog = document.querySelector('dialog#lb')
const lightbox = new LightboxController(dialog)
// TODO: more than one gallery, normal on talent pages
document.querySelectorAll('ul.gallery').forEach((gal) => {
    const gc = new GalleryController(gal, lightbox)
    gc.collapse_main()
})
