(function () {
  'use strict';
  var root = document.getElementById('x5-counter-widget');
  var label = document.getElementById('x5-value');
  var callbackId = null;
  var held = false, lastX = 0, lastY = 0;
  function refresh() {
    if (label) label.textContent = window.model && window.model.count != null ?
      String(window.model.count) : '—';
  }
  function resize() {
    if (window.viewEnv && viewEnv.resizeViewPx) viewEnv.resizeViewPx(220, 65);
  }
  function start() {
    resize();
    refresh();
    if (window.viewEnv && viewEnv.addDataChangedCallback) {
      try { callbackId = viewEnv.addDataChangedCallback('model', 0, true); } catch (e) {}
    }
    if (window.engine) {
      window.engine.on('viewEnv.onDataChanged', function (a, b, ids) {
        if (callbackId !== null && ids && typeof ids.indexOf === 'function' &&
            ids.indexOf(callbackId) === -1) return;
        refresh();
      });
    }
    if (window.model && typeof window.model.onReady === 'function') window.model.onReady();
  }
  if (root) {
    root.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      held = true;
      lastX = e.screenX;
      lastY = e.screenY;
      e.preventDefault();
    });
    document.addEventListener('mousemove', function (e) {
      if (!held) return;
      var dx = Math.round(e.screenX - lastX), dy = Math.round(e.screenY - lastY);
      if (!dx && !dy) return;
      lastX = e.screenX;
      lastY = e.screenY;
      if (window.model && typeof window.model.onDrag === 'function') {
        window.model.onDrag({dx: dx, dy: dy});
      }
    });
    document.addEventListener('mouseup', function () { held = false; });
    window.addEventListener('blur', function () { held = false; });
  }
  if (window.engine && window.engine.whenReady) {
    window.engine.whenReady.then(start);
  } else { start(); }
})();
