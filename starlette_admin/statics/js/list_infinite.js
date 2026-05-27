$(function () {
  moment.locale(model.locale);
  $.fn.DataTable.DateTime.defaults.locale = model.locale;

  var selectedRows = [];
  var dt_fields = [];
  var dt_columns = [];

  // Build columns same as list.js
  (function () {
    let fringe = structuredClone(model.fields);
    while (fringe.length > 0) {
      let field = fringe.shift(0);
      if (field.type === "CollectionField")
        fringe = field.fields
          .map((f) => {
            f.name = field.name + "." + f.name;
            f.label = field.label + "." + f.label;
            return f;
          })
          .concat(fringe);
      else if (field.type === "ListField") {
        if (field.field.type == "CollectionField") {
          dt_columns.push({
            name: field.name,
            data: field.name,
            orderable: field.field.orderable,
            searchBuilderType: field.search_builder_type,
            render: function (data, type, full, meta) {
              return render[field.field.render_function_key](data, type, full, meta, field);
            },
          });
        } else {
          field.field.name = field.name;
          field.field.label = field.label;
          field.field.orderable = field.orderable;
          field.field.search_builder_type = field.search_builder_type;
          field = field.field;
          dt_columns.push({
            name: field.name,
            data: field.name,
            orderable: field.orderable,
            searchBuilderType: field.search_builder_type,
            render: function (data, type, full, meta) {
              return render[field.render_function_key](data, type, full, meta, field);
            },
          });
        }
        dt_fields.push(field);
      } else {
        dt_columns.push({
          name: field.name,
          data: field.name,
          orderable: field.orderable,
          searchBuilderType: field.search_builder_type,
          render: function (data, type, full, meta) {
            return render[field.render_function_key](data, type, full, meta, field);
          },
        });
        dt_fields.push(field);
      }
    }
  })();

  // Build table headers for infinite scroll table
  (function () {
    var $thead = $("#infinite-thead tr");
    dt_columns.forEach(function (col) {
      var field = dt_fields.find((f) => f.name === col.name);
      var label = field ? field.label : col.name;
      var $th = $("<th>").text(label);
      if (col.orderable) {
        $th.css("cursor", "pointer").attr("data-col-name", col.name);
        $th.addClass("sortable-col");
      }
      $thead.append($th);
    });
  })();

  // Also build headers for hidden DT
  (function () {
    var $header = $("#table-header");
    dt_columns.forEach(function (col) {
      var field = dt_fields.find((f) => f.name === col.name);
      var label = field ? field.label : col.name;
      $header.append($("<th>").text(label));
    });
  })();

  // Actions
  var actionManager = new ActionManager(
    model.actionUrl,
    model.rowActionUrl,
    function (query, element) {
      if (element.data("is-row-action") === true)
        query.append("pk", element.closest(".row-actions-container").data("id"));
      else
        selectedRows.forEach((s) => {
          query.append("pks", s);
        });
    },
    function (actionName, element, msg) {
      if (!element.data("is-row-action")) {
        selectedRows = [];
        onSelectChange();
      }
      resetAndReload();
      successAlert(msg);
    },
    function (actionName, element, error) {
      dangerAlert(error);
    }
  );

  // Export buttons - using ExportAll for paginated fetch
  var buttons = [];
  var export_buttons = [];

  // Helper to get current query state for export
  function getExportQueryState() {
    return {
      search: currentSearch || "",
      where: currentWhere,
      orderBy: currentOrder,
    };
  }

  if (model.exportTypes.includes("csv"))
    export_buttons.push({
      text: function (dt) {
        return '<i class="fa-solid fa-file-csv"></i> ' + dt.i18n("buttons.csv");
      },
      action: function () { ExportAll.exportAll("csv", model, getExportQueryState()); },
    });
  if (model.exportTypes.includes("excel"))
    export_buttons.push({
      text: function (dt) {
        return '<i class="fa-solid fa-file-excel"></i> ' + dt.i18n("buttons.excel");
      },
      action: function () { ExportAll.exportAll("excel", model, getExportQueryState()); },
    });
  if (model.exportTypes.includes("pdf"))
    export_buttons.push({
      text: function (dt) {
        return '<i class="fa-solid fa-file-pdf"></i> ' + dt.i18n("buttons.pdf");
      },
      action: function () { ExportAll.exportAll("pdf", model, getExportQueryState()); },
    });
  if (model.exportTypes.includes("print"))
    export_buttons.push({
      text: function (dt) {
        return '<i class="fa-solid fa-print"></i> ' + dt.i18n("buttons.print");
      },
      action: function () { ExportAll.exportAll("print", model, getExportQueryState()); },
    });
  if (export_buttons.length > 0)
    buttons.push({
      extend: "collection",
      text: function (dt) {
        return '<i class="fa-solid fa-file-export"></i> ' + dt.i18n("starlette-admin.buttons.export");
      },
      className: "",
      buttons: export_buttons,
    });

  // SearchBuilder conditions (same as list.js)
  var noInputCondition = function (cn) {
    return {
      conditionName: function (t, i) { return t.i18n(cn); },
      init: function (a) {
        a.s.dt.one("draw.dtsb", function () { a.s.topGroup.trigger("dtsb-redrawLogic"); });
      },
      inputValue: function () {},
      isInputValid: function () { return true; },
    };
  };

  var enumCondition = function (cn) {
    return {
      conditionName: function (t, i) { return t.i18n(cn); },
      init: function (that, fn, preDefined) {
        var column = that.s.dt.column(that.s.dataIdx);
        var indexArray = column.data().toArray();
        var flatArray = indexArray.flatMap((item) =>
          typeof item === "string" ? item.split(",").map((s) => s.trim()) : item
        );
        var choices = [...new Set(flatArray)]
          .filter((e) => e != null && e !== "")
          .sort()
          .map((v) => [v, v]);
        var select = $("<select/>").addClass("form-select");
        select.on("input change", function () {
          fn(that);
        });
        choices.forEach((choice) => {
          select.append($("<option>", { text: choice[1], value: choice[0] }));
        });
        if (preDefined !== null && choices.some((choice) => choice[0] == preDefined[0])) {
          select.val(preDefined[0]);
        }
        return select;
      },
      inputValue: function (el, that) { return [$(el[0]).val()]; },
      isInputValid: function (el, that) { return ($(el[0]).val() ?? "") !== ""; },
    };
  };

  if (model.columnVisibility)
    buttons.push({
      extend: "colvis",
      text: function (dt) {
        return '<i class="fa-solid fa-eye"></i> ' + dt.i18n("buttons.colvis");
      },
    });

  if (model.searchBuilder)
    buttons.push({
      extend: "searchBuilder",
      config: {
        columns: model.searchColumns,
        conditions: {
          bool: {
            false: noInputCondition("starlette-admin.conditions.false"),
            true: noInputCondition("starlette-admin.conditions.true"),
            null: noInputCondition("starlette-admin.conditions.empty"),
            "!null": noInputCondition("starlette-admin.conditions.notEmpty"),
          },
          default: {
            null: noInputCondition("starlette-admin.conditions.empty"),
            "!null": noInputCondition("starlette-admin.conditions.notEmpty"),
          },
          select: {
            "=": enumCondition("searchBuilder.conditions.array.equals"),
            "!=": enumCondition("searchBuilder.conditions.array.not"),
            null: noInputCondition("starlette-admin.conditions.empty"),
            "!null": noInputCondition("starlette-admin.conditions.notEmpty"),
          },
        },
        greyscale: true,
      },
    });

  // SearchBuilder criteria extraction (same as list.js)
  function extractCriteria(c) {
    var d = {};
    if ((c.logic && c.logic == "OR") || c.logic == "AND") {
      d[c.logic.toLowerCase()] = [];
      c.criteria.forEach((v) => { d[c.logic.toLowerCase()].push(extractCriteria(v)); });
    } else {
      if (c.type && c.type.startsWith("moment-")) {
        var searchFormat = dt_fields.find((f) => f.name == c.origData)?.search_format;
        if (!searchFormat) searchFormat = moment.defaultFormat;
        c.value = [];
        if (c.value1) { c.value1 = moment(c.value1).format(searchFormat); c.value.push(c.value1); }
        if (c.value2) { c.value2 = moment(c.value2).format(searchFormat); c.value.push(c.value2); }
      } else if (c.type == "num") {
        c.value = [];
        if (c.value1) { c.value1 = Number(c.value1); c.value.push(c.value1); }
        if (c.value2) { c.value2 = Number(c.value2); c.value.push(c.value2); }
      }
      var cnd = {};
      var c_map = {
        "=": "eq", "!=": "neq", ">": "gt", ">=": "ge", "<": "lt", "<=": "le",
        contains: "contains", starts: "startswith", ends: "endswith",
        "!contains": "not_contains", "!starts": "not_startswith", "!ends": "not_endswith",
        null: "is_null", "!null": "is_not_null", false: "is_false", true: "is_true",
      };
      if (c.condition == "between") { cnd["between"] = c.value; }
      else if (c.condition == "!between") { cnd["not_between"] = c.value; }
      else if (c_map[c.condition]) { cnd[c_map[c.condition]] = c.value1 ?? ""; }
      d[c.origData] = cnd;
    }
    return d;
  }

  // --- Infinite Scroll State ---
  var currentSkip = 0;
  var totalItems = 0;
  var isLoading = false;
  var allLoaded = false;
  var currentSearch = "";
  var currentWhere = null;
  var currentOrder = [];
  var searchBuilderCriteria = null;
  var lastSearchBuilderJSON = "";

  // Sort state
  var sortCol = null;
  var sortDir = "asc";

  // Initialize default sort from model config
  (function () {
    for (var col in model.fieldsDefaultSort) {
      sortCol = col;
      sortDir = model.fieldsDefaultSort[col] === true ? "desc" : "asc";
      break; // use first
    }
  })();

  // Hidden DataTable for SearchBuilder and export buttons.
  // serverSide:true + searching:true are required so that SearchBuilder sends
  // its criteria via the standard DataTables ajax pipeline and fires draw events.
  var hiddenTable = $("#dt").DataTable({
    dom: "r<'d-none't>",
    paging: false,
    searching: true,
    info: false,
    serverSide: true,
    ajax: function (data, callback, settings) {
      // We don't actually load data into this table — it exists only for
      // SearchBuilder UI.  Extract criteria from the ajax request and apply
      // them to the infinite-scroll fetch instead.
      var sbData = data.searchBuilder;
      var sbJSON = sbData && !$.isEmptyObject(sbData) ? JSON.stringify(sbData) : "";
      if (sbJSON !== lastSearchBuilderJSON) {
        lastSearchBuilderJSON = sbJSON;
        if (sbJSON) {
          currentWhere = extractCriteria(sbData);
          searchBuilderCriteria = sbData;
        } else {
          currentWhere = null;
          searchBuilderCriteria = null;
        }
        currentSearch = "";
        saveStateToUrl();
        resetAndReload();
      }
      // Return empty result set so the hidden table stays empty
      callback({ recordsTotal: 0, recordsFiltered: 0, data: [] });
    },
    columns: [
      { data: "DT_RowId", orderable: false, render: render.col_0 },
      { data: "DT_RowId", orderable: false, render: render.col_1 },
      ...dt_columns,
    ],
    language: {
      url: model.dt_i18n_url,
      searchBuilder: {
        delete: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><line x1="4" y1="7" x2="20" y2="7"></line><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path></svg>`,
        left: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-left" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="15 6 9 12 15 18"></polyline></svg>`,
        right: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-right" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="9 6 15 12 9 18"></polyline></svg>`,
      },
    },
    initComplete: function () {

      new $.fn.dataTable.Buttons(hiddenTable, {
        name: "main",
        buttons: buttons,
        dom: { button: { className: "btn btn-secondary" } },
      });
      hiddenTable.buttons("main", null).container().appendTo("#btn_container");
    },
  });

  // --- Fetch items for infinite scroll ---
  function fetchItems(skip, limit, callback) {
    isLoading = true;
    $("#infinite-loading").show();
    var query = { skip: skip, limit: limit, order_by: currentOrder };
    if (currentSearch) query.where = currentSearch;
    else if (currentWhere) query.where = JSON.stringify(currentWhere);
    $.ajax({
      url: model.apiUrl,
      type: "get",
      data: query,
      traditional: true,
      dataType: "json",
      success: function (data) {
        totalItems = data.total;
        callback(data.items);
        isLoading = false;
        $("#infinite-loading").hide();
        updateInfo();
      },
      error: function () {
        isLoading = false;
        $("#infinite-loading").hide();
      },
    });
  }

  function renderRow(item) {
    var pk = item[model.pk];
    var $tr = $("<tr>").attr("data-pk", pk);

    // Checkbox
    var isSelected = selectedRows.indexOf(pk) !== -1;
    var $cb = $('<td><input class="form-check-input row-checkbox" type="checkbox"></td>');
    if (isSelected) {
      $cb.find("input").prop("checked", true);
      $tr.addClass("row-selected");
    }
    $tr.append($cb);

    // Row actions
    var rowActionsHtml = item._meta ? item._meta.rowActions || "" : "";
    $tr.append($('<td>').html('<div class="row-actions-container" data-id="' + pk + '">' + rowActionsHtml + "</div>"));

    // Data columns
    dt_columns.forEach(function (col) {
      var data = item[col.name];
      // Handle nested names (e.g. "category.name")
      if (data === undefined && col.name.indexOf(".") !== -1) {
        var parts = col.name.split(".");
        data = item;
        for (var i = 0; i < parts.length && data != null; i++) {
          data = data[parts[i]];
        }
      }
      var rendered = col.render(data, "display", item, {});
      $tr.append($("<td>").html(rendered));
    });

    return $tr;
  }

  function appendItems(items) {
    var $tbody = $("#infinite-tbody");
    // Show empty message if no items at all
    $("#infinite-empty-message").remove();
    if (items.length === 0 && currentSkip === 0) {
      allLoaded = true;
      var colCount = dt_columns.length + 2;
      $tbody.append(
        '<tr id="infinite-empty-message"><td colspan="' + colCount + '" class="text-center text-muted p-4">' +
        (model.noItemsMessage || "No items found.") +
        '</td></tr>'
      );
      return;
    }
    items.forEach(function (item) {
      item.DT_RowId = item[model.pk];
      $tbody.append(renderRow(item));
    });
    currentSkip += items.length;
    if (currentSkip >= totalItems) {
      allLoaded = true;
    }
    actionManager.initNoConfirmationActions();
    $('[data-toggle="tooltip"]').tooltip();
    // If sentinel is still visible, load more
    if (!allLoaded) {
      setTimeout(checkSentinelVisible, 100);
    }
  }

  function loadNextPage() {
    if (isLoading || allLoaded) return;
    fetchItems(currentSkip, model.pageSize, appendItems);
  }

  function resetAndReload() {
    currentSkip = 0;
    totalItems = 0;
    allLoaded = false;
    $("#infinite-tbody").empty();
    loadNextPage();
  }

  function updateInfo() {
    var loaded = Math.min(currentSkip, totalItems);
    $("#infinite-info").text(
      "Showing " + loaded + " of " + totalItems + " entries"
    );
  }

  // --- Sort handling ---
  function updateSortIndicators() {
    $(".sortable-col").each(function () {
      $(this).find(".sort-icon").remove();
      if ($(this).attr("data-col-name") === sortCol) {
        var icon = sortDir === "asc"
          ? '<i class="sort-icon fa-solid fa-sort-up ms-1"></i>'
          : '<i class="sort-icon fa-solid fa-sort-down ms-1"></i>';
        $(this).append(icon);
      }
    });
  }

  $(".sortable-col").on("click", function () {
    var colName = $(this).attr("data-col-name");
    if (sortCol === colName) {
      sortDir = sortDir === "asc" ? "desc" : "asc";
    } else {
      sortCol = colName;
      sortDir = "asc";
    }
    currentOrder = [sortCol + " " + sortDir];
    updateSortIndicators();
    saveStateToUrl();
    resetAndReload();
  });

  // --- Search ---
  var searchTimeout = null;
  $("#searchInput").on("keyup", function () {
    var val = $(this).val();
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () {
      currentSearch = val;
      currentWhere = null;
      saveStateToUrl();
      resetAndReload();
    }, 300);
  });



  // --- Intersection Observer for infinite loading ---
  var sentinel = document.getElementById("scroll-sentinel");

  function checkSentinelVisible() {
    if (isLoading || allLoaded) return;
    var rect = sentinel.getBoundingClientRect();
    var windowHeight = window.innerHeight || document.documentElement.clientHeight;
    if (rect.top <= windowHeight + 400) {
      loadNextPage();
    }
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && !isLoading && !allLoaded) {
          loadNextPage();
        }
      });
    },
    { rootMargin: "400px" }
  );
  observer.observe(sentinel);

  // --- Selection ---
  $(document).on("change", ".row-checkbox", function () {
    var $tr = $(this).closest("tr");
    var pk = $tr.attr("data-pk");
    if (this.checked) {
      if (selectedRows.indexOf(pk) === -1) selectedRows.push(pk);
      $tr.addClass("row-selected");
    } else {
      selectedRows = selectedRows.filter((s) => s !== pk);
      $tr.removeClass("row-selected");
    }
    onSelectChange();
  });

  $("#infinite-select-all").on("change", function () {
    var checked = this.checked;
    $("#infinite-tbody .row-checkbox").each(function () {
      this.checked = checked;
      var $tr = $(this).closest("tr");
      var pk = $tr.attr("data-pk");
      if (checked) {
        if (selectedRows.indexOf(pk) === -1) selectedRows.push(pk);
        $tr.addClass("row-selected");
      } else {
        selectedRows = selectedRows.filter((s) => s !== pk);
        $tr.removeClass("row-selected");
      }
    });
    onSelectChange();
  });

  function onSelectChange() {
    if (selectedRows.length === 0) $("#actions-dropdown").hide();
    else $("#actions-dropdown").show();
    $(".actions-selected-counter").text(selectedRows.length);
  }

  // --- Scroll position persistence ---
  var STORAGE_KEY = "infinite_scroll_" + location.pathname;

  function saveScrollPosition() {
    var pos = window.scrollY || window.pageYOffset;
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ scrollTop: pos, skip: currentSkip }));
  }

  function restoreScrollPosition() {
    var saved = sessionStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {
      var state = JSON.parse(saved);
      if (state.skip && state.skip > model.pageSize) {
        // Load items in chunks of pageSize until we reach the saved skip
        var targetSkip = state.skip;
        function loadChunk() {
          if (currentSkip >= targetSkip || allLoaded) {
            setTimeout(function () {
              window.scrollTo(0, state.scrollTop || 0);
            }, 50);
            return;
          }
          fetchItems(currentSkip, model.pageSize, function (items) {
            appendItems(items);
            loadChunk();
          });
        }
        loadChunk();
        return true;
      } else {
        // Will restore after first load
        setTimeout(function () {
          window.scrollTo(0, state.scrollTop || 0);
        }, 100);
      }
    } catch (e) {}
    return false;
  }

  window.addEventListener("beforeunload", function () {
    // Only preserve scroll if navigating to detail/edit of same model
    // beforeunload doesn't know destination, so we rely on link click handler
  });

  // Save scroll only when clicking links to detail/edit of same identity
  var listBasePath = location.pathname; // e.g. /admin/node/list
  var identityBase = listBasePath.replace(/\/list$/, ""); // e.g. /admin/node
  $(document).on("click", "a[href]", function () {
    var href = $(this).attr("href") || "";
    // Save scroll only if navigating to detail or edit of the same model
    if (href.startsWith(identityBase + "/detail/") || href.startsWith(identityBase + "/edit/")) {
      saveScrollPosition();
    } else {
      // Navigating elsewhere — clear saved scroll
      sessionStorage.removeItem(STORAGE_KEY);
    }
  });

  // --- State in URL ---
  function saveStateToUrl() {
    var params = {};
    if (currentSearch) params.search = currentSearch;
    if (currentOrder.length > 0) {
      params.order = currentOrder.map(function (o) {
        var parts = o.split(" ");
        return (parts[1] === "desc" ? "-" : "") + parts[0];
      });
    }
    if (searchBuilderCriteria && !$.isEmptyObject(searchBuilderCriteria)) {
      params.searchBuilder = JSON.stringify(searchBuilderCriteria);
    }
    var query = Qs.stringify(params, { encode: false, indices: false });
    history.replaceState(null, "", location.pathname + (query ? "?" + query : ""));
  }

  function loadStateFromUrl() {
    var params = Qs.parse(location.search, { ignoreQueryPrefix: true });
    if (params.search) {
      currentSearch = params.search;
      $("#searchInput").val(params.search);
    }
    if (params.order) {
      if (typeof params.order === "string") params.order = [params.order];
      currentOrder = params.order.map(function (o) {
        var isDesc = o.startsWith("-");
        var colName = o.startsWith("-") || o.startsWith("+") ? o.substring(1) : o;
        return colName + " " + (isDesc ? "desc" : "asc");
      });
      // Set sort state from first order entry
      if (currentOrder.length > 0) {
        var parts = currentOrder[0].split(" ");
        sortCol = parts[0];
        sortDir = parts[1] || "asc";
      }
    }
    if (params.searchBuilder) {
      try {
        searchBuilderCriteria = JSON.parse(params.searchBuilder);
        currentWhere = extractCriteria(searchBuilderCriteria);
      } catch (e) {}
    }
  }

  // --- Initialize ---
  loadStateFromUrl();
  updateSortIndicators();

  // Try to restore scroll position (loads more items if needed)
  var restored = restoreScrollPosition();
  if (!restored) {
    loadNextPage();
  }

  actionManager.initNoConfirmationActions();
  actionManager.initActionModal();
  $('[data-toggle="tooltip"]').tooltip();
});
