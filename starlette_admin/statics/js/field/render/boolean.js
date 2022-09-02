export function render(data, type, full, meta, fieldOptions, escape) {
  if (data == null) return null_column();
  if (type != "display") return data === true;
  return data === true
    ? `<span class="text-center text-success"><i class="fa-solid fa-check-circle fa-lg"></i></span>`
    : `<span class="text-center text-danger"><i class="fa-solid fa-times-circle fa-lg"></i></span>`;
}
