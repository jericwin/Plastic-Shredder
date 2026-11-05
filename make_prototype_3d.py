"""True-to-colour 3D model (MESH entities) of the shredder + heat press prototype.
Units mm.  X = length (left->right), Y = depth (front=0 -> back), Z = height.
In AutoCAD: VSCURRENT -> Realistic to see colours; CONVTOSOLID turns meshes into solids.
Usage: python make_prototype_3d.py out.dxf [preview.png|-] [web_page.html]"""
import sys
import math
import ezdxf
from ezdxf.math import Matrix44, Vec3
from ezdxf.render import MeshBuilder
from ezdxf.enums import TextEntityAlignment

OUT = sys.argv[1] if len(sys.argv) > 1 else "prototype_3d.dxf"

# colours sampled from the prototype photo (RGB)
C = dict(
    frame=(55, 59, 66), shred=(68, 71, 76), chamber=(28, 29, 32),
    blade=(178, 181, 185), shaft=(120, 122, 126), bin=(80, 83, 88),
    press=(62, 66, 72), platen=(140, 142, 146), heat=(196, 198, 200),
    pillar=(208, 210, 213), hyd=(30, 31, 34), res=(64, 66, 70),
    mould=(168, 170, 173), mould_in=(70, 72, 75), panel=(230, 230, 226),
    plate=(250, 250, 250), red=(205, 35, 35), green=(35, 155, 65),
    yellow=(245, 200, 0), display=(18, 18, 18), black=(25, 25, 25),
)
LAYER_COLOR = {"FRAME": "frame", "SHREDDER": "shred", "BLADES": "blade",
               "PRESS": "press", "HYDRAULIC": "hyd", "ELECTRICAL": "panel",
               "BIN_MOLD": "bin", "LABELS": "plate"}

doc = ezdxf.new("R2018", setup=True)
doc.units = ezdxf.units.MM
doc.header["$INSUNITS"] = 4
msp = doc.modelspace()
for name, key in LAYER_COLOR.items():
    doc.layers.add(name, true_color=ezdxf.rgb2int(C[key]))
doc.layers.add("TEXT", color=7)

MESHES = []   # (rgb, vertices, faces) - also used for the preview
PRIMS = []    # primitive list exported for the web viewer
PART = "frame"


def part(name):
    global PART
    PART = name


def add(layer, verts, faces, col=None, rec=True):
    key = col or LAYER_COLOR[layer]
    rgb = C[key]
    if rec:
        PRIMS.append({"t": "m", "v": [list(map(float, q)) for q in verts],
                      "f": [list(q) for q in faces], "c": key, "p": PART})
    mb = MeshBuilder()
    mb.add_mesh(vertices=verts, faces=faces)
    mesh = mb.render_mesh(msp, dxfattribs={"layer": layer})
    mesh.rgb = rgb
    MESHES.append((rgb, verts, faces))


