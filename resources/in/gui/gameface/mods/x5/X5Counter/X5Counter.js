(function () {
  'use strict';
  var label = document.getElementById('x5-value');
  var callbackId = null;
  function refresh() {
    if (label) label.textContent = window.model && window.model.count != null ? String(window.model.count) : '—';
  }
  function start() {
    refresh();
    if (window.viewEnv && viewEnv.addDataChangedCallback) {
      try { callbackId = viewEnv.addDataChangedCallback('model', 0, true); } catch (e) {}
    }
    if (window.engine) {
      window.engine.on('viewEnv.onDataChanged', function (a, b, ids) {
        if (callbackId !== null && ids && typeof ids.indexOf === 'function' && ids.indexOf(callbackId) === -1) return;
        refresh();
      });
    }
  }
  if (window.engine && window.engine.whenReady) {
    window.engine.whenReady.then(start);
  } else { start(); }
})();
