#!/usr/bin/env python3
import argparse, json, subprocess, tempfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BASE=ROOT/"python/scripts/client"
SRC=[BASE/"gui/mods/mod_inq_x5.py"]
RES=ROOT/"resources/in"
def add(z,name,data):
    info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
    info.compress_type=zipfile.ZIP_STORED
    z.writestr(info,data)
def build(py27,version):
    meta=json.loads((ROOT/"build.json").read_text(encoding="utf-8"))["info"]
    if version: meta["version"]=version
    node=ET.Element("root")
    for k in ("id","version","name","description"): ET.SubElement(node,k).text=meta[k]
    dest=ROOT/"build"/"me.inq.x5.wotmod"
    dest.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        compiled=[]
        for src in SRC:
            target=Path(folder)/(src.stem+".pyc")
            subprocess.run([py27,"-c","import py_compile,sys;py_compile.compile(sys.argv[1],cfile=sys.argv[2],doraise=True)",str(src),str(target)],check=True)
            data=target.read_bytes()
            if data[:4] != bytes.fromhex("03f30d0a"): raise RuntimeError("Python 2.7 required")
            compiled.append((src,data))
        with zipfile.ZipFile(dest,"w") as z:
            add(z,"meta.xml",ET.tostring(node,encoding="utf-8",xml_declaration=True))
            for src,data in compiled: add(z,"res/scripts/client/"+src.relative_to(BASE).with_suffix(".pyc").as_posix(),data)
            for item in sorted(RES.rglob("*")):
                if item.is_file(): add(z,"res/"+item.relative_to(RES).as_posix(),item.read_bytes())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert all(i.compress_type==zipfile.ZIP_STORED for i in z.infolist())
    print(dest)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--python27",required=True)
    p.add_argument("--version")
    a=p.parse_args()
    build(a.python27,a.version)