def box(x1, y1, z1, x2, y2, z2, layer, col=None):
    v = [(x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1),
         (x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    add(layer, v, f, col, rec=False)
    PRIMS.append({"t": "b", "b": [x1, y1, z1, x2, y2, z2],
                  "c": col or LAYER_COLOR[layer], "p": PART})


def frustum(cx, cy, z1, z2, r1, r2, layer, axis="z", n=24, cap=True, col=None):
    """Round cylinder/cone. axis z: centre (cx,cy) z1..z2; axis x: centre (y=cx, z=cy)
    from x=z1..z2; axis y: centre (x=cx, z=cy) from y=z1..z2."""
    v = []
    for z, r in ((z1, r1), (z2, r2)):
        for i in range(n):
            a = 2 * math.pi * i / n
            u, w = cx + r * math.cos(a), cy + r * math.sin(a)
            v.append({"z": (u, w, z), "x": (z, u, w), "y": (u, z, w)}[axis])
    f = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    if cap:
        f.append(tuple(reversed(range(n))))
        f.append(tuple(range(n, 2 * n)))
    add(layer, v, f, col, rec=False)
    PRIMS.append({"t": "c", "a": axis, "cx": cx, "cy": cy, "z1": z1, "z2": z2, "r1": r1,
                  "r2": r2, "n": n, "cap": cap, "c": col or LAYER_COLOR[layer], "p": PART})


def tray(bot, top, z1, z2, layer, bottom=True, col=None):
    """Open-top tapered tray / hopper. bot/top = (x1,y1,x2,y2)."""
    def ring(r, z):
        x1, y1, x2, y2 = r
        return [(x1, y1, z), (x2, y1, z), (x2, y2, z), (x1, y2, z)]
    v = ring(bot, z1) + ring(top, z2)
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    if bottom:
        f.append((0, 3, 2, 1))
    add(layer, v, f, col, rec=False)
    PRIMS.append({"t": "m", "v": v, "f": [list(q) for q in f],
                  "c": col or LAYER_COLOR[layer], "p": PART})


def plate_text(s, origin, ux, uy, h, w, txt_h):
    """White name plate + black text on an arbitrary plane (ux right, uy up)."""
    o, ux, uy = Vec3(origin), Vec3(ux).normalize(), Vec3(uy).normalize()
    n = ux.cross(uy)
    p = [o - ux * w / 2 - uy * h / 2, o + ux * w / 2 - uy * h / 2,
         o + ux * w / 2 + uy * h / 2, o - ux * w / 2 + uy * h / 2]
    add("LABELS", [tuple(q + n * 1) for q in p], [(0, 1, 2, 3)], "plate", rec=False)
    PRIMS.append({"t": "label", "s": s, "o": list(o), "ux": list(ux), "uy": list(uy),
                  "h": h, "w": w, "th": txt_h, "p": PART})
    t = msp.add_text(s, height=txt_h, dxfattribs={"layer": "TEXT", "style": "OpenSans"})
    t.set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
    t.transform(Matrix44.ucs(ux, uy, n, o + n * 3))


T, TABLE, D = 60, 650, 700
STANDS = ((0, 800), (920, 1700))

# ---------------- frame ----------------
part("frame")
for x1, x2 in STANDS:
    for lx in (x1, x2 - T):
        for ly in (0, D - T):
            box(lx, ly, 10, lx + T, ly + T, TABLE, "FRAME")                  # legs
            box(lx - 20, ly - 20, 0, lx + T + 20, ly + T + 20, 10, "FRAME")  # feet
    for ly in (0, D - T):
        box(x1 + T, ly, TABLE - T, x2 - T, ly + T, TABLE, "FRAME")           # top rails
        box(x1 + T, ly, 290, x2 - T, ly + T, 330, "FRAME")                   # shelf rails
    for lx in (x1, x2 - T):
        box(lx, T, TABLE - T, lx + T, D - T, TABLE, "FRAME")                 # top cross
        box(lx, T, 200, lx + T, D - T, 260, "FRAME")                         # low cross
    for sy in (150, 550):
        box(x1 + T, sy - 20, 290, x2 - T, sy + 20, 330, "FRAME")             # shelf slats
for ly in (0, D - T):
    box(800, ly, 200, 920, ly + T, 260, "FRAME")                             # tie bar

# ---------------- shredder ----------------
part("housing")
Y1, Y2 = 100, 600
box(200, Y1, TABLE, 780, Y1 + 10, 690, "SHREDDER")      # front plate around window
box(200, Y1, 990, 780, Y1 + 10, 1030, "SHREDDER")
box(200, Y1, 690, 250, Y1 + 10, 990, "SHREDDER")
box(730, Y1, 690, 780, Y1 + 10, 990, "SHREDDER")
box(200, Y2 - 10, TABLE, 780, Y2, 1030, "SHREDDER")     # back plate
box(200, Y1, TABLE, 230, Y2, 1030, "SHREDDER")          # end plates
box(750, Y1, TABLE, 780, Y2, 1030, "SHREDDER")
box(230, 200, TABLE, 750, 500, 660, "SHREDDER", "chamber")   # dark chamber floor
for bx in (185, 795):                                    # bearing blocks
    for bz in (770, 880):
        box(bx - 15, 290, bz - 40, bx + 15, 410, bz + 40, "SHREDDER", "shaft")
part("cutters")
for sy, sz in ((300, 770), (400, 880)):                  # twin shafts + hook blades
    frustum(sy, sz, 170, 810, 20, 20, "BLADES", axis="x", n=12, col="shaft")
    for i in range(14):
        x0 = 250 + i * 480 / 14 + 3
        frustum(sy, sz, x0, x0 + 18, 70, 70, "BLADES", axis="x", n=8)
part("drive")
box(780, 330, 720, 900, 470, 920, "SHREDDER")            # gearbox
frustum(400, 820, 900, 1080, 70, 70, "SHREDDER", axis="x", n=20)   # motor
part("hopper")
box(230, 80, 1030, 750, 620, 1060, "SHREDDER")           # hopper collar
tray((250, 160, 730, 540), (100, 25, 880, 675), 1060, 1320, "SHREDDER", bottom=False)
# name plate on the sloped front face of the hopper
slope = Vec3(0, -135, 260)
plate_text("SHREDDING MACHINE", (490, 160 - 135 * (1245 - 1060) / 260, 1245),
           (1, 0, 0), slope, 60, 550, 30)
# discharge chute
part("chute")
add("SHREDDER",
    [(780, 300, 840), (960, 300, 720), (960, 420, 720), (780, 420, 840),
     (780, 300, 880), (960, 300, 760), (960, 420, 760), (780, 420, 880)],
    [(0, 1, 2, 3), (0, 1, 5, 4), (3, 2, 6, 7)])
# collection bin + handles
part("bin")
tray((240, 140, 720, 560), (230, 130, 730, 570), 330, 570, "BIN_MOLD")
box(218, 300, 470, 230, 400, 490, "BIN_MOLD", "black")
box(730, 300, 470, 742, 400, 490, "BIN_MOLD", "black")
# shredder control box
part("panels")
box(-20, -150, 660, 180, 0, 950, "ELECTRICAL")
add("ELECTRICAL", [(20, -151, 890), (50, -151, 890), (35, -151, 915)], [(0, 1, 2)], "yellow")
frustum(115, 895, -150, -170, 18, 18, "ELECTRICAL", axis="y", n=16, col="green")
frustum(115, 815, -150, -170, 18, 18, "ELECTRICAL", axis="y", n=16, col="red")
frustum(60, 740, -150, -155, 40, 40, "ELECTRICAL", axis="y", n=20, col="yellow")
box(52, -175, 712, 68, -155, 768, "ELECTRICAL", "red")   # isolator handle

# ---------------- heat press ----------------
part("lower_platen")
box(930, 50, TABLE, 1690, 650, 690, "PRESS")              # base plate
box(960, 50, 690, 1660, 650, 750, "PRESS", "platen")      # lower platen
part("upper_platen")
box(960, 50, 800, 1660, 650, 820, "PRESS", "heat")        # heat plate
box(960, 50, 820, 1660, 650, 900, "PRESS", "platen")      # upper platen
part("crown")
box(930, 50, 990, 1690, 650, 1090, "PRESS")               # crown
plate_text("HEAT PRESS MACHINE", (1310, 50, 1040), (1, 0, 0), (0, 0, 1), 50, 620, 28)
part("pillars")
for px in (980, 1640):
    for py in (100, 600):
        frustum(px, py, 690, 1090, 25, 25, "PRESS", n=16, col="pillar")
        frustum(px, py, 820, 900, 35, 35, "PRESS", n=16, col="shaft")
        frustum(px, py, 1090, 1110, 32, 32, "PRESS", n=6, col="pillar")
part("hydraulic")
frustum(1310, 350, 900, 925, 70, 70, "HYDRAULIC", col="pillar")   # ram flange
frustum(1310, 350, 925, 990, 40, 40, "HYDRAULIC", col="pillar")   # ram rod
frustum(1310, 350, 1090, 1255, 60, 60, "HYDRAULIC")               # cylinder
frustum(1310, 350, 1255, 1290, 70, 70, "HYDRAULIC")               # end cap
frustum(1310, 350, 1290, 1380, 25, 130, "HYDRAULIC", cap=False, col="res")
frustum(1310, 350, 1380, 1395, 130, 130, "HYDRAULIC", col="res")
hose = msp.add_spline([(1370, 350, 1200), (1450, 350, 1260), (1530, 300, 1180),
                       (1660, 250, 1100)], dxfattribs={"layer": "HYDRAULIC"})
hose.rgb = C["black"]
PRIMS.append({"t": "tube", "pts": [[1370, 350, 1200], [1450, 350, 1260], [1530, 300, 1180], [1660, 250, 1100]], "r": 12, "c": "black", "p": PART})
# mould tray
part("mould")
tray((1060, 120, 1520, 580), (970, 60, 1610, 640), 330, 600, "BIN_MOLD", col="mould")
for i in range(1, 12):
    x = 1060 + i * 460 / 12
    box(x - 4, 140, 335, x + 4, 560, 350, "BIN_MOLD", "mould_in")
# press control box
part("panels")
box(1730, -100, 790, 1980, 100, 1140, "ELECTRICAL")
box(1800, -110, 1040, 1910, -100, 1110, "ELECTRICAL", "display")
for txt, z, h, c in (("160°", 1085, 22, "red"), ("160°", 1055, 16, "green")):
    t = msp.add_text(txt, height=h, dxfattribs={"layer": "TEXT", "style": "OpenSans"})
    t.set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
    t.transform(Matrix44.ucs((1, 0, 0), (0, 0, 1), (0, -1, 0), (1855, -112, z)))
    t.rgb = C[c]
    PRIMS.append({"t": "led", "s": txt, "o": [1855, -112, z], "th": h, "c": c, "p": PART})
for i, c in enumerate(("red", "green", "red")):
    frustum(1790 + i * 65, 970, -100, -125, 17, 17, "ELECTRICAL", axis="y", n=16, col=c)
frustum(1855, 870, -100, -130, 25, 25, "ELECTRICAL", axis="y", n=16, col="black")
cable = msp.add_spline([(1760, 0, 790), (1740, 50, 720), (1700, 100, 690)],
                       dxfattribs={"layer": "ELECTRICAL"})
cable.rgb = C["black"]
PRIMS.append({"t": "tube", "pts": [[1760, 0, 790], [1740, 50, 720], [1700, 100, 690]], "r": 8, "c": "black", "p": PART})

# open in a SW isometric view
vp = doc.viewports.get("*Active")[0]
vp.dxf.direction = (-1, -1, 1)
vp.dxf.target = (1000, 350, 650)
vp.dxf.center = (0, 0)
vp.dxf.height = 2800
doc.saveas(OUT)
print("saved", OUT, len(MESHES), "meshes")

# ---- web viewer: inject the same primitives + colours into the HTML template ----
import json
import os
_here = os.path.dirname(os.path.abspath(__file__))
_tpl = os.path.join(_here, "viewer_template.html")
if os.path.exists(_tpl):
    data = json.dumps({"colors": {k: "#%02x%02x%02x" % v for k, v in C.items()},
                       "prims": PRIMS}, separators=(",", ":"))
    html = open(_tpl, encoding="utf-8").read().replace("/*MODEL_DATA*/null", data)
    # standalone file to double-click locally (full document)
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
    page = head + html.replace("<header", "</head>\n<body>\n<header", 1) + "\n</body>\n</html>\n"
    for name in ("prototype_3d_viewer.html", "index.html"):   # index.html = GitHub Pages entry
        open(os.path.join(_here, name), "w", encoding="utf-8").write(page)
    # body-only version used for the published web page
    if len(sys.argv) > 3:
        open(sys.argv[3], "w", encoding="utf-8").write(html)
    print("saved prototype_3d_viewer.html", len(PRIMS), "primitives")

if len(sys.argv) > 2 and sys.argv[2] != "-":      # optional shaded preview png
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    light = Vec3(-0.4, -0.7, 0.6).normalize()
    polys, cols = [], []
    for rgb, verts, faces in MESHES:
        for face in faces:
            pts = [Vec3(verts[i]) for i in face]
            nrm = (pts[1] - pts[0]).cross(pts[2] - pts[0])
            k = 0.55 + 0.45 * abs(nrm.normalize().dot(light)) if nrm.magnitude else 0.8
            polys.append([tuple(p) for p in pts])
            cols.append(tuple(min(1, c / 255 * k) for c in rgb))
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(polys, facecolors=cols,
                                         edgecolor=(0, 0, 0, 0.35), linewidths=0.25))
    ax.set_xlim(-100, 2000); ax.set_ylim(-500, 1200); ax.set_zlim(0, 1500)
    ax.set_box_aspect((2100, 1700, 1500))
    ax.view_init(elev=22, azim=-60)
    ax.set_axis_off()
    plt.savefig(sys.argv[2], dpi=110, bbox_inches="tight", facecolor="white")
