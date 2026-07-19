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
