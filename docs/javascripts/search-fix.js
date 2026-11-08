/*
 * The search dialog uses a shadow root. The light DOM CSS cannot select its
 * elements. Add a style to the shadow root. The style sets normal letter
 * spacing.
 */
(function () {
  "use strict";

  var STYLE =
    "dialog[open] { --letter-spacing: normal; } dialog[open] input { letter-spacing: normal; }";

  function patch() {
    for (var i = 0; i < document.body.children.length; i++) {
      var host = document.body.children[i];
      var root = host.shadowRoot;
      if (!root || root.querySelector("style[data-docs-search]")) {
        continue;
      }
      var style = document.createElement("style");
      style.setAttribute("data-docs-search", "");
      style.textContent = STYLE;
      root.appendChild(style);
    }
  }

  patch();

  new MutationObserver(function () {
    patch();
    window.setTimeout(patch, 0);
  }).observe(document.body, { childList: true });
})();
