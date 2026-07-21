(function () {
  function highlight(stars, value) {
    stars.forEach(function (star, idx) {
      star.classList.toggle("sa-rating-star-filled", idx < value);
    });
  }

  function currentValue(container) {
    var checked = container.querySelector('input[type="radio"]:checked');
    return checked ? parseInt(checked.value, 10) : 0;
  }

  function initRating(container) {
    if (container.dataset.saInit) return;
    container.dataset.saInit = "1";

    var inputs = Array.prototype.slice.call(
      container.querySelectorAll('input[type="radio"]')
    );
    var stars = Array.prototype.slice.call(
      container.querySelectorAll(".sa-rating-star")
    );

    stars.forEach(function (star, idx) {
      star.addEventListener("mouseenter", function () {
        highlight(stars, idx + 1);
      });
      star.addEventListener("click", function () {
        inputs[idx].checked = true;
        highlight(stars, idx + 1);
      });
    });

    container.addEventListener("mouseleave", function () {
      highlight(stars, currentValue(container));
    });

    highlight(stars, currentValue(container));
  }

  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-rating]").forEach(initRating);
  });
})();
