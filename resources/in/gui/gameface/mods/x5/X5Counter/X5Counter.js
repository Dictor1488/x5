import { ModelObserver } from "../../libs/model.js";
import { pxToRem } from "../../libs/common.js";

const observer = ModelObserver("X5Counter");
const ID = "inq-x5-root";
let dragging = false, pointerDown = null, grabX = 0, grabY = 0;
let pendingPosition = null, dragFrame = null, nextPoint = null;
let lastState = null, renderFrame = null, captureOff = null;

function model() {
    const host = observer.model;
    return host && host.x5Data;
}
function callPosition(p) {
    const m = model();
    if (m && typeof m.setPosition === "function") {
        const vp = viewport();
        m.setPosition({x:Math.round(p.x), y:Math.round(p.y), w:Math.round(vp.w), h:Math.round(vp.h)});
    }
}
function rem(px) {
    try { return Number(pxToRem(Number(px) || 0)) || 0; }
    catch (_) { return Number(px) || 0; }
}
function viewport() {
    return {w:rem(document.documentElement.clientWidth || window.innerWidth),
            h:rem(document.documentElement.clientHeight || window.innerHeight)};
}
function rectRem(root) {
    const r = root.getBoundingClientRect();
    return {x:rem(r.left), y:rem(r.top), w:rem(r.width), h:rem(r.height)};
}
function clamp(root, x, y) {
    const vp = viewport(), r = rectRem(root);
    return {x:Math.max(0,Math.min(Math.max(0,vp.w-r.w),x)),
            y:Math.max(0,Math.min(Math.max(0,vp.h-r.h),y))};
}
function place(root,x,y) {
    const p=clamp(root,x,y);
    root.style.transform="translate3d(0,0,0)";
    root.style.left=p.x+"rem"; root.style.top=p.y+"rem";
    return p;
}
function rootElement() {
    let root=document.getElementById(ID);
    if(root)return root;
    root=document.createElement("div");
    root.id=ID;
    root.innerHTML='<span class="inq-x5-ring">×5</span><span class="inq-x5-num">—</span><div class="inq-x5-hit-zone"></div>';
    document.body.appendChild(root);
    bind(root);
    return root;
}
function targetPosition(root,m) {
    const vp=viewport();
    const w=Number(m.posW)||0,h=Number(m.posH)||0;
    const x=Number(m.posX)||0,y=Number(m.posY)||0;
    if(w>0&&h>0&&x>=0&&y>=0) return clamp(root,x*vp.w/w,y*vp.h/h);
    return clamp(root,320,200);
}
function render() {
    const root=rootElement(),m=model();
    if(!m || m.visible !== true) {root.style.display="none";return;}
    root.style.display="flex";
    root.querySelector(".inq-x5-num").textContent=String(m.count === undefined?"—":m.count);
    if(!dragging) {
        const p=pendingPosition||targetPosition(root,m);
        place(root,p.x,p.y);
        if(pendingPosition) {
            const actual=targetPosition(root,m);
            if(Math.abs(actual.x-pendingPosition.x)<1&&Math.abs(actual.y-pendingPosition.y)<1)
                pendingPosition=null;
        }
    }
}
function endDrag(root,save) {
    if(nextPoint && dragging) drawDrag(root,nextPoint);
    if(dragFrame!==null) cancelAnimationFrame(dragFrame);
    dragFrame=null;nextPoint=null;
    if(dragging) {
        const p=rectRem(root);
        root.style.transform="translate3d(0,0,0)";
        const fixed=place(root,p.x,p.y);
        if(pointerDown && pointerDown.moved && save) {
            pendingPosition=fixed;
            callPosition(fixed);
        }
    }
    dragging=false;pointerDown=null;
}
function drawDrag(root,e) {
    const next=clamp(root,rem(e.x)-grabX,rem(e.y)-grabY);
    root.style.transform="translate3d(0,0,0)";
    root.style.left=next.x+"rem";root.style.top=next.y+"rem";
}
function unbindCapture() { if(captureOff){captureOff();captureOff=null;} }
function bind(root) {
    if(document._inqX5Bound)return;
    document._inqX5Bound=true;
    document.addEventListener("mousedown",e=>{
        const current=document.getElementById(ID);
        if(!current||current.style.display==="none"||!current.contains(e.target)||Number(e.button)!==0)return;
        const r=rectRem(current);
        grabX=rem(e.clientX)-r.x;grabY=rem(e.clientY)-r.y;
        pointerDown={x:e.clientX,y:e.clientY,moved:false};dragging=true;
        e.stopImmediatePropagation();e.preventDefault();
        unbindCapture();
        const onMove=ev=>{
            if(!dragging)return;
            if(Math.abs(ev.clientX-pointerDown.x)+Math.abs(ev.clientY-pointerDown.y)>1) pointerDown.moved=true;
            nextPoint={x:ev.clientX,y:ev.clientY};
            if(dragFrame===null) dragFrame=requestAnimationFrame(()=>{
                dragFrame=null;
                if(dragging&&nextPoint)drawDrag(current,nextPoint);
                nextPoint=null;
            });
            ev.preventDefault();
        };
        const onUp=ev=>{
            if(Number(ev.button)!==0)return;
            if(dragging)drawDrag(current,{x:ev.clientX,y:ev.clientY});
            unbindCapture();endDrag(current,true);ev.preventDefault();
        };
        document.addEventListener("mousemove",onMove,true);
        document.addEventListener("mouseup",onUp,true);
        captureOff=()=>{
            document.removeEventListener("mousemove",onMove,true);
            document.removeEventListener("mouseup",onUp,true);
        };
    },true);
    window.addEventListener("blur",()=>{unbindCapture();endDrag(root,true);});
    document.addEventListener("visibilitychange",()=>{if(document.hidden){unbindCapture();endDrag(root,true);}});
    window.addEventListener("resize",()=>{pendingPosition=null;render();});
}
function state() {
    const m=model();
    return m?JSON.stringify([m.visible,m.count,m.posX,m.posY,m.posW,m.posH,m.rev]):null;
}
function updated() {
    if(renderFrame!==null)return;
    renderFrame=requestAnimationFrame(()=>{
        renderFrame=null;
        const s=state();
        if(s!==lastState){lastState=s;render();}
    });
}
function start() {
    rootElement();
    observer.onUpdate(updated);
    observer.subscribe();
    engine.on("viewEnv.onDataChanged",updated);
    updated();
}
if(window.engine&&window.engine.whenReady)engine.whenReady.then(start);
else start();
