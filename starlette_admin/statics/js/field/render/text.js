export function render(data, type, full, meta, fieldOptions, escape) {
  if (data == null) return null_column();
  if (type != "display") return escape(data);
  return `<span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title="${escape(
    data
  )}" style="max-width: 30em;">${escape(data)}</span>`;
}
