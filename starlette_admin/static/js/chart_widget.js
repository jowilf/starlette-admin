(function () {
    document.querySelectorAll('.apex-chart').forEach(function (el) {
        var series = JSON.parse(el.getAttribute('data-series') || '[]');
        var userOpts = JSON.parse(el.getAttribute('data-options') || '{}');
        var opts = Object.assign({}, userOpts);
        opts.chart = Object.assign(
            {
                type: el.getAttribute('data-type') || 'line',
                height: parseInt(el.getAttribute('data-height') || '300', 10)
            },
            userOpts.chart || {}
        );
        opts.series = series;
        new ApexCharts(el, opts).render();
    });
})();
