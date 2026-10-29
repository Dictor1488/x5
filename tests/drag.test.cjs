// Node-only regression of GameFace DOM drag. No game installation required.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');

const listeners = new Map();
const store = new Map();
const updates = [];
const root = {
  style: {},
  _dragging: false,
  innerHTML: '',
  contains(target) { return target === this; },
  addEventListener(type, fn) { store.set(type, fn); },
  querySelector() { return countLabel; },
  getBoundingClientRect() {
    return {
      left: parseInt(this.style.left || '320', 10),
      top: parseInt(this.style.top || '200', 10),
      width: 115, height: 48
    };
  }
};
const countLabel = {textContent: '—'};
const document = {
  getElementById(id) { return id === 'inq-x5-root' ? root : null; },
  createElement() { return root; },
  body: {appendChild() {}},
  addEventListener(type, fn) { listeners.set(type, fn); },
  removeEventListener(type, fn) { if (listeners.get(type) === fn) listeners.delete(type); }
};
const state = {
  x5Data: {
    visible: true, count: '40', posX: 0, posY: 0, posW: 0, posH: 0,
    setPosition(payload) { updates.push(payload); }
  }
};
const observer = {
  model: state, onUpdate(fn) { this.render = fn; }, subscribe() {}
};
const context = {
  document, window: {innerWidth: 800, innerHeight: 600, addEventListener() {}},
  engine: {whenReady: Promise.resolve()},
  __ModelObserver() { return observer; },
  console
};
const source = fs.readFileSync(path.join(__dirname, '..', 'resources/in/gui/gameface/mods/x5/X5Counter/X5Counter.js'), 'utf8')
  .replace(/^import \{ ModelObserver \} from .*;$/m, 'const ModelObserver = __ModelObserver;');
vm.runInNewContext(source, context);
function fire(type, event) {
  const fn = listeners.get(type);
  assert.ok(fn, 'Missing ' + type + ' listener');
  fn(event);
}
Promise.resolve().then(() => {
  assert.equal(countLabel.textContent, '40');
  let claimed = false;
  const mouseDown = store.get('mousedown');
  assert.ok(mouseDown, 'Missing widget-local mousedown handler');
  mouseDown({
    target: root, clientX: 330, clientY: 210,
    preventDefault() { claimed = true; }, stopImmediatePropagation() {}
    // GameFace often supplies no standard MouseEvent.button field.
  });
  assert.ok(claimed, 'root mousedown without button must start drag');
  fire('mousemove', {clientX: 450, clientY: 260, preventDefault() {}});
  assert.equal(root.style.left, '440px');
  assert.equal(root.style.top, '250px');
  fire('mousemove', {clientX: 9999, clientY: 9999, preventDefault() {}});
  assert.equal(root.style.left, '685px');
  assert.equal(root.style.top, '552px');
  fire('mouseup', {});
  assert.equal(updates.length, 1);
  assert.equal(updates[0].x, 685);
  assert.equal(updates[0].y, 552);
  assert.equal(updates[0].w, 800);
  assert.equal(updates[0].h, 600);
  console.log('PASS: x5 DOM drag without MouseEvent.button, viewport clamped, persisted on mouseup');
}).catch(e => { console.error(e); process.exitCode = 1; });
