"""Enclosures for every build (CadQuery), in millimetres.

Each build has:
  assembly()  -> [(solid, colour, gloss)] for the product render
  parts()     -> {name: solid} printable parts for STEP/STL export
Print in PETG, 0.2 mm layers. Wall thickness 2 mm unless noted.
"""
import math
import cadquery as cq

SHELL = "#eef1f1"      # body
SHELL2 = "#dfe5e6"     # second body tone
TEAL = "#0b6e7a"
GLASS = "#1d2a30"      # display window
RUBBER = "#3a474d"
STRAP = "#47555b"
CARD = "#d8c9a8"       # cardboard mouthpiece
STEEL = "#b9c3c6"


def rbox(L, W, H, r=6, top=1.5):
    b = cq.Workplane("XY").box(L, W, H).edges("|Z").fillet(r)
    return b.faces(">Z").edges().fillet(top) if top else b


def hollow(solid, wall=2.0, openface=">Z"):
    try:
        out = solid.faces(openface).shell(-wall)
        if out.val().isValid():
            return out
    except Exception:
        pass
    # Fallback for shapes the kernel cannot offset: remove an inner pocket
    bb = solid.val().BoundingBox()
    sgn = 1 if openface.startswith(">") else -1
    pocket = (cq.Workplane("XY").box(bb.xlen - 2 * wall, bb.ylen - 2 * wall, bb.zlen)
              .edges("|Z").fillet(min(bb.xlen, bb.ylen) / 2 - wall - 0.5 if min(bb.xlen, bb.ylen) < 30 else 6)
              .translate((bb.center.x, bb.center.y, bb.center.z + sgn * wall)))
    return solid.cut(pocket)


def window(w, h, depth=0.6):
    return cq.Workplane("XY").box(w, h, depth).edges("|Z").fillet(1.5)


def button(d=7, h=1.6):
    return cq.Workplane("XY").cylinder(h, d / 2).faces(">Z").edges().fillet(0.6)


def usb_cut(solid, x, z, axis="X"):
    c = cq.Workplane("YZ").rect(9.4, 3.6).extrude(8).edges("|X").fillet(1.4).translate((x - 4, 0, z))
    return solid.cut(c)


# ------------------------------------------------------------------ breath counter
def breath_counter():
    L, W, H = 66, 48, 15
    body = rbox(L, W, H, r=14, top=0).edges("<Z").fillet(3)
    dome = cq.Workplane("XY").box(L, W, 6).edges("|Z").fillet(14).faces(">Z").edges().fillet(5).translate((0, 0, H / 2 + 3))
    shell = body.union(dome)
    shell = usb_cut(shell, -L / 2, -H / 2 + 6)
    lugs = []
    for s in (-1, 1):
        lug = cq.Workplane("XY").box(10, 34, 4).edges("|Z").fillet(2).translate((s * (L / 2 + 3), 0, -H / 2 + 3))
        lug = lug.cut(cq.Workplane("XY").box(4, 26, 10).translate((s * (L / 2 + 4), 0, -H / 2 + 3)))
        shell = shell.union(lug)
    strap = []
    for s in (-1, 1):
        band = (cq.Workplane("XZ").center(s * (L / 2 + 4), -H / 2 + 2).rect(1.6, 1.0).extrude(-26 / 2)
                .union(cq.Workplane("XZ").center(s * (L / 2 + 4), -H / 2 + 2).rect(1.6, 1.0).extrude(26 / 2)))
        band = cq.Workplane("XY").box(46, 24, 1.4).translate((s * (L / 2 + 26), 0, -H / 2 + 1.2))
        strap.append(band)
    win = window(30, 16).translate((-9, 4, H / 2 + 6))
    b1 = button(9, 2).translate((20, 9, H / 2 + 6))
    b2 = button(9, 2).translate((20, -10, H / 2 + 6))
    asm = [(shell, SHELL, 0.25), (win, GLASS, 0.6), (b1, TEAL, 0.2), (b2, TEAL, 0.2)] + [(s, STRAP, 0.05) for s in strap]
    base = hollow(body, 2.0)
    lid = dome.cut(win.translate((0, 0, -0.1))).cut(cq.Workplane("XY").cylinder(20, 3.4).translate((20, 9, 0))).cut(cq.Workplane("XY").cylinder(20, 3.4).translate((20, -10, 0)))
    return asm, {"base": usb_cut(base, -L / 2, -H / 2 + 6), "lid": lid}


