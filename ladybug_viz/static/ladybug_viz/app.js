/**
 * LadybugDB Viz – Shared front-end utilities.
 * Graph-specific and Cypher-specific JS is inlined in their templates.
 */

"use strict";

// Mark the current nav link as active based on URL
(function initNav() {
  const path = window.location.pathname;
  document.querySelectorAll(".topbar__link").forEach(link => {
    if (link.getAttribute("href") === path) {
      link.classList.add("active");
    }
  });
})();
