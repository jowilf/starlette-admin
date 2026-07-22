(function () {
    // Tab pane ids are re-generated on every render, so they can't be used as
    // a stable sessionStorage key across page loads. The tab's position
    // within the widget is stable instead, so state is keyed on that.
    var bs = window.bootstrap || (window.tabler && window.tabler.bootstrap);

    document.querySelectorAll('[data-tabs-storage-key]').forEach(function (card) {
        var storageKey = card.getAttribute('data-tabs-storage-key');
        var navLinks = card.querySelectorAll('.nav-tabs[role="tablist"] > .nav-item > .nav-link');

        var saved = sessionStorage.getItem(storageKey);
        if (saved !== null && bs) {
            var link = navLinks[parseInt(saved, 10)];
            if (link) bs.Tab.getOrCreateInstance(link).show();
        }

        navLinks.forEach(function (link, index) {
            link.addEventListener('shown.bs.tab', function () {
                sessionStorage.setItem(storageKey, String(index));
            });
        });
    });
})();
