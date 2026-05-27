/**
 * export_all.js - Paginated export utility for starlette-admin.
 * Fetches ALL items from the API in pages, shows a progress bar,
 * then generates CSV/Excel/PDF/Print directly without DataTables.
 */
var ExportAll = (function ($) {
  "use strict";

  var PAGE_SIZE = 500;

  function getExportFields(model) {
    var exportFieldNames = model.exportColumns.map(function (col) {
      return col.split(":")[0];
    });
    var fields = [];
    var fringe = (model.fields || []).slice();
    while (fringe.length > 0) {
      var f = fringe.shift();
      if (f.type === "CollectionField") {
        (f.fields || []).forEach(function (child) {
          fringe.push({ name: f.name + "." + child.name, label: f.label + "." + child.label, type: child.type, fields: child.fields });
        });
      } else {
        fields.push(f);
      }
    }
    var result = [];
    exportFieldNames.forEach(function (name) {
      var found = fields.find(function (ff) { return ff.name === name; });
      result.push({ name: name, label: found ? found.label : name });
    });
    return result;
  }

  function getCellValue(item, fieldName) {
    var val = item;
    var parts = fieldName.split(".");
    for (var i = 0; i < parts.length && val != null; i++) {
      val = val[parts[i]];
    }
    if (val == null) return "";
    if (typeof val === "object") {
      if (Array.isArray(val)) return val.join(", ");
      return JSON.stringify(val);
    }
    return String(val);
  }

  function showProgress() {
    var cancelled = false;
    var $overlay = $(
      '<div class="export-progress-overlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:99999;display:flex;align-items:center;justify-content:center;">' +
        '<div class="export-progress-dialog" style="border-radius:8px;padding:24px 32px;min-width:320px;max-width:400px;box-shadow:0 4px 24px rgba(0,0,0,0.3);">' +
          '<div class="export-progress-title" style="margin-bottom:8px;font-weight:600;">Exporting data...</div>' +
          '<div class="progress" style="height:20px;">' +
            '<div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width:0%;">0%</div>' +
          '</div>' +
          '<div class="export-progress-text" style="margin-top:8px;font-size:0.85em;">Fetching page 1...</div>' +
          '<div style="margin-top:16px;text-align:right;">' +
            '<button class="btn btn-secondary export-cancel-btn" type="button">Cancel</button>' +
          '</div>' +
        '</div>' +
      '</div>'
    );
    // Apply theme-aware styles
    var isDark = document.body.getAttribute("data-bs-theme") === "dark" ||
                document.documentElement.getAttribute("data-bs-theme") === "dark" ||
                window.matchMedia("(prefers-color-scheme: dark)").matches && !document.body.getAttribute("data-bs-theme");
    var $dialog = $overlay.find(".export-progress-dialog");
    if (isDark) {
      $dialog.css({ background: "#1e293b", color: "#e2e8f0" });
      $overlay.find(".export-progress-text").css("color", "#94a3b8");
    } else {
      $dialog.css({ background: "#fff", color: "#1e293b" });
      $overlay.find(".export-progress-text").css("color", "#666");
    }
    $("body").append($overlay);
    // Cancel button handler
    var cancelCallback = null;
    $overlay.find(".export-cancel-btn").on("click", function () {
      cancelled = true;
      if (cancelCallback) cancelCallback();
    });
    return {
      update: function (pct, text) {
        var p = Math.min(100, Math.round(pct));
        $overlay.find(".progress-bar").css("width", p + "%").text(p + "%");
        if (text) $overlay.find(".export-progress-text").text(text);
      },
      close: function () { $overlay.remove(); },
      isCancelled: function () { return cancelled; },
      onCancel: function (fn) { cancelCallback = fn; },
    };
  }

  function fetchAllPages(apiUrl, baseQuery, onProgress, onDone, onError, cancelCtrl) {
    var allItems = [];
    var total = null;
    var currentXhr = null;

    if (cancelCtrl) cancelCtrl.abort = function () {
      if (currentXhr) currentXhr.abort();
    };

    function fetchPage(skip) {
      if (cancelCtrl && cancelCtrl.isCancelled()) { onError("__cancelled__"); return; }
      var query = $.extend({}, baseQuery, { skip: skip, limit: PAGE_SIZE });
      currentXhr = $.ajax({
        url: apiUrl, type: "get", data: query, traditional: true, dataType: "json",
        success: function (resp) {
          currentXhr = null;
          if (cancelCtrl && cancelCtrl.isCancelled()) { onError("__cancelled__"); return; }
          total = resp.total;
          allItems = allItems.concat(resp.items);
          onProgress(allItems.length, total);
          if (allItems.length >= total) { onDone(allItems); }
          else { fetchPage(allItems.length); }
        },
        error: function (xhr, status, err) {
          currentXhr = null;
          if (status === "abort") { onError("__cancelled__"); return; }
          onError("Failed to fetch data: " + (err || status));
        },
      });
    }
    fetchPage(0);
  }

  function downloadCSV(headers, rows, filename) {
    var BOM = "\uFEFF";
    var csv = headers.map(escapeCSV).join(",") + "\n";
    rows.forEach(function (row) { csv += row.map(escapeCSV).join(",") + "\n"; });
    var blob = new Blob([BOM + csv], { type: "text/csv;charset=utf-8;" });
    triggerSave(blob, filename);
  }

  function escapeCSV(val) {
    var s = String(val == null ? "" : val);
    if (s.indexOf('"') !== -1 || s.indexOf(",") !== -1 || s.indexOf("\n") !== -1) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }

  function downloadExcel(headers, rows, filename) {
    var JSZipLib = window.JSZip;
    if (!JSZipLib) { alert("Excel export not available (JSZip not loaded)."); return; }
    var zip = new JSZipLib();
    var sheetData = '<row r="1">';
    for (var h = 0; h < headers.length; h++) {
      sheetData += '<c r="' + colLetter(h) + '1" t="inlineStr" s="2"><is><t>' + escapeXml(headers[h]) + "</t></is></c>";
    }
    sheetData += "</row>";
    for (var r = 0; r < rows.length; r++) {
      var rn = r + 2;
      sheetData += '<row r="' + rn + '">';
      for (var c = 0; c < rows[r].length; c++) {
        var v = rows[r][c];
        if (v !== "" && !isNaN(v) && v !== null && String(v).trim() !== "") {
          sheetData += '<c r="' + colLetter(c) + rn + '" t="n"><v>' + v + "</v></c>";
        } else {
          sheetData += '<c r="' + colLetter(c) + rn + '" t="inlineStr"><is><t xml:space="preserve">' + escapeXml(v) + "</t></is></c>";
        }
      }
      sheetData += "</row>";
    }
    var sheetXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheetData>' + sheetData + "</sheetData></worksheet>";
    var workbookXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>';
    var stylesXml = '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><sz val="11"/><name val="Calibri"/><b/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" applyFont="1"/></cellXfs></styleSheet>';
    var relsXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>';
    var wbRelsXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>';
    var ctXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>';
    zip.file("[Content_Types].xml", ctXml);
    zip.folder("_rels").file(".rels", relsXml);
    var xl = zip.folder("xl");
    xl.file("workbook.xml", workbookXml);
    xl.file("styles.xml", stylesXml);
    xl.folder("_rels").file("workbook.xml.rels", wbRelsXml);
    xl.folder("worksheets").file("sheet1.xml", sheetXml);
    if (zip.generateAsync) {
      zip.generateAsync({ type: "blob", mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }).then(function (blob) { triggerSave(blob, filename); });
    } else {
      triggerSave(zip.generate({ type: "blob", mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }), filename);
    }
  }

  function colLetter(idx) {
    var s = "", n = idx;
    while (n >= 0) { s = String.fromCharCode((n % 26) + 65) + s; n = Math.floor(n / 26) - 1; }
    return s;
  }

  function escapeXml(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
  }

  function downloadPDF(headers, rows, filename) {
    if (!window.pdfMake) { alert("PDF export not available (pdfMake not loaded)."); return; }
    var body = [];
    body.push(headers.map(function (h) { return { text: h, style: "tableHeader" }; }));
    rows.forEach(function (row, idx) {
      body.push(row.map(function (cell) { return { text: String(cell), style: idx % 2 ? "tableBodyEven" : "tableBodyOdd" }; }));
    });
    var docDef = {
      pageSize: "A4",
      pageOrientation: headers.length > 6 ? "landscape" : "portrait",
      content: [{ table: { headerRows: 1, body: body }, layout: "lightHorizontalLines" }],
      styles: {
        tableHeader: { bold: true, fontSize: 9, color: "white", fillColor: "#2d4154" },
        tableBodyEven: { fontSize: 8 },
        tableBodyOdd: { fontSize: 8, fillColor: "#f3f3f3" },
      },
      defaultStyle: { fontSize: 8 },
    };
    pdfMake.createPdf(docDef).download(filename);
  }

  function printTable(headers, rows) {
    var html = "<html><head><title>Print</title><style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:4px 8px;font-size:12px;text-align:left}th{background:#2d4154;color:#fff}</style></head><body><table><thead><tr>";
    headers.forEach(function (h) { html += "<th>" + escapeHtml(h) + "</th>"; });
    html += "</tr></thead><tbody>";
    rows.forEach(function (row) { html += "<tr>"; row.forEach(function (cell) { html += "<td>" + escapeHtml(cell) + "</td>"; }); html += "</tr>"; });
    html += "</tbody></table></body></html>";
    var win = window.open("", "_blank");
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(function () { win.print(); }, 250);
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function triggerSave(blob, filename) {
    if ($.fn.dataTable && $.fn.dataTable.fileSave) { $.fn.dataTable.fileSave(blob, filename); return; }
    if (window.saveAs) { window.saveAs(blob, filename); return; }
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(function () { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
  }

  function exportAll(type, model, queryState) {
    var progress = showProgress();
    var baseQuery = { order_by: queryState.orderBy || [] };
    if (queryState.search) baseQuery.where = queryState.search;
    else if (queryState.where) baseQuery.where = JSON.stringify(queryState.where);

    var exportFields = getExportFields(model);

    // Cancel control object shared with fetchAllPages
    var cancelCtrl = {
      isCancelled: progress.isCancelled,
      abort: null, // will be set by fetchAllPages
    };

    // Wire up cancel button to abort immediately and close dialog
    progress.onCancel(function () {
      if (cancelCtrl.abort) cancelCtrl.abort();
      progress.close();
    });

    fetchAllPages(
      model.apiUrl, baseQuery,
      function (loaded, total) {
        var pct = total > 0 ? (loaded / total) * 100 : 0;
        progress.update(pct, "Fetched " + loaded + " / " + total + " items (page " + Math.ceil(loaded / PAGE_SIZE) + "/" + Math.ceil(total / PAGE_SIZE) + ")");
      },
      function (allItems) {
        progress.update(100, "Generating file...");
        var headers = exportFields.map(function (f) { return f.label; });
        var rows = allItems.map(function (item) {
          return exportFields.map(function (f) { return getCellValue(item, f.name); });
        });
        var filename = (model.label || "export").replace(/[^a-zA-Z0-9_\-]/g, "_");
        setTimeout(function () {
          try {
            switch (type) {
              case "csv": downloadCSV(headers, rows, filename + ".csv"); break;
              case "excel": downloadExcel(headers, rows, filename + ".xlsx"); break;
              case "pdf": downloadPDF(headers, rows, filename + ".pdf"); break;
              case "print": printTable(headers, rows); break;
            }
          } catch (e) {
            console.error("Export error:", e);
            if (typeof dangerAlert === "function") dangerAlert("Export failed: " + e.message);
          }
          progress.close();
        }, 50);
      },
      function (errMsg) {
        progress.close();
        if (errMsg === "__cancelled__") return; // User cancelled, no error message
        if (typeof dangerAlert === "function") dangerAlert(errMsg);
        else alert(errMsg);
      },
      cancelCtrl
    );
  }

  return { exportAll: exportAll };
})(jQuery);
