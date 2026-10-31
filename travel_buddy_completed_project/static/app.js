document.querySelectorAll("form[data-confirm]").forEach(form => {
  form.addEventListener("submit", event => {
    if (!window.confirm(form.dataset.confirm || "Are you sure?")) event.preventDefault();
  });
});
document.querySelectorAll('input[type="date"]').forEach(input => {
  if (input.min && !input.value) input.min = input.min;
});
