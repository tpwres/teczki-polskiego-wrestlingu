class ThemeController {
    constructor(root) {
        this.root = document.documentElement
    }
    async setup(root) {
        const toggler = this.root.querySelector('a#darkmodetoggle')
        toggler.addEventListener('click', this.switchTheme.bind(this))
        toggler.addEventListener('dblclick', this.switchAltTheme.bind(this))
        const theme = await this.load()
        if (theme !== null)
            this.apply(theme)
    }

    detect() {
        const theme = this.root.getAttribute('data-theme')
        if (theme !== null)
            return theme
        else if (window.matchMedia('(prefers-color-scheme: dark)').matches)
            return 'dark'
        else if (window.matchMedia('(prefers-color-scheme: light)').matches)
            return 'light'
        // no theme set, no support for color scheme (or no preference): default to light
        return 'light'
    }

    apply(theme) {
        this.root.setAttribute('data-theme', theme)
        this.save(theme)
    }

    async load() {
        if (window.cookieStore) {
            const cookie = await window.cookieStore.get('theme')
            return cookie ? cookie.value : null
        }
        // Fallback to document.cookie
        const name = 'theme='
        return document.cookie
            .split('; ')
            .find(row => row.startsWith('theme='))
            ?.split('=')[1] || null
    }

    async save(theme) {
        const maxAge = 365 * 86400
        if (window.cookieStore) {
            return await window.cookieStore.set({
                name: 'theme',
                value: theme,
                maxAge
            })
        }
        document.cookie = `theme=${theme};max-age=${maxAge};path=/`
    }

    switchTheme() {
        this.apply(this.detect() == 'dark' ? 'light' : 'dark')
    }

    switchAltTheme() {
        this.apply('og')
    }
}

new ThemeController().setup()
