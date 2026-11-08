"""Generate a 2D AutoCAD DXF (front / top / right-side views) of the
shredding machine + heat press prototype. Units: millimetres.
Dimensions are estimated from the reference photo (~2.8 mm/px)."""
import sys
import math
import ezdxf
from ezdxf.enums import TextEntityAlignment

OUT = sys.argv[1]
COLOR = "--color" in sys.argv   # true-to-colour solid fills, black lines & text

# true colours sampled from the prototype photo (RGB)
C = dict(
    frame=(55, 59, 66), shred=(68, 71, 76), chamber=(28, 29, 32),
    blade=(178, 181, 185), shaft=(120, 122, 126), bin=(80, 83, 88),
    press=(62, 66, 72), platen=(140, 142, 146), heat=(196, 198, 200),
    pillar=(208, 210, 213), hyd=(30, 31, 34), res=(64, 66, 70),
    mould=(168, 170, 173), mould_in=(70, 72, 75), panel=(230, 230, 226),
    plate=(255, 255, 255), red=(205, 35, 35), green=(35, 155, 65),
    yellow=(245, 200, 0), display=(18, 18, 18), floor=(214, 212, 205),
    mplate=(204, 206, 209), rail=(160, 163, 168), mcb=(246, 246, 242),
    dev=(72, 76, 84), term=(96, 128, 170), sink=(185, 188, 192), black=(25, 25, 25),
)
LAYER_FILL = {"FRAME": "frame", "SHREDDER": "shred", "BLADES": "blade",
              "PRESS": "press", "HYDRAULIC": "hyd", "ELECTRICAL": "panel",
              "BIN_MOLD": "bin", "TEXT": "plate"}

doc = ezdxf.new("R2018", setup=True)
doc.units = ezdxf.units.MM
doc.header["$INSUNITS"] = 4
doc.header["$MEASUREMENT"] = 1
msp = doc.modelspace()

LAYERS = {
    "FRAME": 7,        # all layers black (color 7)
    "SHREDDER": 7,
    "BLADES": 7,
    "PRESS": 7,
    "HYDRAULIC": 7,
    "ELECTRICAL": 7,
    "BIN_MOLD": 7,
    "HIDDEN": 7,
    "CENTER": 7,
    "TEXT": 7,
    "DIMS": 7,
    "TITLE": 7,
    "BALLOON": 7,
}
for name, col in LAYERS.items():
    doc.layers.add(name, color=col)  # 7 = black on white paper / white on dark screen
doc.layers.add("FILL", color=7)
doc.layers.get("HIDDEN").dxf.linetype = "DASHED"
doc.layers.get("CENTER").dxf.linetype = "CENTER"

ds = doc.dimstyles.new("MM30")
ds.dxf.dimtxt = 30
ds.dxf.dimasz = 25
ds.dxf.dimexe = 15
ds.dxf.dimexo = 10
ds.dxf.dimgap = 8
ds.dxf.dimdec = 0
ds.dxf.dimclrd = 7
ds.dxf.dimclre = 7
ds.dxf.dimclrt = 7
doc.header["$LTSCALE"] = 20


def _fill(pts, layer, fill):
    """Solid true-colour hatch under an outline (colour mode only)."""
    if not COLOR or fill is False:
        return
    key = fill or LAYER_FILL.get(layer)
    if not key:
        return
    h = msp.add_hatch(dxfattribs={"layer": "FILL"})
    h.set_solid_fill(rgb=C[key])
    h.paths.add_polyline_path(pts, is_closed=True)


def rect(x1, y1, x2, y2, layer, ox=0, oy=0, fill=None):
    _fill([(x1 + ox, y1 + oy), (x2 + ox, y1 + oy), (x2 + ox, y2 + oy), (x1 + ox, y2 + oy)],
          layer, fill)
    msp.add_lwpolyline(
        [(x1 + ox, y1 + oy), (x2 + ox, y1 + oy), (x2 + ox, y2 + oy), (x1 + ox, y2 + oy)],
        close=True, dxfattribs={"layer": layer})


def poly(pts, layer, ox=0, oy=0, close=True, fill=None):
    if close:
        _fill([(x + ox, y + oy) for x, y in pts], layer, fill)
    msp.add_lwpolyline([(x + ox, y + oy) for x, y in pts], close=close,
                       dxfattribs={"layer": layer})


def line(x1, y1, x2, y2, layer, ox=0, oy=0):
    msp.add_line((x1 + ox, y1 + oy), (x2 + ox, y2 + oy), dxfattribs={"layer": layer})


