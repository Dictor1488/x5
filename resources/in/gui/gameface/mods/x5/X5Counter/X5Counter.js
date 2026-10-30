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
    if (target && typeof target[name] === "function") {
        try { target[name](args || {}); }
        catch (error) { console.error("[x5] " + name + " failed", error); }
    } else {
        console.error("[x5] missing ViewModel command: " + name);
    }
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
    const visible = vm.visible && vm.visible.value !== undefined ? vm.visible.value : vm.visible;
    root.style.display = visible === true ? 'flex' : 'none';
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

// Document capture gives this widget ownership only when it received the hit.
// Move locally, then send the final position through the Wulf command.
function installDrag() {
    if (initialized) return;
    const root = ensureRoot();
    initialized = true;

    // Gameface's documented mouse-driven drag pattern: begin on the element,
    // track movement on the document and finish on mouse release.
    root.addEventListener("mousedown", function (e) {
        if (root.style.display === "none") return;
        if (e.button !== undefined && e.button !== 0) return;
        if (e.preventDefault) e.preventDefault();
        if (e.stopPropagation) e.stopPropagation();

        const bounds = root.getBoundingClientRect();
        const startX = e.clientX, startY = e.clientY;
        const initialLeft = bounds.left, initialTop = bounds.top;
        const boxW = bounds.width, boxH = bounds.height;
        let moved = false;

        // Fixed-position widget switches from its CSS default to a pixel anchor.
        root.style.right = "auto";
        root.style.bottom = "auto";
        root.style.left = Math.round(initialLeft) + "px";
        root.style.top = Math.round(initialTop) + "px";
        root._dragging = true;

        function onMove(ev) {
            if (ev.preventDefault) ev.preventDefault();
            const vp = viewport();
            const dx = ev.clientX - startX, dy = ev.clientY - startY;
            if (Math.abs(dx) > 1 || Math.abs(dy) > 1) moved = true;
            let x = clamp(initialLeft + dx, 0, Math.max(0, vp.w - boxW));
            let y = clamp(initialTop + dy, 1, Math.max(1, vp.h - boxH));
            if (ev.shiftKey) {
                if (Math.abs(dx) >= Math.abs(dy)) y = initialTop;
                else x = initialLeft;
            }
            root.style.left = Math.round(x) + "px";
            root.style.top = Math.round(y) + "px";
        }

        function onUp() {
            document.removeEventListener("mousemove", onMove, true);
            document.removeEventListener("mouseup", onUp, true);
            window.removeEventListener("blur", onUp);
            root._dragging = false;
            if (!moved) return;
            const vp = viewport();
            const rect = root.getBoundingClientRect();
            if (!vp.w || !vp.h) return;
            invoke("setPosition", {
                x: Math.max(1, Math.round(rect.left)),
                y: Math.max(1, Math.round(rect.top)),
                w: vp.w, h: vp.h
            });
        }

        document.addEventListener("mousemove", onMove, true);
        document.addEventListener("mouseup", onUp, true);
        window.addEventListener("blur", onUp);
    });
    window.addEventListener("resize", render);
}

function start() {
    ensureRoot();
    installDrag();
    observer.onUpdate(render);
    observer.subscribe();
    render();
}
// The OpenWG engine supplies this promise for the injected module.
if (window.engine && window.engine.whenReady) {
    window.engine.whenReady.then(start);
} else {
    start();
}
