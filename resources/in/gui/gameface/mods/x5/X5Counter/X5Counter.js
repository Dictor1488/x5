// Garage sub-view injection, same OpenWG ModelObserver interface as MoE Calculator.
import { ModelObserver } from "../../libs/model.js";

const observer = ModelObserver("X5Counter");
const ID = "inq-x5-root";
let initialized = false;

function dataModel() {
    const host = observer.model && observer.model.x5Data;
    return host && host.value !== undefined ? host.value : host;
}
function invoke(name, args) {
    const direct = observer.model && observer.model.x5Data;
    let target = direct && typeof direct[name] === "function" ? direct : dataModel();
    if (target && typeof target[name] === "function") target[name](args || {});
}
function viewport() {
    return { w: window.innerWidth || 0, h: window.innerHeight || 0 };
}
function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

function ensureRoot() {
    let root = document.getElementById(ID);
    if (root) return root;
    root = document.createElement("div");
    root.id = ID;
    root.innerHTML = '<span class="inq-x5-ring">×5</span><span class="inq-x5-num">—</span>';
    document.body.appendChild(root);
    return root;
}

function render() {
    const root = ensureRoot();
    const vm = dataModel();
    if (!vm) return;
    const count = vm.count && vm.count.value !== undefined ? vm.count.value : vm.count;
    root.querySelector(".inq-x5-num").textContent = count === undefined ? "—" : String(count);
    if (root._dragging) return;
    const vp = viewport();
    let x = Number(vm.posX && vm.posX.value !== undefined ? vm.posX.value : vm.posX) || 0;
    let y = Number(vm.posY && vm.posY.value !== undefined ? vm.posY.value : vm.posY) || 0;
    const w = Number(vm.posW && vm.posW.value !== undefined ? vm.posW.value : vm.posW) || 0;
    const h = Number(vm.posH && vm.posH.value !== undefined ? vm.posH.value : vm.posH) || 0;
    if (x > 0 && y > 0 && w > 0 && h > 0) {
        x = Math.round(x * vp.w / w);
        y = Math.round(y * vp.h / h);
        const box = root.getBoundingClientRect();
        root.style.left = clamp(x, 0, Math.max(0, vp.w - box.width)) + "px";
        root.style.top = clamp(y, 0, Math.max(0, vp.h - box.height)) + "px";
        root.style.right = "auto";
    } else {
        root.style.left = "";
        root.style.top = "";
        root.style.right = "";
    }
}

function installDrag() {
    if (initialized) return;
    initialized = true;
    document.addEventListener("mousedown", function (event) {
        const root = document.getElementById(ID);
        if (!root || !event.ctrlKey || event.button !== 0 || !root.contains(event.target)) return;
        // Only claim the x5 widget; don't take inputs from other injected mods.
        event.preventDefault();
        event.stopImmediatePropagation();
        const r = root.getBoundingClientRect();
        const offsetX = event.clientX - r.left;
        const offsetY = event.clientY - r.top;
        const vp = viewport();
        root.style.right = "auto";
        root.style.left = Math.round(r.left) + "px";
        root.style.top = Math.round(r.top) + "px";
        root._dragging = true;
        function move(e) {
            const left = clamp(e.clientX - offsetX, 0, Math.max(0, vp.w - r.width));
            const top = clamp(e.clientY - offsetY, 0, Math.max(0, vp.h - r.height));
            root.style.left = Math.round(left) + "px";
            root.style.top = Math.round(top) + "px";
            e.preventDefault();
        }
        function up() {
            document.removeEventListener("mousemove", move, true);
            document.removeEventListener("mouseup", up, true);
            root._dragging = false;
            const rect = root.getBoundingClientRect();
            const now = viewport();
            invoke("setPosition", {
                x: Math.max(1, Math.round(rect.left)),
                y: Math.max(1, Math.round(rect.top)),
                w: now.w, h: now.h
            });
        }
        document.addEventListener("mousemove", move, true);
        document.addEventListener("mouseup", up, true);
    }, true);
    window.addEventListener("resize", render);
}

function start() {
    ensureRoot();
    installDrag();
    observer.subscribe(render);
    render();
}
// The OpenWG engine supplies this promise for the injected module.
if (window.engine && window.engine.whenReady) {
    window.engine.whenReady.then(start);
} else {
    start();
}
