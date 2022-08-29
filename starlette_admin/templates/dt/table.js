var table = $("#dt").DataTable({
  dom: "r<'table-responsive't><'card-footer d-flex align-items-center'<'m-0'i><'m-0 ms-auto'p>>",
  paging: true,
  lengthChange: true,
  searching: true,
  info: true,
  colReorder: true,
  searchHighlight: true,
  // responsive: true,
  serverSide: true,
  scrollX: false,
  lengthMenu: lengthMenu,
  pagingType: "full_numbers",
  pageLength: {{model.page_size}},
  select: {
    style: "multi",
    selector: "td:first-child .form-check-input",
    className: "row-selected",
  },
//  buttons: buttons,
  language: {
    info: "Showing <strong>_START_</strong> to <strong>_END_</strong> off <strong>_TOTAL_</strong> records",
    infoEmpty: "No matching records found",
    infoFiltered: "",
    searchBuilder: {
      button: {
        _: '<i class="fa-solid fa-filter"></i> Filter (%d)',
      }
    },
    buttons: {
        pageLength: {
            _: "%d",
            '-1': "All"
        }
    }
  },
  ajax: function (data, callback, settings) {
    //console.log(data);
    order = [];
    data.order.forEach((o) => {
      const { column, dir } = o;
      order.push(`${data.columns[column].data} ${dir}`);
    });
    where = null;
    if (data.searchBuilder && !jQuery.isEmptyObject(data.searchBuilder)) {
      where = extractCriteria(data.searchBuilder);
      //console.log(where);
    }
    query = {
      skip: settings._iDisplayStart,
      limit: settings._iDisplayLength,
      order_by: order,
    };
    if(data.search.value != "")
        query.where = data.search.value
    else if (where) query.where = JSON.stringify(where);
    $.ajax({
      url: "{{ url_for(__name__ ~ ':api', identity=model.identity)  | safe}}",
      type: "get",
      data: query,
      traditional: true,
      dataType: "json",
      success: function (data, status, xhr) {
        total = data.total;
        data = data.items;
        data.forEach((d) => {
          d.DT_RowId = d[pk];
        });
        callback({
          recordsFiltered: total,
          data: data,
        });
      },
    });
  },
  columns: dt_columns,
  order: [],
});
new $.fn.dataTable.Buttons( table, {
    name: 'main',
    buttons: buttons,
   dom: {
        	button: {
          	className: 'btn btn-secondary'
          }
        }
});
new $.fn.dataTable.Buttons( table, {
    name: 'pageLength',
    buttons: [{
       extend: 'pageLength',
       className: 'btn'
    }
   ],
   dom: {
        	button: {
          	className: ''
          }
        }
});


table.buttons('main',null).container().appendTo("#btn_container");
table.buttons('pageLength',null).container().appendTo("#pageLength_container");
//table.buttons('pagination',null).container().appendTo("#page_container");
$("#searchInput").keyup(function () {
  table.search($(this).val()).draw();
});

function onSelectChange() {
  selectedRows = table.rows({ selected: true }).ids().toArray();
  if (table.rows({ selected: true }).count() == 0)
    $("#multi-delete-btn").hide();
  else $("#multi-delete-btn").show();
  $("#multi-delete-btn span").text(table.rows({ selected: true }).count());
}

if (can_delete) {
  table
    .on("select", function (e, dt, type, indexes) {
      onSelectChange();
    })
    .on("deselect", function (e, dt, type, indexes) {
      onSelectChange();
    });

  $("#modal-delete-btn").click(function () {
    $("#modal-delete").modal("hide");
    $("#modal-loading").modal("show");
    query = new URLSearchParams(selectedRows.map((s) => ["pks", s])).toString();
    fetch(
      `{{ url_for(__name__ ~ ':api', identity=model.identity)  | safe}}?${query}`,
      {
        method: "DELETE",
      }
    )
      .then(async (response) => {
        if (response.ok) {
          await new Promise((r) => setTimeout(r, 500));
          $("#modal-loading").modal("hide");
          table.ajax.reload();
          $("#select-all").prop("checked", false);
          $("#multi-delete-btn").hide();
        } else return Promise.reject();
      })
      .catch(async (error) => {
        await new Promise((r) => setTimeout(r, 500));
        $("#modal-loading").modal("hide");
        $("#modal-error").modal("show");
      });
  });

  $("#multi-delete-btn").click(function () {
    $("#modal-delete-body span").text(
      table.rows({ selected: true }).count() + " {{model.label}}"
    );
    $("#modal-delete").modal("show");
  });
}