def circle(cx, cy, r, layer, ox=0, oy=0, fill=None):
    _fill([(cx + ox + r * math.cos(a * math.pi / 24), cy + oy + r * math.sin(a * math.pi / 24))
           for a in range(48)], layer, fill)
    msp.add_circle((cx + ox, cy + oy), r, dxfattribs={"layer": layer})


def text(s, x, y, h=30, layer="TEXT", align=TextEntityAlignment.MIDDLE_CENTER, ox=0, oy=0):
    msp.add_text(s, height=h, dxfattribs={"layer": layer, "style": "OpenSans"}).set_placement(
        (x + ox, y + oy), align=align)


def hdim(x1, x2, y, base, ox=0, oy=0):
    msp.add_linear_dim(base=(x1 + ox, base + oy), p1=(x1 + ox, y + oy), p2=(x2 + ox, y + oy),
                       dimstyle="MM30", dxfattribs={"layer": "DIMS"}).render()


def vdim(y1, y2, x, base, ox=0, oy=0):
    msp.add_linear_dim(base=(base + ox, y1 + oy), p1=(x + ox, y1 + oy), p2=(x + ox, y2 + oy),
                       angle=90, dimstyle="MM30", dxfattribs={"layer": "DIMS"}).render()


T = 60          # square tube size
TABLE = 650     # table (top of frame) height
D = 700         # depth of both stands
S1, S2 = 0, 800        # shredder stand X extents
P1, P2 = 920, 1700     # press stand X extents

# =====================================================================
# FRONT VIEW  (origin = ground, left end of shredder stand)
# =====================================================================
FX, FY = 0, 0

def stand_front(x1, x2):
    rect(x1, 0, x1 + T, TABLE, "FRAME")                 # left leg
    rect(x2 - T, 0, x2, TABLE, "FRAME")                 # right leg
    rect(x1, TABLE - T, x2, TABLE, "FRAME")             # top rail
    rect(x1 + T, 290, x2 - T, 290 + 40, "FRAME")        # shelf rail
    rect(x1 - 20, 0, x1 + T + 20, 10, "FRAME")          # foot plates
    rect(x2 - T - 20, 0, x2 + 20, 10, "FRAME")

stand_front(S1, S2)
stand_front(P1, P2)
# lower stretcher tying both stands + middle legs
rect(S1 + T, 200, P2 - T, 200 + T, "FRAME")
rect(S2, 200, P1, 200 + T, "FRAME")

# ---------------- Shredder ----------------
# collection bin (sits on shelf rail)
rect(230, 330, 730, 570, "BIN_MOLD")
rect(220, 555, 740, 575, "BIN_MOLD")                    # rolled rim
for hx in (260, 700):                                   # side handles
    poly([(hx - 12, 400), (hx + 12, 400), (hx + 12, 500), (hx - 12, 500)], "BIN_MOLD")
rect(300, 430, 660, 470, "TEXT", fill="plate" if COLOR else False)
text("COLLECTION BIN", 480, 450, 28)

# cutting housing
rect(200, TABLE, 780, 1030, "SHREDDER")
rect(250, 690, 730, 990, "SHREDDER", fill="chamber")                    # cutting chamber opening
for bx in (215, 765):                                   # bearing blocks
    for by in (770, 880):
        rect(bx - 15, by - 35, bx + 15, by + 35, "SHREDDER")
# twin rotors with hook blades
for cy in (770, 880):
    line(250, cy, 730, cy, "CENTER")
    rect(250, cy - 20, 730, cy + 20, "BLADES", fill="shaft")          # shaft Ø40
    n = 14
    pitch = 480 / n
    for i in range(n):
        x0 = 250 + i * pitch + 3
        x1 = x0 + pitch * 0.55
        poly([(x0, cy - 55), (x1, cy - 55), (x1, cy + 40), (x1 + 10, cy + 60),
              (x0, cy + 55)], "BLADES")
rect(320, 993, 660, 1018, "TEXT", fill="plate" if COLOR else False)
text("TWIN-SHAFT CUTTERS", 490, 1005, 22)

# hopper
rect(230, 1030, 750, 1060, "SHREDDER")                  # collar
poly([(250, 1060), (730, 1060), (880, 1320), (100, 1320)], "SHREDDER")
rect(215, 1215, 765, 1275, "TEXT", fill="plate")
text("SHREDDING MACHINE", 490, 1245, 30)

