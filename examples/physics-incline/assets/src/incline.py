# 빗면(30°) 위의 상자와 중력의 분해 — 힘 화살표 끝점을 3D에서 계산해 핫스폿으로 남김
import bmesh
th = math.radians(30)
L, W = 6.0, 2.4
b, h = L * math.cos(th), L * math.sin(th)
world((0.012, 0.016, 0.024), 1.0)
# 빗면(삼각기둥)
me = bpy.data.meshes.new("wedge"); ob = bpy.data.objects.new("wedge", me); bpy.context.scene.collection.objects.link(ob)
bm = bmesh.new()
v = [bm.verts.new(p) for p in [(0, -W/2, 0), (b, -W/2, 0), (0, -W/2, h), (0, W/2, 0), (b, W/2, 0), (0, W/2, h)]]
for f in [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)]:
    bm.faces.new([v[i] for i in f])
bm.normal_update(); bm.to_mesh(me); bm.free()
paint(ob, mat("wood", (0.42, 0.27, 0.15), rough=0.6))
# 바닥
bpy.ops.mesh.primitive_plane_add(size=40, location=(b / 2, 0, 0)); paint(bpy.context.object, mat("floor", (0.07, 0.08, 0.10), rough=0.8))
# 상자
s, a = 2.6, 1.1
d = V3((math.cos(th), 0, -math.sin(th))); n = V3((math.sin(th), 0, math.cos(th)))
P = V3((0, 0, h)) + d * s
C = P + n * (a / 2)
bpy.ops.mesh.primitive_cube_add(size=a, location=C, rotation=(0, th, 0))
bx = bpy.context.object
bpy.ops.object.modifier_add(type="BEVEL"); bx.modifiers["Bevel"].width = 0.06; bx.modifiers["Bevel"].segments = 3
paint(bx, mat("box", (0.10, 0.55, 0.60), rough=0.35))
# 힘 화살표 끝점 (그림 앞쪽 면 y = -W/2 - 0.05 에 투영되도록 같은 y에 둠)
y = -0.0
G = 2.6
c = V3((C.x, y, C.z))
spot("block", c)
spot("g_tip", c + V3((0, 0, -G)))
spot("par_tip", c + d * (G * math.sin(th)))
spot("perp_tip", c - n * (G * math.cos(th)))
spot("n_tip", c + n * (G * math.cos(th)))
spot("top", (0, -W / 2, h))
spot("corner", (b, -W / 2, 0))
spot("theta", (b - 0.9, -W / 2, 0.22))
spot("slope_mid", (b * 0.25, -W / 2, h * 0.75))
# 조명과 카메라
area((b / 2 - 2, -6, 7), (b / 2, 0, 1), energy=650, size=6, color=(1.0, 0.95, 0.88))
area((b + 4, 3, 4), (b / 2, 0, 1), energy=260, size=5, color=(0.7, 0.8, 1.0))
sun((0.9, 0.0, 0.5), energy=1.2)
camera((b / 2 + 0.3, -12.5, 2.4), (b / 2 + 0.3, 0, 1.55), lens=42)