# ------------------------------------------------------------------ jaundice meter
def jaundice_meter():
    L, D = 128, 30
    body = cq.Workplane("YZ").ellipse(D / 2, D / 2 * 0.82).extrude(L).translate((-L / 2, 0, 0)).edges().fillet(9)
    nose = (cq.Workplane("YZ").workplane(offset=-L / 2 + 2).ellipse(D / 2 * 0.9, D / 2 * 0.74)
            .workplane(offset=-26).circle(6.5).loft())
    collar = cq.Workplane("YZ").workplane(offset=-L / 2 - 30).circle(7.6).extrude(7).edges().fillet(1.2)
    tip = cq.Workplane("YZ").workplane(offset=-L / 2 - 31).circle(3.2).extrude(2)
    flat = cq.Workplane("XY").box(60, 18, 4).edges("|Z").fillet(4).translate((14, 0, D / 2 * 0.82 - 1.2))
    shell = body.union(nose).union(flat)
    shell = usb_cut(shell, L / 2 + 4, 0) if False else shell
    win = window(30, 13).translate((22, 0, D / 2 * 0.82 + 1.0))
    b = button(8, 2).translate((-6, 0, D / 2 * 0.82 + 1.2))
    cap = (cq.Workplane("YZ").circle(9.6).extrude(18).faces("<X").edges().fillet(2)
           .translate((-L / 2 - 52, -30, -6)))
    asm = [(shell, SHELL, 0.3), (collar, TEAL, 0.15), (tip, GLASS, 0.5), (win, GLASS, 0.6), (b, TEAL, 0.2), (cap, SHELL2, 0.2)]
    top_half = shell.intersect(cq.Workplane("XY").box(300, 60, 40).translate((0, 0, 20)))
    bottom_half = shell.intersect(cq.Workplane("XY").box(300, 60, 40).translate((0, 0, -20)))
    return asm, {"body-lower": hollow(bottom_half, 2.0, ">Z"), "body-upper": hollow(top_half, 2.0, "<Z"),
                 "probe-collar": collar, "reference-cap": cap}


# ------------------------------------------------------------------ capillary refill timer
def capillary_refill_timer():
    L, W, H = 86, 52, 22
    base = rbox(L, W, H, r=10, top=2)
    slope = (cq.Workplane("XZ").polyline([(L / 2 - 24, H / 2), (L / 2, H / 2 - 9), (L / 2, H / 2), ]).close()
             .extrude(W / 2, both=True))
    base = base.cut(slope)
    trough = cq.Workplane("YZ").circle(10.5).extrude(L).translate((-L / 2, 0, H / 2 + 4.5))
    cradle = cq.Workplane("XY").box(58, 30, 9).edges("|X").fillet(4).translate((-10, 0, H / 2 + 4.5)).cut(trough)
    shell = base.union(cradle)
    pad = cq.Workplane("XY").cylinder(1.2, 6).translate((-10, 0, H / 2 - 1.2 + 4.6 - 10.4 + 6.5))
    arch = (cq.Workplane("YZ").rect(36, 34).extrude(14).edges("|X").fillet(5).translate((-17, 0, H / 2 + 17))
            .cut(cq.Workplane("YZ").rect(24, 30).extrude(20).edges("|X").fillet(3).translate((-20, 0, H / 2 + 12))))
    plunger = cq.Workplane("XY").cylinder(16, 4).translate((-10, 0, H / 2 + 38)).union(
        cq.Workplane("XY").cylinder(5, 9).edges(">Z").fillet(2).translate((-10, 0, H / 2 + 48)))
    win = (cq.Workplane("XY").box(20, 30, 0.6).edges("|Z").fillet(1.5)
           .rotate((0, 0, 0), (0, 1, 0), -20.5).translate((L / 2 - 12, 0, H / 2 - 4.2)))
    asm = [(shell, SHELL, 0.25), (arch, SHELL2, 0.2), (plunger, TEAL, 0.25), (pad, GLASS, 0.5), (win, GLASS, 0.6)]
    return asm, {"base": hollow(base, 2.0, "<Z"), "cradle": cradle, "arch": arch, "plunger": plunger}


