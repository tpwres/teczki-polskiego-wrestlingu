import { Application, Controller } from "/stimulus.js"

class LightboxController extends Controller {
    static targets = ["dialog", "close", "prev", "next", "img", "caption", "desc", "attribution"]

    paginator

    next() {
        if (!this.nextFigure) return

        this.populate(this.nextFigure)
    }

    prev() {
        if (!this.prevFigure) return

        this.populate(this.prevFigure)
    }

    populate(figure) {
        const caption = figure.querySelector('figcaption').innerHTML
        const attribution = figure.querySelector('data.attribution').innerHTML

        this.imgTarget.src = figure.dataset.path
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
        // Note: previously used naturalWidth
        this.captionTarget.style.width = `clamp(50vw, ${this.imgTarget.width}px, 80vw)`
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
