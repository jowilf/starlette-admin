(function () {
    document.querySelectorAll('[data-countup]').forEach(function (el) {
        var opts = { enableScrollSpy: true };
        try {
            var raw = el.getAttribute('data-countup');
            if (raw) Object.assign(opts, JSON.parse(raw));
        } catch (_) {}
        var cu = new window.countUp.CountUp(el, parseFloat(el.textContent), opts);
        if (!cu.error) cu.start();
    });

    document.querySelectorAll('.stat-chart').forEach(function (el) {
        var series = JSON.parse(el.getAttribute('data-series') || '[]');
        var colorToken = el.getAttribute('data-color') || 'primary';
        var resolvedColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--tblr-' + colorToken).trim() || colorToken;
        var defaults = {
            series: series,
            colors: [resolvedColor],
            chart: {
                type: el.getAttribute('data-type') || 'line',
                height: el.getAttribute('data-height') || '40px',
                sparkline: { enabled: true },
                toolbar: { show: false },
                animations: { enabled: true }
            },
            fill: { type: 'solid',  opacity: 0.16},
            stroke: { curve: 'smooth', width: 2 },
            tooltip: {
                fixed: { enabled: false },
                x: { show: false },
                marker: { show: false }
            }
        };
        var extra = JSON.parse(el.getAttribute('data-options') || '{}');
        if (extra.chart) extra.chart = Object.assign({}, defaults.chart, extra.chart);
        new ApexCharts(el, Object.assign({}, defaults, extra)).render();
    });
})();
