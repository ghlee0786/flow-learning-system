# 동물 세포 단면: 앞쪽 1/8을 잘라 내 안쪽 소기관을 보여 줌. 소기관 위치를 핫스폿으로 남김
import random
random.seed(4)
world((0.010, 0.012, 0.020), 1.0)
R = 3.0
bpy.ops.mesh.primitive_cube_add(size=1, location=(1.6, -1.6, 1.6)); cutter = bpy.context.object
cutter.scale = (3.2, 3.2, 3.2); cutter.hide_render = True; cutter.display_type = "WIRE"

cutters = {}
def cutter_at(off):
    if off not in cutters:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(1.6 + off, -1.6 - off, 1.6 + off)); c = bpy.context.object
        c.scale = (3.2, 3.2, 3.2); c.hide_render = True; c.display_type = "WIRE"; cutters[off] = c
    return cutters[off]

def cut(o, op="DIFFERENCE", off=0.0):
    m = o.modifiers.new("cut", "BOOLEAN"); m.operation = op; m.object = cutter_at(off) if off else cutter; m.solver = "EXACT"
    return o

def sphere(r, loc, mt, seg=64, scale=(1, 1, 1), rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2, rotation=rot)
    o = bpy.context.object; o.scale = scale; bpy.ops.object.shade_smooth(); return paint(o, mt)

M = dict(
    memb=mat("membrane", (0.85, 0.45, 0.50), rough=0.35),
    cyto=mat("cytoplasm", (0.93, 0.80, 0.70), rough=0.5),
    nuc=mat("nucleus", (0.42, 0.28, 0.70), rough=0.4),
    nuc_in=mat("chromatin", (0.62, 0.48, 0.86), rough=0.5),
    nl=mat("nucleolus", (0.22, 0.10, 0.40), rough=0.4),
    mito=mat("mito", (0.95, 0.52, 0.18), rough=0.35),
    mito_in=mat("cristae", (0.85, 0.32, 0.10), rough=0.4),
    er=mat("er", (0.25, 0.55, 0.90), rough=0.35),
    golgi=mat("golgi", (0.25, 0.72, 0.45), rough=0.35),
    lyso=mat("lyso", (0.85, 0.20, 0.25), rough=0.3),
    ribo=mat("ribo", (0.20, 0.12, 0.30), rough=0.5),
    ves=mat("vesicle", (0.55, 0.85, 0.65), rough=0.25))
# 세포막(바깥 껍질)과 세포질
memb = sphere(R, (0, 0, 0), M["memb"]); s = memb.modifiers.new("shell", "SOLIDIFY"); s.thickness = 0.10; cut(memb)
cyto = sphere(R - 0.10, (0, 0, 0), M["cyto"]); cut(cyto)
# 핵, 인
nuc = sphere(1.15, (0, 0, 0), M["nuc"]); cut(nuc, off=0.035)
inner = sphere(1.02, (0, 0, 0), M["nuc_in"]); cut(inner, off=0.06)
nl = sphere(0.40, (0.30, -0.30, 0.30), M["nl"], seg=48); cut(nl, off=0.085)
# 미토콘드리아 (바닥 단면 위에 누워 있음)
mitos = [((1.75, -0.75, 0.20), 0.6), ((0.75, -1.95, 0.22), -0.9), ((2.15, -1.55, 0.20), 1.4)]
for (loc, rz) in mitos:
    sphere(0.30, loc, M["mito"], seg=48, scale=(1.9, 0.75, 0.62), rot=(0, 0, rz))
# 소포체: 핵을 둘러싼 얇은 판(반지) 일부만 남김
for k, (rad, z) in enumerate([(1.45, 0.12), (1.62, 0.30), (1.78, 0.48), (1.50, 0.68)]):
    bpy.ops.mesh.primitive_torus_add(major_radius=rad, minor_radius=0.055, location=(0, 0, z), major_segments=96, minor_segments=12)
    t = bpy.context.object; t.scale = (1, 1, 0.55); paint(t, M["er"]); cut(t, "INTERSECT")
    for q in range(10):
        a = math.radians(-85 + q * 8.5)
        sphere(0.045, (rad * math.cos(a), rad * math.sin(a), z + 0.07), M["ribo"], seg=12)
# 골지체: 뒤쪽 벽(y=0) 앞에 휘어진 판 4장
for k in range(4):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.75 - k * 0.07, minor_radius=0.06, location=(1.75, -0.25 - k * 0.16, 1.55), rotation=(math.radians(90), 0, 0), major_segments=64, minor_segments=12)
    g = bpy.context.object; g.scale = (1.0, 0.45, 1.0); paint(g, M["golgi"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.75, -0.6, 1.0)); cc = bpy.context.object; cc.scale = (3, 3, 1.1); cc.hide_render = True
    m = g.modifiers.new("half", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = cc; m.solver = "EXACT"
for k in range(3):
    sphere(0.10, (2.35 - k * 0.12, -0.45 - k * 0.25, 2.05 + k * 0.1), M["ves"], seg=16)
# 리소좀
sphere(0.30, (2.35, -0.35, 0.30), M["lyso"], seg=32)
sphere(0.20, (0.55, -2.55, 0.25), M["lyso"], seg=24)
# 자유 리보솜
for q in range(45):
    rr, a = random.uniform(1.3, 2.7), random.uniform(math.radians(-88), math.radians(-2))
    sphere(0.04, (rr * math.cos(a), rr * math.sin(a), 0.04), M["ribo"], seg=10)
# 핫스폿
spot("membrane", (-0.95, -2.80, 0.75))
spot("cytoplasm", (1.45, -2.25, 0.02))
spot("nucleus", (0.80, -0.30, 0.035))
spot("nucleolus", (0.30, -0.30, 0.085))
spot("er", (1.62 * math.cos(math.radians(-45)), 1.62 * math.sin(math.radians(-45)), 0.32))
spot("ribosome", (1.45 * math.cos(math.radians(-30)), 1.45 * math.sin(math.radians(-30)), 0.2))
spot("mitochondria", mitos[0][0])
spot("golgi", (1.75, -0.75, 1.55))
spot("lysosome", (2.35, -0.35, 0.30))
spot("vesicle", (2.23, -0.70, 2.15))
# 조명·카메라
area((6, -6, 7), (0.5, -0.5, 0.5), energy=900, size=5, color=(1.0, 0.96, 0.92))
area((-5, -4, 3), (0, 0, 0.5), energy=300, size=6, color=(0.65, 0.75, 1.0))
area((2, 5, 6), (0, 0, 0), energy=250, size=4, color=(1.0, 0.85, 0.85))
camera((7.6, -7.0, 6.2), (0.55, -0.55, 0.35), lens=48)
