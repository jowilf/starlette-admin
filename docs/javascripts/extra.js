// Open external links in a new tab.
document.addEventListener("DOMContentLoaded", () => {
  const host = window.location.hostname;
  document.querySelectorAll(".md-content a[href]").forEach((link) => {
    if (link.hostname && link.hostname !== host) {
      link.target = "_blank";
      link.rel = "noopener";
    }
  });
});

// Landing page scroll reveal: fade sections up as they enter the viewport.
document.addEventListener("DOMContentLoaded", () => {
  if (!document.querySelector(".home-hero")) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const targets = document.querySelectorAll(
    ".home-card, .home-spot-copy, .home-spot-media, .home-section-title, .home-lede, .home-code-head ~ .tabbed-set, .home-foot, .home-backend, .home-plugin-panel, .home-cookie"
  );
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("home-reveal-in");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );
  targets.forEach((el) => {
    el.classList.add("home-reveal");
    observer.observe(el);
  });
});