# ------------------------------------------------------------------ freezing-of-gait anklet
def freezing_of_gait_anklet():
    R_in, T, H, sweep = 48, 15, 42, 78

    def sector(r1, r2, a_from, a_to, h):
        p = lambda r, a: (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
        am = (a_from + a_to) / 2
        return (cq.Workplane("XY").moveTo(*p(r2, a_from)).threePointArc(p(r2, am), p(r2, a_to))
                .lineTo(*p(r1, a_to)).threePointArc(p(r1, am), p(r1, a_from)).close()
                .extrude(h).translate((0, 0, -h / 2)))
    pod = sector(R_in, R_in + T, 90 - sweep / 2, 90 + sweep / 2, H)
    pod = pod.edges("|Z").fillet(5).faces(">Z or <Z").edges().fillet(3)
    band = sector(R_in - 0.2, R_in + 2.2, -40, 220, 30)
    btn = (cq.Workplane("XZ").circle(5).extrude(-2).translate((0, R_in + T + 1.5, 9)).edges().fillet(0.6))
    led = cq.Workplane("XZ").circle(1.4).extrude(-0.8).translate((0, R_in + T + 0.6, -10))
    rot = lambda w: w.rotate((0, 0, 0), (0, 0, 1), 200)
    asm = [(rot(pod), SHELL, 0.3), (rot(band), STRAP, 0.05), (rot(btn), TEAL, 0.2), (rot(led), TEAL, 0.5)]
    return asm, {"pod": hollow(pod, 2.0, ">Z")}


# ------------------------------------------------------------------ stroke rehab glove
def stroke_rehab_glove():
    pod = cq.Workplane("XY").ellipse(31, 23).extrude(12).edges().fillet(4)
    seat = cq.Workplane("XY").ellipse(40, 30).extrude(1.2).translate((0, 0, -1.2)).edges().fillet(0.5)
    strips, tips = [], []
    angles = [-58, -24, -8, 8, 24]
    lengths = [46, 70, 76, 70, 58]
    for i, (a, ln) in enumerate(zip(angles, lengths)):
        s = cq.Workplane("XY").box(ln, 6.5, 1.0).edges("|Z").fillet(2).translate((ln / 2 + 28, 0, 0.5))
        t = cq.Workplane("XY").box(6, 7.5, 1.4).edges("|Z").fillet(1.5).translate((ln + 26, 0, 0.7))
        strips.append(s.rotate((0, 0, 0), (0, 0, 1), a)); tips.append(t.rotate((0, 0, 0), (0, 0, 1), a))
    btn = button(8, 1.8).translate((-12, 0, 12.6))
    led = cq.Workplane("XY").cylinder(1, 1.6).translate((-12, 12, 12.2))
    vent = cq.Workplane("XY").box(16, 1.6, 0.6).translate((10, 0, 12.2))
    asm = [(seat, STRAP, 0.05), (pod, SHELL, 0.3), (btn, TEAL, 0.2), (led, TEAL, 0.5), (vent, GLASS, 0.1)] + \
          [(s, "#c9d3d5", 0.15) for s in strips] + [(t, TEAL, 0.1) for t in tips]
    return asm, {"pod": hollow(pod, 1.8, "<Z")}


# ------------------------------------------------------------------ anaemia screener
def anaemia_screener():
    L, W, Hh = 64, 36, 15
    lower = rbox(L, W, Hh, r=12, top=4).faces(">Z").edges().fillet(0.01) if False else \
        cq.Workplane("XY").box(L, W, Hh).edges("|Z").fillet(12).faces("<Z").edges().fillet(5)
    upper = cq.Workplane("XY").box(L, W, Hh).edges("|Z").fillet(12).faces(">Z").edges().fillet(5)
    groove = cq.Workplane("YZ").circle(9.5).extrude(L - 10).translate((-L / 2 - 1, 0, 0))
    lower = lower.cut(groove.translate((0, 0, Hh / 2)))
    upper = upper.cut(groove.translate((0, 0, -Hh / 2)))
    hinge = cq.Workplane("XZ").circle(4.5).extrude(W / 2 - 2, both=True).translate((L / 2 - 2, 0, Hh / 2))
    upper = upper.translate((0, 0, Hh + 1.5)).rotate((L / 2 - 2, 0, Hh / 2), (L / 2 - 2, 1, Hh / 2), 14)
    win = window(26, 13).translate((6, 0, Hh * 1.5 + 1.8)).rotate((L / 2 - 2, 0, Hh / 2), (L / 2 - 2, 1, Hh / 2), 14)
    pad = (cq.Workplane("YZ").circle(9.2).extrude(L - 14).translate((-L / 2 + 1, 0, Hh / 2 - 0.4))
           .intersect(cq.Workplane("XY").box(L, W, 4).translate((0, 0, Hh / 2 - 6))))
    btn = cq.Workplane("XZ").circle(4).extrude(-1.6).translate((-6, -W / 2 - 0.8, 0))
    asm = [(lower, SHELL, 0.3), (upper, SHELL, 0.3), (hinge, TEAL, 0.25), (win, GLASS, 0.6), (pad, RUBBER, 0.05), (btn, TEAL, 0.2)]
    return asm, {"lower": hollow(lower, 2.0, "<Z"), "upper": upper}


# ------------------------------------------------------------------ open spirometer
def open_spirometer():
    D, L = 34, 118
    tube = cq.Workplane("YZ").circle(D / 2).extrude(L).translate((-L / 2, 0, 0))
    tube = tube.cut(cq.Workplane("YZ").circle(D / 2 - 2).extrude(L + 2).translate((-L / 2 - 1, 0, 0)))
    flange = cq.Workplane("YZ").circle(D / 2 + 3).extrude(6).translate((-3, 0, 0)).cut(
        cq.Workplane("YZ").circle(D / 2 - 2).extrude(8).translate((-4, 0, 0)))
    mouth = (cq.Workplane("YZ").circle(D / 2 - 2.2).extrude(34).translate((-L / 2 - 30, 0, 0))
             .cut(cq.Workplane("YZ").circle(D / 2 - 3.2).extrude(40).translate((-L / 2 - 33, 0, 0))))
    grip = (cq.Workplane("XY").box(40, 32, 92).edges("|Z").fillet(10).edges("<Z").fillet(6)
            .rotate((0, 0, 0), (0, 1, 0), 10).translate((8, 0, -D / 2 - 40)))
    neck = cq.Workplane("XY").box(44, 30, 14).edges("|Z").fillet(8).translate((4, 0, -D / 2 + 2))
    taps = [cq.Workplane("XY").cylinder(9, 2.4).translate((x, 0, -D / 2 - 2)) for x in (-16, 14)]
    body = grip.union(neck)
    win = (window(26, 22).rotate((0, 0, 0), (0, 1, 0), -80).translate((-13.5, 0, -D / 2 - 26)))
    btn = cq.Workplane("YZ").circle(4.5).extrude(-2).translate((-13.6, 0, -D / 2 - 50))
    asm = [(tube, SHELL2, 0.3), (flange, TEAL, 0.2), (mouth, CARD, 0.02), (body, SHELL, 0.3), (win, GLASS, 0.6), (btn, TEAL, 0.2)] + [(t, STEEL, 0.4) for t in taps]
    return asm, {"flow-tube": tube, "mesh-flange": flange, "grip": hollow(grip, 2.0, ">Z")}


# ------------------------------------------------------------------ clubfoot brace sensor
def clubfoot_brace_sensor():
    D, H = 36, 11
    cap = cq.Workplane("XY").cylinder(H, D / 2).edges().fillet(4.2)
    ring = cq.Workplane("XY").cylinder(0.8, D / 2 - 4).translate((0, 0, H / 2 - 0.1)).cut(cq.Workplane("XY").cylinder(2, D / 2 - 5.2).translate((0, 0, H / 2)))
    btn = button(9, 1.6).translate((0, 0, H / 2 + 0.6))
    clip = (cq.Workplane("XY").box(12, 44, 2.4).edges("|Z").fillet(2.5).translate((0, 0, -H / 2 - 1.2))
            .union(cq.Workplane("XY").box(12, 2.4, 9).translate((0, 21, -H / 2 - 5.5)))
            .union(cq.Workplane("XY").box(12, 2.4, 9).translate((0, -21, -H / 2 - 5.5))))
    led = cq.Workplane("XY").cylinder(0.6, 1.2).translate((9, -7, H / 2 + 0.1))
    asm = [(cap, SHELL, 0.3), (ring, TEAL, 0.2), (btn, SHELL2, 0.25), (clip, RUBBER, 0.05), (led, TEAL, 0.5)]
    return asm, {"capsule": hollow(cap, 2.0, ">Z"), "clip": clip}


BUILDERS = {
    "breath-counter": breath_counter,
    "jaundice-meter": jaundice_meter,
    "capillary-refill-timer": capillary_refill_timer,
    "freezing-of-gait-anklet": freezing_of_gait_anklet,
    "stroke-rehab-glove": stroke_rehab_glove,
    "anaemia-screener": anaemia_screener,
    "open-spirometer": open_spirometer,
    "clubfoot-brace-sensor": clubfoot_brace_sensor,
}
