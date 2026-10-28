(function () {
  'use strict';
  if (document.getElementById('x5-counter-widget')) return;
  var host = document.createElement('div');
  host.id = 'x5-counter-widget';
  host.innerHTML = '<span class="x5-multiplier">×5</span><span class="x5-label">XP</span><span class="x5-count" aria-label="Available XP bonuses">—</span>';
  document.body.appendChild(host);
  // TODO: Replace this exposed callback with an actual OpenWG ViewModel observer.
  // Unknown count is shown as —, not a fabricated zero.
  window.x5CounterSetCount = function (amount) {
    if (typeof amount !== 'number' || !isFinite(amount) || amount < 0) return;
    var el = document.querySelector('#x5-counter-widget .x5-count');
    if (el) el.textContent = String(Math.floor(amount));
  };
})();
