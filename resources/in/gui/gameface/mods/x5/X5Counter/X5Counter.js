import { ModelObserver } from "../../libs/model.js";
import { pxToRem } from "../../libs/common.js";

const observer = ModelObserver("X5Counter");
const ID = "inq-x5-root";
let down = null, dragging = false, pending = null, bounds = null;
let next = null, frame = null, removeCapture = null;
let renderFrame = null, lastState = null;

function vm() { return observer.model && observer.model.x5Data; }
function toRem(n) { return Number(pxToRem(Number(n) || 0)) || 0; }
function size() {
    return {w:toRem(document.documentElement.clientWidth || window.innerWidth),
            h:toRem(document.documentElement.clientHeight || window.innerHeight)};
}
function geometry(root) {
    const r = root.getBoundingClientRect();
    return {x:toRem(r.left), y:toRem(r.top),
            w:toRem(r.width), h:toRem(r.height)};
}
function restrict(x,y) {
    return {x:Math.max(0,Math.min(bounds.maxX,x)),
            y:Math.max(0,Math.min(bounds.maxY,y))};
}
function place(root,x,y) {
    const s=size(),r=geometry(root);
    bounds={maxX:Math.max(0,s.w-r.w),maxY:Math.max(0,s.h-r.h)};
    const p=restrict(x,y);
    root.style.transform="translate3d(0,0,0)";
    root.style.left=p.x+"rem";
    root.style.top=p.y+"rem";
    return p;
}
function modelPosition(m) {
    const x=Number(m.posX),y=Number(m.posY);
    if(Number.isFinite(x)&&Number.isFinite(y)&&x>0&&y>0) {
        const storedW=Number(m.posW)||0,storedH=Number(m.posH)||0,s=size();
        return {x:storedW>0?x*s.w/storedW:x,
                y:storedH>0?y*s.h/storedH:y};
    }
    return {x:320,y:200};
}
function sendPosition(p) {
    const m=vm();
    if(m&&typeof m.onPositionChanged==="function") {
        const s=size();
        m.onPositionChanged({x:Math.round(p.x),y:Math.round(p.y),
                             w:Math.round(s.w),h:Math.round(s.h)});
    }
}
function rootNode() {
    let root=document.getElementById(ID);
    if(root)return root;
    root=document.createElement("div");
    root.id=ID;
    root.innerHTML='<span class="inq-x5-ring">×5</span><span class="inq-x5-num">0</span><div class="inq-x5-hit-zone"></div>';
    document.body.appendChild(root);
    installInteraction();
    window.addEventListener("resize",()=>{if(!dragging){pending=null;render();}});
    return root;
}
function applyDrag(root,clientX,clientY) {
    if(!down)return;
    const p=restrict(toRem(clientX)-down.offsetX,toRem(clientY)-down.offsetY);
    down.final=p;
    root.style.transform="translate3d("+(p.x-down.baseX)+"rem,"+
                                       (p.y-down.baseY)+"rem,0)";
}
function cancelFrame() {
    if(frame!==null)cancelAnimationFrame(frame);
    frame=null;next=null;
}
function queue(root,event) {
    next={x:event.clientX,y:event.clientY};
    if(frame!==null)return;
    frame=requestAnimationFrame(()=>{
        frame=null;
        const pt=next;next=null;
        if(dragging&&pt)applyDrag(root,pt.x,pt.y);
    });
}
function finish(root,save) {
    if(!down)return;
    if(next&&dragging)applyDrag(root,next.x,next.y);
    cancelFrame();
    if(dragging&&down.moved) {
        const p=place(root,down.final.x,down.final.y);
        pending=p;
        if(save)sendPosition(p);
    } else {
        root.style.transform="translate3d(0,0,0)";
    }
    dragging=false;
    down=null;
}
function clearCapture() {
    if(removeCapture){removeCapture();removeCapture=null;}
}
function installInteraction() {
    if(document._inqX5InteractionBound)return;
    document._inqX5InteractionBound=true;
    document.addEventListener("mousedown",event=>{
        const root=document.getElementById(ID);
        if(Number(event.button)!==0||!root||root.style.display==="none"||
           !root.contains(event.target))return;
        clearCapture();
        const r=geometry(root), s=size();
        bounds={maxX:Math.max(0,s.w-r.w),maxY:Math.max(0,s.h-r.h)};
        down={x:Number(event.clientX),y:Number(event.clientY),
              baseX:r.x,baseY:r.y,
              offsetX:toRem(event.clientX)-r.x,
              offsetY:toRem(event.clientY)-r.y,
              final:{x:r.x,y:r.y},moved:false};
        dragging=true;
        pending=null;
        event.stopImmediatePropagation();
        event.preventDefault();
        const move=ev=>{
            if(!down)return;
            const dx=ev.clientX-down.x,dy=ev.clientY-down.y;
            if(dx*dx+dy*dy>1)down.moved=true;
            if(down.moved)queue(root,ev);
            ev.preventDefault();
        };
        const up=ev=>{
            if(Number(ev.button)!==0)return;
            if(down)applyDrag(root,ev.clientX,ev.clientY);
            if(down&&Math.abs(ev.clientX-down.x)+Math.abs(ev.clientY-down.y)>1)
                down.moved=true;
            clearCapture();finish(root,true);ev.preventDefault();
        };
        document.addEventListener("mousemove",move,true);
        document.addEventListener("mouseup",up,true);
        removeCapture=()=>{
            document.removeEventListener("mousemove",move,true);
            document.removeEventListener("mouseup",up,true);
        };
    },true);
    window.addEventListener("blur",()=>{
        clearCapture();const root=document.getElementById(ID);
        if(root)finish(root,true);
    });
    document.addEventListener("visibilitychange",()=>{
        if(document.hidden){
            clearCapture();const root=document.getElementById(ID);
            if(root)finish(root,true);
        }
    });
}
function render() {
    const root=rootNode(),m=vm();
    if(!m||!m.visible){root.style.display="none";return;}
    root.style.display="flex";
    root.querySelector(".inq-x5-num").textContent=String(m.count);
    if(dragging)return;
    const current=modelPosition(m);
    if(pending&&Math.abs(current.x-pending.x)<1&&Math.abs(current.y-pending.y)<1)
        pending=null;
    const p=pending||current;
    place(root,p.x,p.y);
}
function state() {
    const m=vm();
    return m?JSON.stringify([m.visible,m.count,m.posX,m.posY,m.posW,m.posH]):null;
}
function update() {
    if(renderFrame!==null)return;
    renderFrame=requestAnimationFrame(()=>{
        renderFrame=null;
        const current=state();
        if(current!==lastState){lastState=current;render();}
    });
}
function start() {
    rootNode();
    observer.onUpdate(update);
    observer.subscribe();
    engine.on("viewEnv.onDataChanged",update);
    update();
}
engine.whenReady.then(start);