# discharge chute to press
poly([(780, 840), (960, 720), (960, 690), (780, 800)], "SHREDDER")
line(780, 860, 960, 740, "SHREDDER")

# shredder control box
rect(-20, 660, 180, 950, "ELECTRICAL")
rect(-10, 670, 170, 940, "ELECTRICAL")
poly([(20, 890), (50, 890), (35, 915)], "ELECTRICAL", fill="yellow")   # warning sign
circle(115, 895, 18, "ELECTRICAL", fill="green"); text("ON", 115, 862, 14)
circle(115, 815, 18, "ELECTRICAL", fill="red"); text("OFF", 115, 782, 14)
circle(60, 740, 32, "ELECTRICAL", fill="yellow"); rect(52, 712, 68, 768, "ELECTRICAL", fill="red")  # isolator
text("MAIN SW", 60, 690, 14)

# ---------------- Heat press ----------------
rect(P1 + 10, TABLE, P2 - 10, 690, "PRESS")             # base plate
rect(960, 690, 1660, 750, "PRESS", fill="platen")                      # lower platen
rect(960, 800, 1660, 820, "PRESS", fill="heat")                      # upper heat plate
rect(960, 820, 1660, 900, "PRESS", fill="platen")                      # upper (moving) platen
for px in (980, 1640):                                  # guide pillars Ø50
    rect(px - 25, 690, px + 25, 990, "PRESS", fill="pillar")
    line(px, 670, px, 1110, "CENTER")
    rect(px - 35, 820, px + 35, 900, "PRESS", fill="shaft")           # guide bushings
    rect(px - 30, 1090, px + 30, 1110, "PRESS", fill="pillar")         # lock nuts
rect(P1 + 10, 990, P2 - 10, 1090, "PRESS")              # crown plate
rect(1000, 1015, 1620, 1065, "TEXT", fill="plate")
text("HEAT PRESS MACHINE", 1310, 1040, 28)
# hydraulic cylinder + ram
rect(1270, 900, 1350, 990, "HYDRAULIC", fill="pillar")                 # ram rod Ø80
rect(1240, 900, 1380, 925, "HYDRAULIC")                 # ram flange
rect(1250, 1090, 1370, 1260, "HYDRAULIC")               # cylinder Ø120
rect(1240, 1255, 1380, 1290, "HYDRAULIC")
line(1310, 880, 1310, 1400, "CENTER")
# oil reservoir / feed funnel on top
poly([(1290, 1290), (1330, 1290), (1440, 1380), (1180, 1380)], "HYDRAULIC", fill="res")
rect(1180, 1380, 1440, 1395, "HYDRAULIC", fill="res")
# hydraulic hose
msp.add_spline([(1380, 1200), (1450, 1250), (1520, 1180), (1560, 1100)],
               dxfattribs={"layer": "HYDRAULIC"})

# mould / tray under press
poly([(970, 600), (1610, 600), (1520, 320), (1060, 320)], "BIN_MOLD", fill="mould")
poly([(1010, 580), (1570, 580), (1490, 350), (1090, 350)], "BIN_MOLD", fill="mould_in")
for i in range(1, 12):
    y = 350 + i * (230 / 12)
    xl = 1090 - (1090 - 1010) * (y - 350) / 230
    xr = 1490 + (1570 - 1490) * (y - 350) / 230
    line(xl + 15, y, xr - 15, y, "BIN_MOLD")
text("MOULD TRAY", 1290, 280, 26)

# press control box
rect(1730, 790, 1980, 1140, "ELECTRICAL")
rect(1740, 800, 1970, 1130, "ELECTRICAL")
rect(1800, 1040, 1910, 1110, "ELECTRICAL", fill="display")             # temp. controller
for _t, _y, _h, _c in (("160°", 1085, 22, "red"), ("160°", 1055, 16, "green")):
    _e = msp.add_text(_t, height=_h, dxfattribs={"layer": "TEXT", "style": "OpenSans"})
    _e.set_placement((1855, _y), align=TextEntityAlignment.MIDDLE_CENTER)
    if COLOR:  # LED readout keeps its real colour (unreadable black-on-black otherwise)
        _e.rgb = C[_c]
for i, lbl in enumerate(("STOP", "START", "HEAT")):
    cx = 1790 + i * 65
    circle(cx, 970, 17, "ELECTRICAL", fill=("red", "green", "red")[i]); text(lbl, cx, 935, 13)
