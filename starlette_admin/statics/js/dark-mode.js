/*
 * Automatic dark mode.
 *
 * Follows the operating system / browser color-scheme preference and reflects
 * it on the <body> via Tabler's `data-bs-theme="dark"` attribute. The attribute
 * is kept in sync when the user changes their system preference at runtime.
 */
(function () {
    function applyTheme() {
        const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)").matches;
        if (prefersDarkScheme) {
            document.body.setAttribute("data-bs-theme", "dark");
        } else {
            document.body.removeAttribute("data-bs-theme");
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        applyTheme();
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyTheme);
    });
})();
