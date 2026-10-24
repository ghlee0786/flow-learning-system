"""Blender로 3D 장면을 렌더해 레슨 이미지로 씁니다.

AI(또는 사람)가 bpy 장면 스크립트를 쓰면, Blender를 창 없이 실행해 Cycles로 렌더하고
`spot_` 로 시작하는 오브젝트(보통 빈 오브젝트)의 3D 위치가 이미지의 어디에 찍히는지 계산해
assets/<이름>.png 와 assets/<이름>.png.json(핫스폿 좌표) 를 만듭니다.
레슨에서는 {"img": ["assets/<이름>.png", {"spots": [...], "arrows": [...]}]} 로 그 위치를 가리킵니다.

장면 스크립트에서 바로 쓸 수 있는 도우미: mat, paint, spot, camera, sun, area, world, look_at, cylinder_between
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .course import Course

WRAPPER = r'''
import bpy, json, sys, math, mathutils
from bpy_extras.object_utils import world_to_camera_view
A = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
V3 = mathutils.Vector

def _set(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return

def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, emit=0.0, alpha=1.0, transmission=0.0, sss=0.0):
    """Principled BSDF 재질. color는 0~1 RGB."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    c = tuple(color) + (1.0,)
    _set(b, ["Base Color"], c); _set(b, ["Roughness"], rough); _set(b, ["Metallic"], metal)
    if emit:
        _set(b, ["Emission Color", "Emission"], c); _set(b, ["Emission Strength"], emit)
    if alpha < 1:
        _set(b, ["Alpha"], alpha); m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
    if transmission:
        _set(b, ["Transmission Weight", "Transmission"], transmission)
    if sss:
        _set(b, ["Subsurface Weight", "Subsurface"], sss)
    return m

def paint(obj, m):
    obj.data.materials.clear(); obj.data.materials.append(m); return obj

def look_at(obj, target):
    d = V3(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def camera(location, target=(0, 0, 0), lens=50):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object; cam.data.lens = lens; look_at(cam, target)
    bpy.context.scene.camera = cam; return cam

def sun(rotation=(0.8, 0.2, 0.6), energy=3.0, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="SUN", rotation=rotation)
    l = bpy.context.object; l.data.energy = energy; l.data.color = color; return l

def area(location, target=(0, 0, 0), energy=800, size=4, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=location)
    l = bpy.context.object; l.data.energy = energy; l.data.size = size; l.data.color = color; look_at(l, target); return l

def world(color=(0.03, 0.04, 0.06), strength=1.0):
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = tuple(color) + (1,); bg.inputs[1].default_value = strength
    bpy.context.scene.world = w; return w

def spot(name, location):
    """이 위치가 이미지의 어디에 찍히는지 핫스폿 '{name}'으로 기록됩니다."""
    o = bpy.data.objects.new("spot_" + name, None); o.location = location
    bpy.context.scene.collection.objects.link(o); return o

def cylinder_between(p1, p2, r=0.05, m=None):
    p1, p2 = V3(p1), V3(p2); d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(p1 + p2) / 2, vertices=24)
    o = bpy.context.object; o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    if m: paint(o, m)
    return o

G = dict(bpy=bpy, math=math, mathutils=mathutils, V3=V3, mat=mat, paint=paint, look_at=look_at, camera=camera, sun=sun,
         area=area, world=world, spot=spot, cylinder_between=cylinder_between, __name__="__main__")
exec(compile(open(A["script"], encoding="utf-8").read(), A["script"], "exec"), G)

sc = bpy.context.scene
if sc.camera is None:
    camera((7, -7, 5), (0, 0, 0.5))
if sc.world is None:
    world()
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
oidn = bool(getattr(bpy.app.build_options, "openimagedenoise", False))
sc.cycles.use_denoising = oidn
sc.cycles.samples = A["samples"] if oidn else min(512, A["samples"] * 4)
sc.cycles.sample_clamp_indirect = 6.0
sc.cycles.max_bounces = 8
sc.render.filter_size = 1.8 if not oidn else 1.5
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = A["w"], A["h"], 100
try:
    sc.view_settings.view_transform = "AgX"
except Exception:
    sc.view_settings.view_transform = "Filmic"
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = A["out"]
bpy.ops.render.render(write_still=True)
hs = {}
for o in sc.objects:
    name = o.name[5:] if o.name.startswith("spot_") else o.get("spot")
    if not name:
        continue
    co = world_to_camera_view(sc, sc.camera, o.matrix_world.translation)
    hs[name] = [round(co.x, 4), round(1 - co.y, 4)]
json.dump({"w": A["w"], "h": A["h"], "hotspots": hs, "renderer": "Blender " + bpy.app.version_string + " Cycles",
           "script": A["rel"]}, open(A["out"] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("FLS_RENDER_OK")
'''


def find_blender() -> str | None:
    env = os.environ.get("FLS_BLENDER")
    if env and Path(env).exists():
        return env
    b = shutil.which("blender")
    if b:
        return b
    cands = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"), reverse=True)
    cands += ["/Applications/Blender.app/Contents/MacOS/Blender"]
    return next((c for c in cands if Path(c).exists()), None)


def render(course: Course, name: str, script: str, width: int = 1280, height: int = 720, samples: int = 64, timeout: int = 1800) -> dict:
    blender = find_blender()
    if not blender:
        raise RuntimeError("Blender를 찾지 못했습니다. 설치하거나 FLS_BLENDER 환경 변수에 blender 실행 파일 경로를 넣으세요.")
    src_dir = course.assets_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    if "\n" not in script and Path(script).exists():
        script = Path(script).read_text(encoding="utf-8")
    sp = src_dir / f"{name}.py"
    sp.write_text(script, encoding="utf-8")
    out = course.assets_dir / f"{name}.png"
    args = {"script": str(sp), "out": str(out), "w": width, "h": height, "samples": samples, "rel": sp.relative_to(course.root).as_posix()}
    with tempfile.TemporaryDirectory(prefix="fls-blender-") as tmp:
        wp = Path(tmp) / "wrapper.py"
        wp.write_text(WRAPPER, encoding="utf-8")
        t0 = time.time()
        r = subprocess.run([blender, "-b", "--factory-startup", "-noaudio", "-P", str(wp), "--", json.dumps(args)],
                           capture_output=True, text=True, timeout=timeout)
    if "FLS_RENDER_OK" not in r.stdout:
        tail = (r.stdout + r.stderr)[-2500:]
        raise RuntimeError(f"Blender 렌더 실패:\n{tail}")
    meta = json.loads(Path(str(out) + ".json").read_text(encoding="utf-8"))
    return {"image": out.relative_to(course.root).as_posix(), "hotspots": meta["hotspots"], "size": [width, height],
            "seconds": round(time.time() - t0, 1), "script": args["rel"]}