circle(1855, 870, 25, "ELECTRICAL", fill="hyd"); line(1855, 850, 1855, 890, "ELECTRICAL")
text("MODE", 1855, 828, 13)
msp.add_spline([(1760, 790), (1740, 720), (1700, 690)], dxfattribs={"layer": "ELECTRICAL"})

# front view dims
hdim(-20, 1980, 0, -150)
hdim(S1, S2, 0, -80)
hdim(P1, P2, 0, -80)
vdim(0, TABLE, S1, -150)
vdim(0, 1320, S1, -260)
vdim(0, 1395, 1980, 2120)
hdim(100, 880, 1320, 1420)
text("FRONT VIEW", 1000, -280, 50)

# =====================================================================
# TOP VIEW (third-angle: above the front view; front edge at bottom)
# =====================================================================
TX, TY = 0, 2100

def stand_top(x1, x2):
    rect(x1, 0, x2, D, "FRAME", TX, TY)
    rect(x1 + T, T, x2 - T, D - T, "FRAME", TX, TY, fill="floor")
    for lx, lz in ((x1, 0), (x2 - T, 0), (x1, D - T), (x2 - T, D - T)):
        rect(lx, lz, lx + T, lz + T, "FRAME", TX, TY)

stand_top(S1, S2)
stand_top(P1, P2)
rect(S2, 300, P1, 360, "HIDDEN", TX, TY)              # stretcher (hidden)
# shredder hopper (top 780 x 650, throat 480 x 380)
rect(100, 25, 880, 675, "SHREDDER", TX, TY)
rect(250, 160, 730, 540, "SHREDDER", TX, TY, fill="chamber")
for a, b in (((100, 25), (250, 160)), ((880, 25), (730, 160)),
             ((880, 675), (730, 540)), ((100, 675), (250, 540))):
    line(*a, *b, "SHREDDER", TX, TY)
for z in (300, 400):                                  # rotors seen through throat
    line(250, z, 730, z, "CENTER", TX, TY)
    for i in range(14):
        x0 = 250 + i * 480 / 14 + 3
        rect(x0, z - 45, x0 + 19, z + 45, "BLADES", TX, TY)
# drive motor + gearbox behind housing
rect(780, 380, 900, 480, "SHREDDER", TX, TY, fill="blade")
rect(900, 390, 900, 470, "SHREDDER", TX, TY)
text("GEARBOX", 840, 430, 18, ox=TX, oy=TY)
rect(-20, -150, 180, 0, "ELECTRICAL", TX, TY)         # control box
# press crown / platen, pillars, cylinder
rect(P1 + 10, 50, P2 - 10, 650, "PRESS", TX, TY)
for px in (980, 1640):
    for pz in (100, 600):
        circle(px, pz, 35, "PRESS", TX, TY, fill="shaft")
        circle(px, pz, 25, "PRESS", TX, TY, fill="pillar")
circle(1310, 350, 130, "HYDRAULIC", TX, TY, fill="res")           # reservoir rim
circle(1310, 350, 60, "HYDRAULIC", TX, TY)            # cylinder
line(1150, 350, 1470, 350, "CENTER", TX, TY)
line(1310, 190, 1310, 510, "CENTER", TX, TY)
poly([(780, 300), (960, 300), (960, 420), (780, 420)], "SHREDDER", TX, TY)  # chute
rect(1730, -40, 1980, 160, "ELECTRICAL", TX, TY)      # press control box

hdim(S1, P2, 0, -320, TX, TY)
vdim(0, D, P2, 1780 + 300, TX, TY)
vdim(25, 675, 100, -150, TX, TY)
text("TOP VIEW", 1000, 900, 50, ox=TX, oy=TY)

# =====================================================================
# RIGHT SIDE VIEW (third-angle: right of front view; front at left)
# =====================================================================
SX, SY = 2500, 0

rect(0, 0, T, TABLE, "FRAME", SX, SY)
rect(D - T, 0, D, TABLE, "FRAME", SX, SY)
rect(0, TABLE - T, D, TABLE, "FRAME", SX, SY)
rect(T, 290, D - T, 330, "FRAME", SX, SY)
rect(T, 200, D - T, 260, "FRAME", SX, SY)
rect(-20, 0, T + 20, 10, "FRAME", SX, SY)
rect(D - T - 20, 0, D + 20, 10, "FRAME", SX, SY)
# press stack
rect(50, TABLE, 650, 690, "PRESS", SX, SY)
rect(50, 690, 650, 750, "PRESS", SX, SY, fill="platen")
rect(50, 800, 650, 900, "PRESS", SX, SY, fill="platen")
rect(50, 800, 650, 820, "PRESS", SX, SY, fill="heat")
line(50, 820, 650, 820, "PRESS", SX, SY)
for pz in (100, 600):
    rect(pz - 25, 690, pz + 25, 990, "PRESS", SX, SY, fill="pillar")
    rect(pz - 35, 820, pz + 35, 900, "PRESS", SX, SY, fill="shaft")
    rect(pz - 30, 1090, pz + 30, 1110, "PRESS", SX, SY, fill="pillar")
    line(pz, 670, pz, 1110, "CENTER", SX, SY)
