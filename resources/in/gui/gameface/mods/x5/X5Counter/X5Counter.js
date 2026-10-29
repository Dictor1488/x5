(function () {
  'use strict';
  var root = document.getElementById('x5-counter-widget');
  var label = document.getElementById('x5-value');
  var callbackId = null, dragging = false;
  function cursor(e) {
    return {x: Number.isFinite(e.screenX) ? e.screenX : e.clientX,
            y: Number.isFinite(e.screenY) ? e.screenY : e.clientY};
  }
  function call(name, data) {
    if (!window.model || typeof window.model[name] !== 'function') return;
    if (data === undefined) window.model[name]();
    else window.model[name](data);
  }
  function refresh() {
    if (label) label.textContent = window.model && window.model.count != null ?
      String(window.model.count) : '—';
  }
  function initialize() {
    if (window.viewEnv && viewEnv.resizeViewPx) {
      viewEnv.resizeViewPx(136, 54);
    }
    refresh();
    if (window.viewEnv && viewEnv.addDataChangedCallback) {
      try { callbackId = viewEnv.addDataChangedCallback('model', 0, true); }
      catch (e) { console.warn('[INQ.x5] model observer unavailable', e); }
    }
    if (window.engine) {
      window.engine.on('viewEnv.onDataChanged', function (a, b, ids) {
        if (callbackId !== null && ids && typeof ids.indexOf === 'function' &&
            ids.indexOf(callbackId) === -1) return;
        refresh();
      });
    }
    call('onReady');
  }
  if (root) {
    root.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      dragging = true;
      call('onDragStart', cursor(e));
      e.preventDefault();
    });
    document.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      var point = cursor(e);
      point.scale = (window.viewEnv && typeof viewEnv.getScale === 'function') ? viewEnv.getScale() : 1;
      call('onDrag', point);
      e.preventDefault();
    });
    function finish() {
      if (!dragging) return;
      dragging = false;
      call('onDragEnd');
    }
    document.addEventListener('mouseup', finish);
    window.addEventListener('blur', finish);
  }
  if (window.engine && window.engine.whenReady) {
    window.engine.whenReady.then(initialize);
  } else {
    initialize();
  }
})();
