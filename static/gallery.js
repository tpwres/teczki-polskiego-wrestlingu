import { Application, Controller } from "/stimulus.js"

class LightboxController extends Controller {
    static targets = ["dialog", "close", "prev", "next", "maximize", "minimize",
                      "container", "img", "caption", "desc", "attribution"]

    paginator
    maximised

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
            this.imgTarget.style.removeProperty("max-height")
            this.imgTarget.style.setProperty('max-width', 'unset', 'important')
            this.zoom_buttons({ maximize: false, minimize: true})
            this.containerTarget.classList.add('maximised')
            this.captionTarget.style.visibility = 'collapse'
            this.maximised = true
        }
    }

    reset_zoom() {
        const img = this.imgTarget
        img.style.maxHeight = '100%'
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

class GalleryController extends Controller {
    static targets = ["figure"]
    static outlets = ["lightbox"]

    connect() {
        this.lightboxOutlet.paginator = this.find_sibling_figures
    }

    open(event) {
        const figure = event.currentTarget.closest('figure')
        const [prevFig, nextFig] = this.find_sibling_figures(figure)

        this.lightboxOutlet.populate(figure)
        this.lightboxOutlet.show()
    }

    find_sibling_figures(figure) {
        // Find next and previous <li> elements and figures inside them
        const nextItem = figure.parentElement.nextElementSibling
        const nextFig = nextItem ? nextItem.querySelector('figure') : null
        const prevItem = figure.parentElement.previousElementSibling
        const prevFig = prevItem ? prevItem.querySelector('figure') : null
        return [prevFig, nextFig]
    }

}

if (window.Stimulus === undefined)
    window.Stimulus = Application.start()

Stimulus.register('lightbox', LightboxController)
Stimulus.register('gallery', GalleryController)