rect(50, 990, 650, 1090, "PRESS", SX, SY)
rect(310, 900, 390, 990, "HYDRAULIC", SX, SY, fill="pillar")
rect(290, 1090, 410, 1260, "HYDRAULIC", SX, SY)
rect(280, 1255, 420, 1290, "HYDRAULIC", SX, SY)
poly([(330, 1290), (370, 1290), (480, 1380), (220, 1380)], "HYDRAULIC", SX, SY, fill="res")
rect(220, 1380, 480, 1395, "HYDRAULIC", SX, SY, fill="res")
line(350, 880, 350, 1420, "CENTER", SX, SY)
# mould tray
poly([(60, 600), (640, 600), (580, 320), (120, 320)], "BIN_MOLD", SX, SY, fill="mould")
# press control box (on front-right corner)
rect(-40, 790, 160, 1140, "ELECTRICAL", SX, SY)
# shredder hopper visible behind (above press crown)
poly([(25, 1320), (675, 1320), (540, 1060)], "HIDDEN", SX, SY, close=False)
line(25, 1320, 160, 1060, "HIDDEN", SX, SY)

hdim(0, D, 0, -100, SX, SY)
vdim(0, 1395, D, 860, SX, SY)
vdim(690, 900, 0, -150, SX, SY)
text("RIGHT SIDE VIEW", 350, -280, 50, ox=SX, oy=SY)

# =====================================================================
# BALLOONS: numbered circle + straight leader with an arrowhead on the part
# =====================================================================
def balloon(label, bx, by, tx, ty, r=38, th=32):
    """Numbered balloon at (bx, by) pointing at the part at (tx, ty)."""
    circle(bx, by, r, "BALLOON", fill="plate")
    text(label, bx, by, th, "BALLOON")
    dx, dy = tx - bx, ty - by
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    al, aw = 40, 11                               # arrow length / half width
    sx, sy = bx + ux * r, by + uy * r             # leader starts on the circle edge
    ex, ey = tx - ux * al, ty - uy * al           # ...and ends at the arrow base
    line(sx, sy, ex, ey, "BALLOON")
    msp.add_solid([(tx, ty), (ex - uy * aw, ey + ux * aw), (ex + uy * aw, ey - ux * aw)],
                  dxfattribs={"layer": "BALLOON"})


# (number, balloon x, y, arrow tip x, y) - front view, plus the gearbox in the top view
for no, bx, by, tx, ty in (
    (1, -60, 1420, 135, 1290),       # hopper
    (2, -60, 1130, 330, 930),        # cutters
    (3, 860, 1170, 760, 1010),       # housing
    (4, 860, 600, 860, 768),         # chute
    (5, 860, 440, 730, 450),         # bin
    (6, 1550, 1600, 1365, 1180),     # hydraulic cylinder
    (7, 850, 1600, 950, 1040),       # crown
    (8, 1780, 1260, 1650, 960),      # pillars
    (9, 1050, 1600, 1100, 860),      # upper platen
    (10, 2050, 720, 1590, 720),      # lower platen
    (11, 2050, 480, 1584, 520),      # mould tray
    (12, -200, 800, -20, 800),       # shredder control panel
    (13, 2050, 1250, 1960, 1140),    # press control panel
    (14, -80, 450, 30, 450),         # frame
    (15, 860, TY - 180, 890, TY + 430),   # gearbox (top view)
):
    balloon(str(no), bx, by, tx, ty)

