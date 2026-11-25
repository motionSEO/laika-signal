"""
라이카 시그널 — 송신기(레트로 영수증 프린터) 모델 생성 스크립트

사용법
  1. Blender 상단의 Scripting 탭을 연다.
  2. Open 으로 이 파일을 열거나, 내용을 붙여 넣는다.
  3. Run Script (▶) 를 누른다.
  다시 실행하면 'LaikaPrinter' 컬렉션을 지우고 새로 만든다.

  GLB 로 내보내려면 아래 EXPORT_GLB 에 저장 경로를 적고 실행한다.
  예) EXPORT_GLB = "/Users/me/Desktop/laika_printer.glb"
"""

import bpy
import bmesh
import math

EXPORT_GLB = None        # 예: "/Users/me/Desktop/laika_printer.glb"
ADD_STAGE = True         # 흰 테이블, 조명, 카메라까지 함께 만들기

# ---------------------------------------------------------------
# 치수 (단위: m, 실제 크기 약 20cm 정도)
# ---------------------------------------------------------------
W = 1.00                 # 몸체 가로
FRONT_Y, BACK_Y = -0.62, 0.62
BASE_H = 0.05            # 아래 받침 두께 (몸체와 사이에 이음선)
FRONT_H = 0.30           # 앞면 높이 (받침 위)
SLOPE_TOP = 0.44         # 경사면 끝 높이
CHAMFER = 0.06
HOOD_R = 0.30            # 뒤쪽 원통 덮개 반지름
HOOD_Y = 0.30
HOOD_LEN = 0.86

COL_NAME = "LaikaPrinter"


