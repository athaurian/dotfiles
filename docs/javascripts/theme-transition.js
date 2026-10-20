(function () {
  "use strict";

  if (!document.startViewTransition) {
    return;
  }

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var replaying = false;

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
    if (typeof settled !== "function") {
      return;
    }

    return Promise.race([
      Promise.resolve().then(settled),
      new Promise(function (resolve) {
        window.setTimeout(resolve, 500);
      }),
    ]).catch(function () {
      // A broken hook must not block the theme change.
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

    try {
      var transition = document.startViewTransition(function () {
        return applyChange(input);
      });
      transition.ready.catch(function () {});
      transition.finished.catch(function () {});
    } catch (error) {
      applyChange(input);
    }
  }

  document.addEventListener("change", onChange, true);
})();