# =====================================================================
# CONTROL PANEL DETAILS (scale 1:10 = 2x the main views)
# =====================================================================
class Detail:
    """Draws in front-view coordinates, scaled k times and moved to (ox, oy)."""
    def __init__(self, x0, y0, ox, oy, k=2):
        self.x0, self.y0, self.ox, self.oy, self.k = x0, y0, ox, oy, k

    def P(self, x, y):
        return (self.ox + (x - self.x0) * self.k, self.oy + (y - self.y0) * self.k)

    def rect(self, x1, y1, x2, y2, layer="ELECTRICAL", fill=None):
        (a, b), (c, d) = self.P(x1, y1), self.P(x2, y2)
        rect(a, b, c, d, layer, fill=fill)

    def circle(self, cx, cy, r, layer="ELECTRICAL", fill=None):
        circle(*self.P(cx, cy), r * self.k, layer, fill=fill)

    def poly(self, pts, layer="ELECTRICAL", fill=None):
        poly([self.P(*q) for q in pts], layer, fill=fill)

    def line(self, x1, y1, x2, y2, layer="ELECTRICAL"):
        line(*self.P(x1, y1), *self.P(x2, y2), layer)

    def text(self, s, x, y, h, layer="TEXT"):
        text(s, *self.P(x, y), h * self.k, layer)

    def callouts(self, items, bx, bx_left=None, gap=95):
        """items = [(label, tx, ty[, side[, by]])] in local coords. Balloons sit in a column at
        model x = bx (side "R") or bx_left (side "L"), kept at least `gap` apart vertically,
        each with a straight leader + arrow. `by` forces a local balloon height."""
        for side, col in (("R", bx), ("L", bx_left)):
            pts = []
            for it in items:
                lab, tx, ty = it[:3]
                if (it[3] if len(it) > 3 else "R") != side:
                    continue
                by = self.P(0, it[4])[1] if len(it) > 4 else self.P(tx, ty)[1]
                pts.append((by, lab, *self.P(tx, ty)))
            pts.sort()
            last = None
            for by, lab, tx, ty in pts:
                by = by if last is None else max(by, last + gap)
                balloon(lab, col, by, tx, ty, r=36, th=24)
                last = by


def din_rail(d, x1, x2, y):
    d.rect(x1, y - 17, x2, y + 17, fill="rail")
    d.line(x1, y - 9, x2, y - 9)
    d.line(x1, y + 9, x2, y + 9)


def terminals(d, x, y1, y2, n, w=12, gap=2):
    for i in range(n):
        d.rect(x + i * (w + gap), y1, x + i * (w + gap) + w, y2, fill="term" if i % 4 else "mcb")


# ---------- Detail A: shredder control panel (part 12) ----------
A1 = Detail(-20, 660, 3900, 2050)          # door (as seen from the front)
A1.rect(-20, 660, 180, 950)
A1.rect(-10, 670, 170, 940)
for hy in (700, 905):                      # hinges, left edge
    A1.rect(-26, hy, -20, hy + 30, fill="shaft")
A1.rect(160, 790, 172, 830, fill="hyd")    # door lock
A1.poly([(20, 890), (50, 890), (35, 915)], fill="yellow")
A1.circle(115, 895, 18, fill="green"); A1.text("ON", 115, 862, 7)
A1.circle(115, 815, 18, fill="red"); A1.text("OFF", 115, 782, 7)
A1.circle(60, 740, 32, fill="yellow"); A1.rect(52, 712, 68, 768, fill="red")
A1.text("MAIN SW", 60, 694, 7)
A1.callouts([("C1", 60, 740), ("C2", 133, 895), ("C3", 133, 815), ("C4", 42, 905)], 4380)
text("DETAIL A - PANEL 12 DOOR", 4100, 2700, 30)

A2 = Detail(-20, 660, 4600, 2050)          # inside, door removed
A2.rect(-20, 660, 180, 950)
A2.rect(-10, 670, 170, 940, fill="mplate")
din_rail(A2, -5, 165, 880)
A2.rect(5, 835, 41, 925, fill="mcb"); A2.rect(17, 872, 29, 890, fill="black")       # MCB
A2.rect(60, 855, 110, 925, fill="dev"); A2.rect(75, 900, 95, 915, fill="mcb")      # contactor
A2.rect(62, 800, 108, 853, fill="dev"); A2.circle(85, 825, 7, fill="red")         # overload
din_rail(A2, -5, 165, 720)
terminals(A2, 10, 695, 745, 10)
for gx in (20, 70, 120):                   # cable glands under the box
    A2.rect(gx, 645, gx + 24, 660, fill="black")
A2.callouts([("C5", 5, 880, "L"), ("C6", 110, 905), ("C7", 108, 820), ("C8", 120, 720),
             ("C9", 132, 652)], 5080, 4510)