# ---------------------------------------------------------------
# 정리
# ---------------------------------------------------------------
def reset_collection():
    col = bpy.data.collections.get(COL_NAME)
    if col:
        for ob in list(col.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    else:
        col = bpy.data.collections.new(COL_NAME)
        bpy.context.scene.collection.children.link(col)
    return col


COL = reset_collection()


def link(ob):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    COL.objects.link(ob)
    return ob


# ---------------------------------------------------------------
# 재질
# ---------------------------------------------------------------
def set_input(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return


def material(name, color, rough=0.5, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, ["Base Color"], (*color, 1.0))
    set_input(bsdf, ["Roughness"], rough)
    if emission is not None:
        set_input(bsdf, ["Emission Color", "Emission"], (*emission, 1.0))
        set_input(bsdf, ["Emission Strength"], strength)
    return m


IVORY = material("Laika_Ivory", (0.72, 0.68, 0.60), 0.42)
RECESS = material("Laika_Recess", (0.015, 0.015, 0.015), 0.7)
PANEL = material("Laika_Panel", (0.02, 0.02, 0.022), 0.18)
FOOT = material("Laika_Foot", (0.05, 0.05, 0.05), 0.8)
LED_GREEN = material("Laika_LED_Green", (0.05, 0.45, 0.12), 0.2, (0.1, 1.0, 0.25), 1.5)
LED_DIM = material("Laika_LED_Dim", (0.25, 0.22, 0.05), 0.3)
LED_SIGNAL = material("Laika_LED_Signal", (0.75, 0.12, 0.05), 0.25, (1.0, 0.45, 0.18), 0.0)  # 송신 표시등 (주황빛 빨강)


def bevel(ob, width=0.012, segs=4):
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segs
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    return mod


def shade_smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True
    if hasattr(ob.data, "use_auto_smooth"):
        ob.data.use_auto_smooth = True
        ob.data.auto_smooth_angle = math.radians(35)


def box(name, size, loc, mat, rot=(0, 0, 0), bev=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bev:
        bevel(ob, bev, 3)
    return link(ob)


# ---------------------------------------------------------------
# 1. 몸체 — 앞이 낮고 뒤로 갈수록 살짝 올라가는 옆 단면을 가로로 밀어냄
# ---------------------------------------------------------------
def make_body():
    z0 = BASE_H
    profile = [  # (y, z)
        (FRONT_Y, z0),
        (FRONT_Y, z0 + FRONT_H),
        (FRONT_Y + CHAMFER, z0 + FRONT_H + CHAMFER),
        (-0.02, z0 + SLOPE_TOP),
        (BACK_Y, z0 + SLOPE_TOP),
        (BACK_Y, z0),
    ]
    me = bpy.data.meshes.new("Body")
    bm = bmesh.new()
    left = [bm.verts.new((-W / 2, y, z)) for y, z in profile]
    right = [bm.verts.new((W / 2, y, z)) for y, z in profile]
    bm.faces.new(list(reversed(left)))
    bm.faces.new(right)
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([left[i], left[j], right[j], right[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Body", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(IVORY)
    bevel(ob, 0.018, 5)
    shade_smooth(ob)
    return link(ob)


body = make_body()

# 아래 받침 (몸체보다 아주 조금 작아 이음선이 생김)
box("Base", (W - 0.008, BACK_Y - FRONT_Y - 0.008, BASE_H - 0.004),
    (0, 0, BASE_H / 2 - 0.002), IVORY, bev=0.01)

# 발
for sx in (-1, 1):
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.035, depth=0.012,
                                            location=(sx * 0.4, sy * 0.52, -0.004))
        f = bpy.context.active_object
        f.name = "Foot"
        f.data.materials.append(FOOT)
        link(f)

# ---------------------------------------------------------------
# 2. 뒤쪽 원통 덮개 (가로로 누운 원통)
# ---------------------------------------------------------------
hood_z = BASE_H + SLOPE_TOP
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=HOOD_R, depth=HOOD_LEN,
                                    location=(0, HOOD_Y, hood_z),
                                    rotation=(0, math.radians(90), 0))
hood = bpy.context.active_object
hood.name = "Hood"
hood.data.materials.append(IVORY)
bevel(hood, 0.02, 5)
shade_smooth(hood)
link(hood)

# 덮개와 몸체 사이의 살짝 들어간 홈
box("HoodGap", (HOOD_LEN + 0.01, 0.012, 0.03), (0, HOOD_Y - HOOD_R - 0.004, hood_z - 0.012), RECESS)

# ---------------------------------------------------------------
# 3. 송신 슬롯 — 원통 위 (카드를 넣는 곳)
# ---------------------------------------------------------------
box("Slot_In", (0.44, 0.022, 0.02),
    (0, HOOD_Y - 0.03, hood_z + HOOD_R - 0.004), RECESS,
    rot=(math.radians(-6), 0, 0))

# ---------------------------------------------------------------
# 4. 수신 슬롯 — 앞 경사면 (기록지가 나오는 곳)
# ---------------------------------------------------------------
y_a, z_a = FRONT_Y + CHAMFER, BASE_H + FRONT_H + CHAMFER
y_b, z_b = -0.02, BASE_H + SLOPE_TOP
slope = math.atan2(z_b - z_a, y_b - y_a)
sy = -0.30
sz = z_a + (sy - y_a) * math.tan(slope)
# 슬롯 주변의 살짝 솟은 테두리
box("Slot_Out_Frame", (0.62, 0.11, 0.012), (0, sy, sz + 0.004), IVORY,
    rot=(slope, 0, 0), bev=0.004)
box("Slot_Out", (0.54, 0.022, 0.02), (0, sy, sz + 0.009), RECESS,
    rot=(slope, 0, 0))

# ---------------------------------------------------------------
# 5. 앞면 조작부 + 표시등
# ---------------------------------------------------------------
panel_z = BASE_H + 0.12
box("Panel", (0.22, 0.012, 0.1), (0.29, FRONT_Y - 0.004, panel_z), PANEL, bev=0.004)


def led(name, x, mat, r=0.016):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r,
                                         location=(x, FRONT_Y - 0.011, panel_z))
    o = bpy.context.active_object
    o.name = name
    o.scale.y = 0.5
    o.data.materials.append(mat)
    shade_smooth(o)
    return link(o)


led("LED_Green", 0.235, LED_GREEN)
led("LED_Dim", 0.275, LED_DIM, 0.008)
led("LED_Signal", 0.315, LED_SIGNAL)

# 전체를 하나로 묶는 빈 오브젝트 (움직이기 편하게)
root = bpy.data.objects.new("LaikaPrinter_Root", None)
link(root)
for ob in COL.objects:
    if ob is not root:
        ob.parent = root

# ---------------------------------------------------------------
# 6. 무대 — 흰 테이블, 부드러운 창가 빛, 45도 카메라
# ---------------------------------------------------------------
if ADD_STAGE:
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.01))
    table = bpy.context.active_object
    table.name = "Table"
    table.data.materials.append(material("Laika_Table", (0.86, 0.86, 0.85), 0.85))
    link(table)

    bpy.ops.object.light_add(type="AREA", location=(-2.2, -1.5, 3.0))
    key = bpy.context.active_object
    key.name = "Key_Window"
    key.data.energy = 320
    key.data.size = 3.0
    key.rotation_euler = (math.radians(35), math.radians(-35), 0)
    link(key)

    bpy.ops.object.light_add(type="AREA", location=(2.5, -2.0, 2.0))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 90
    fill.data.size = 4.0
    fill.rotation_euler = (math.radians(50), math.radians(40), 0)
    link(fill)

    bpy.ops.object.camera_add(location=(1.9, -3.3, 2.9))
    cam = bpy.context.active_object
    cam.name = "Camera_45"
    cam.data.lens = 50
    aim = bpy.data.objects.new("Camera_Target", None)
    aim.location = (0, 0, 0.32)
    link(aim)
    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    link(cam)
    bpy.context.scene.camera = cam

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.9, 0.9, 0.89, 1)
        bg.inputs[1].default_value = 0.35

    scene = bpy.context.scene
    scene.render.resolution_x = 3200
    scene.render.resolution_y = 1800
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        scene.view_settings.view_transform = "Filmic"

# ---------------------------------------------------------------
# 7. GLB 내보내기 (선택)
# ---------------------------------------------------------------
if EXPORT_GLB:
    bpy.ops.object.select_all(action="DESELECT")
    for ob in COL.objects:
        if ob.name not in ("Table", "Key_Window", "Fill", "Camera_45", "Camera_Target"):
            ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=EXPORT_GLB, export_format="GLB",
                              use_selection=True, export_apply=True)
    print("GLB 저장:", EXPORT_GLB)

print("라이카 시그널 송신기 모델 생성 완료")
