(function () {
  "use strict";

  if (!document.startViewTransition) {
    return;
  }

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var replaying = false;
  var root = document.documentElement;
  var transitionId = 0;

  function isPaletteToggle(target) {
    return (
      target &&
      target.name === "__palette" &&
      target.form &&
      target.form.getAttribute("data-md-component") === "palette"
    );
  }

  // Sites can expose this to finish theme work before the new view is captured.
  function waitForSettled() {
    var settled = window.docsThemeSettled;
    var siteWork =
      typeof settled === "function" ? Promise.resolve().then(settled) : Promise.resolve();

    return Promise.race([
      siteWork,
      new Promise(function (resolve) {
        window.setTimeout(resolve, 500);
      }),
    ])
      .catch(function () {
        // A broken hook must not block the theme change.
      })
      .then(function () {
        // Let the theme styles apply before the browser captures the new view.
        return new Promise(function (resolve) {
          window.setTimeout(resolve, 0);
        });
      });
  }

  function applyChange(input) {
    replaying = true;
    try {
      input.dispatchEvent(new Event("change", { bubbles: true }));
    } finally {
      replaying = false;
    }

    return waitForSettled();
  }

  function onChange(event) {
    if (replaying || reducedMotion.matches) {
      return;
    }

    var input = event.target;
    if (!isPaletteToggle(input)) {
      return;
    }

    event.stopImmediatePropagation();

    var id = ++transitionId;
    root.classList.add("theme-transitioning");

    function finish() {
      if (id === transitionId) {
        root.classList.remove("theme-transitioning");
      }
    }

    try {
      var transition = document.startViewTransition(function () {
        return applyChange(input);
      });
      transition.ready.catch(function () {});
      transition.finished.then(finish, finish);
    } catch (error) {
      finish();
      applyChange(input);
    }
  }

  document.addEventListener("change", onChange, true);
})();