text("DETAIL A - PANEL 12 INSIDE", 4800, 2700, 30)

# ---------- Detail B: heat press control panel (part 13) ----------
B1 = Detail(1730, 790, 3900, 1150)
B1.rect(1730, 790, 1980, 1140)
B1.rect(1740, 800, 1970, 1130)
for hy in (830, 1070):                     # hinges, right edge
    B1.rect(1980, hy, 1986, hy + 30, fill="shaft")
B1.rect(1738, 940, 1750, 990, fill="hyd")  # door lock
B1.rect(1800, 1040, 1910, 1110, fill="display")
for _t, _y, _h, _c in (("160°", 1085, 22, "red"), ("160°", 1055, 16, "green")):
    _e = msp.add_text(_t, height=_h * 2, dxfattribs={"layer": "TEXT", "style": "OpenSans"})
    _e.set_placement(B1.P(1855, _y), align=TextEntityAlignment.MIDDLE_CENTER)
    if COLOR:
        _e.rgb = C[_c]
for i, (lbl, col) in enumerate((("STOP", "red"), ("START", "green"), ("HEAT", "red"))):
    B1.circle(1790 + i * 65, 970, 17, fill=col); B1.text(lbl, 1790 + i * 65, 937, 6.5)
B1.circle(1855, 870, 25, fill="hyd"); B1.line(1855, 850, 1855, 890)
B1.text("MODE", 1855, 828, 6.5)
B1.callouts([("C10", 1910, 1075), ("C11", 1773, 970, "L"), ("C12", 1855, 987, "L"),
             ("C13", 1937, 970), ("C14", 1880, 870)], 4480, 3830)
text("DETAIL B - PANEL 13 DOOR", 4150, 1910, 30)

B2 = Detail(1730, 790, 4700, 1150)
B2.rect(1730, 790, 1980, 1140)
B2.rect(1740, 800, 1970, 1130, fill="mplate")
din_rail(B2, 1745, 1862, 1055)
B2.rect(1755, 1010, 1791, 1100, fill="mcb"); B2.rect(1767, 1047, 1779, 1065, fill="black")   # MCB
B2.rect(1805, 1015, 1855, 1095, fill="dev"); B2.rect(1820, 1070, 1840, 1085, fill="mcb")    # contactor
B2.rect(1870, 990, 1960, 1115, fill="sink")                # heat sink with fins
for fx in range(1878, 1960, 10):
    B2.line(fx, 990, fx, 1115)
B2.rect(1885, 1020, 1945, 1085, fill="dev"); B2.text("SSR", 1915, 1052, 9, "TEXT")
din_rail(B2, 1745, 1965, 845)
terminals(B2, 1755, 820, 870, 14)
for gx in (1750, 1800, 1850):
    B2.rect(gx, 775, gx + 24, 790, fill="black")
B2.callouts([("C15", 1945, 1050), ("C16", 1830, 1015, "L", 960), ("C17", 1755, 1060, "L"),
             ("C18", 1950, 845), ("C19", 1874, 782)], 5280, 4620)
text("DETAIL B - PANEL 13 INSIDE", 4950, 1910, 30)

# ---------- component list ----------
COMPONENTS = [
    ("C1", "Main isolator switch, rotary, lockable", "12 / door"),
    ("C2", "ON push button, green (start shredder)", "12 / door"),
    ("C3", "OFF push button, red (stop shredder)", "12 / door"),
    ("C4", "Electrical hazard warning label", "12 / door"),
    ("C5", "Circuit breaker (MCB), motor supply", "12 / inside *"),
    ("C6", "Shredder motor contactor", "12 / inside *"),
    ("C7", "Thermal overload relay", "12 / inside *"),
    ("C8", "Terminal block on DIN rail", "12 / inside *"),
    ("C9", "Cable glands (power in, motor out)", "12 / bottom *"),
    ("C10", "Temperature controller (PID, 160 °C)", "13 / door"),
    ("C11", "STOP push button, red", "13 / door"),
    ("C12", "START push button, green", "13 / door"),
    ("C13", "HEAT push button / lamp, red", "13 / door"),
    ("C14", "MODE selector switch", "13 / door"),
    ("C15", "Solid-state relay (SSR) on heat sink", "13 / inside *"),
    ("C16", "Hydraulic pump contactor", "13 / inside *"),
    ("C17", "Circuit breaker (MCB)", "13 / inside *"),
    ("C18", "Terminal block on DIN rail", "13 / inside *"),
    ("C19", "Cable glands (power, heaters, thermocouple)", "13 / bottom *"),
]


def table(x0, ytop, title, header, rows, widths, rowh=40, th=22):
    text(title, x0 + sum(widths) / 2, ytop + 40, 36, "TITLE")
    for r, row in enumerate([header] + rows):
        y = ytop - (r + 1) * rowh
        cx = x0
        for c, cell in enumerate(row):
            rect(cx, y, cx + widths[c], y + rowh, "TITLE")
            text(cell, cx + 12, y + rowh / 2, th, "TITLE", TextEntityAlignment.MIDDLE_LEFT)
            cx += widths[c]
    return ytop - (len(rows) + 1) * rowh


yb = table(3900, 1000, "CONTROL PANEL COMPONENTS", ("NO.", "DESCRIPTION", "PANEL / WHERE"),
           [list(c) for c in COMPONENTS], [100, 720, 300])
text("* INSIDE PARTS ARE TYPICAL WIRING, NOT VISIBLE IN THE PHOTO - CONFIRM ON THE MACHINE.",
     3900, yb - 40, 20, "TEXT", TextEntityAlignment.MIDDLE_LEFT)

# =====================================================================
# NOTES, PARTS LIST & TITLE BLOCK
# =====================================================================
NX, NY = 2400, 1900
parts = [
    ("1", "Shredder hopper", "MS sheet 3 mm"),
    ("2", "Twin-shaft cutter (2x14 hook blades)", "Tool steel"),
    ("3", "Shredder housing / chamber", "MS plate 6 mm"),
    ("4", "Discharge chute", "MS sheet 2 mm"),
    ("5", "Collection bin", "MS sheet 2 mm"),
    ("6", "Hydraulic cylinder + ram + oil tank", "Ø120 / Ø80"),
    ("7", "Crown plate", "MS plate 25 mm"),
    ("8", "Guide pillars (4x)", "Ø50 C45 shaft"),
    ("9", "Upper heated platen", "Al / MS w/ heaters"),
    ("10", "Lower platen", "MS plate 20 mm"),
    ("11", "Mould tray", "MS sheet 3 mm"),
    ("12", "Shredder control panel (detail A)", "IP54, C1-C9"),
    ("13", "Heat press control panel (detail B)", "IP54, C10-C19"),
    ("14", "Support frame", "60x60x3 SHS"),
    ("15", "Gearbox + motor (assumed)", "Behind housing"),
]
table(NX, NY + (len(parts) + 1) * 45, "PARTS LIST", ("NO.", "DESCRIPTION", "MATERIAL / SPEC"),
      [list(p) for p in parts], [90, 700, 450], rowh=45, th=24)

notes = ("NOTES:\\P"
         "1. ALL DIMENSIONS IN MILLIMETRES.\\P"
         "2. DIMENSIONS ESTIMATED FROM PHOTO - VERIFY BEFORE FABRICATION.\\P"
         "3. FRAME: 60x60x3 SQUARE HOLLOW SECTION, WELDED, PAINTED DARK GREY.\\P"
         "4. PLATEN WORKING TEMP. 160°C (SET ON TEMP. CONTROLLER).\\P"
         "5. BALLOONS = PARTS LIST NO.; C1-C19 = PANEL COMPONENTS.")
msp.add_mtext(notes, dxfattribs={"layer": "TEXT", "char_height": 24,
                                 "insert": (NX, NY - 60), "width": 1250})

# title block
BX, BY, BW, BH = 4000, -690, 1300, 260
rect(BX, BY, BX + BW, BY + BH, "TITLE")
line(BX, BY + 130, BX + BW, BY + 130, "TITLE")
line(BX + 800, BY, BX + 800, BY + 130, "TITLE")
text("PLASTIC SHREDDER & HEAT PRESS PROTOTYPE", BX + BW / 2, BY + 195, 32, "TITLE")
text("GA - 3 VIEWS + PANEL DETAILS", BX + 400, BY + 85, 30, "TITLE")
text("DRAWN: 2026-11-08", BX + 400, BY + 40, 24, "TITLE")
text("UNITS: mm", BX + 1050, BY + 85, 26, "TITLE")
text("1:20 / DETAILS 1:10", BX + 1050, BY + 40, 24, "TITLE")

# drawing border around everything
rect(-500, -740, 5400, 3150, "TITLE")

doc.set_modelspace_vport(height=4000, center=(2450, 1205))
doc.saveas(OUT)
print("saved", OUT)
