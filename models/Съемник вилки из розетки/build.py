# -*- coding: utf-8 -*-
# Съёмник вилки из розетки (Schuko: CEE 7/3 / CEE 7/4)
#
# ЧАСТЬ 1 — ДЕРЖАТЕЛЬ: плоский диск Ø70x5.
#   - отверстие Ø38 (проходит корпус вилки, держится за буртик Ø40);
#   - два зубца ВНУТРЬ от кромки отверстия (на ±90°), только нижние 2 мм;
#   - по бокам (3 и 9 часов) — цапфы-оси у верхнего края детали.
#
# ЧАСТЬ 2 — РЫЧАГ: плоская V-образная скоба вокруг диска.
#   - сверху ручка-лопатка с окном под палец;
#   - верхняя дуга r36…r46 несёт ступицы на цапфах;
#   - два плеча сходятся в V, внизу пятка с тремя выступами в стенку.
#   Печатается сразу надетой на цапфы (print-in-place).
#
# Все размеры — из таблицы "Параметры" (алиасы); литералов размеров в коде нет.
# Скрипт идемпотентный: пересоздаёт таблицу и оба тела.
#
# Запуск: exec(open(r"...\build.py", encoding="utf-8").read())

import math

import FreeCAD as App
import Part

DOC_NAME = "plug_puller"

doc = App.getDocument(DOC_NAME)
if doc is None:
    doc = App.newDocument(DOC_NAME)

# ------------------------------------------------------------------ параметры
sh = doc.getObject("Parameters")
if sh is not None:
    doc.removeObject(sh.Name)      # пересоздаём: иначе остаются старые alias
sh = doc.addObject("Spreadsheet::Sheet", "Parameters")
sh.Label = "Параметры"

sh.set("A1", "Параметр")
sh.set("B1", "Значение")
sh.set("C1", "Источник / смысл")

INPUTS = [
    # CEE 7/4 (вилка), CEE 7/3 (розетка)
    ("pin_diameter",             "4.8 mm",  "справочно: CEE 7/4, штырь"),
    ("pin_spacing",              "19 mm",   "справочно: CEE 7/4, расстояние штырей"),
    ("socket_recess_diameter",   "45 mm",   "справочно: CEE 7/3, стакан розетки"),
    ("socket_recess_depth",      "17.5 mm", "справочно: CEE 7/3, глубина стакана"),
    ("plug_body_diameter",       "35.5 mm", "справочно: CEE 7/4, корпус вилки"),
    ("earth_contact_offset",     "90 deg",  "справочно: CEE 7/4, боковые контакты"),
    # --- часть 1: держатель
    ("holder_diameter",          "70 mm",   "проект: диаметр диска"),
    ("holder_thickness",         "5 mm",    "проект: толщина детали"),
    ("plug_collar_diameter",     "40 mm",   "проект: буртик вилки (за него держим)"),
    ("holder_hole_diameter",     "38 mm",   "проект: отверстие диска"),
    ("tooth_depth",              "2 mm",    "проект: вылет зубца внутрь (просвет Ø34)"),
    ("tooth_height",             "2 mm",    "проект: высота зубца (не на всю толщину)"),
    ("tooth_width",              "3 mm",    "проект: ширина зубца"),
    ("print_clearance",          "0.45 mm", "проект: зазор в сопряжении с рычагом"),
    ("hinge_pin_diameter",       "4.5 mm",  "проект: диаметр цапфы-оси"),
    ("hinge_pin_length",         "7.5 mm",  "проект: вылет цапфы за кромку диска"),
    # --- часть 2: рычаг
    ("lever_thickness",          "5 mm",    "проект: толщина рычага (та же плоскость)"),
    ("lever_gap",                "1 mm",    "проект: зазор рычага по диску"),
    ("lever_arm_width",          "10 mm",   "проект: ширина плеча V"),
    ("lever_v_foot_y",           "50 mm",   "проект: от оси цапф вниз до верха пятки"),
    ("lever_foot_width",         "32 mm",   "проект: ширина пятки"),
    ("lever_foot_height",        "10 mm",   "проект: высота пятки"),
    ("lever_foot_mouth",         "12 mm",   "проект: просвет V у пятки"),
    ("lever_pad_count",          "3",       "проект: число выступов в стенку"),
    ("lever_pad_diameter",       "7 mm",    "проект: диаметр выступа"),
    ("lever_pad_spacing",        "9 mm",    "проект: шаг выступов"),
    ("lever_hub_diameter",       "10 mm",   "проект: диаметр ступицы (под цапфу)"),
    ("lever_hub_inset",          "0.5 mm",  "проект: ступица не доходит до кромок обода"),
    ("lever_handle_length",      "42 mm",   "проект: вылет ручки за обод"),
    ("lever_handle_width",       "42 mm",   "проект: ширина ручки"),
    ("lever_handle_corner_radius", "12 mm", "проект: скругление ручки"),
    ("lever_handle_hole_length", "22 mm",   "проект: окно под палец, длина"),
    ("lever_handle_hole_width",  "13 mm",   "проект: окно под палец, ширина"),
    ("lever_handle_hole_offset", "21 mm",   "проект: центр окна от торца ручки"),
    ("lever_handle_angle",       "15 deg",  "проект: подъём ручки над плоскостью"),
    ("lever_wall_angle",         "15 deg",  "проект: подъём пятки над плоскостью"),
    ("lever_bend_radius",        "5 mm",    "проект: радиус изгиба (по средней линии)"),
]

DERIVED = [
    ("holder_half",              "=holder_diameter / 2", ""),
    ("holder_hole_radius",       "=holder_hole_diameter / 2", ""),
    ("tooth_inner_diameter",     "=holder_hole_diameter - 2 * tooth_depth",
                                 "просвет по зубцам (должен быть >= корпуса вилки)"),
    ("hinge_height",             "=holder_thickness", "оси у верхнего края детали"),
    ("hinge_pin_end",            "=holder_half + hinge_pin_length", "наружный конец цапфы"),
    ("hinge_hook_diameter",      "=hinge_pin_diameter + 2 * print_clearance", "отверстие в рычаге"),
    ("lever_inner_diameter",     "=holder_diameter + 2 * lever_gap", "внутренний Ø рычага по диску"),
    ("lever_inner_radius",       "=lever_inner_diameter / 2", ""),
    ("lever_outer_radius",       "=lever_inner_radius + lever_arm_width", "наружный радиус рычага"),
    ("lever_outer_diameter",     "=lever_outer_radius * 2", ""),
    ("lever_hub_center_x",       "=lever_inner_radius + lever_arm_width / 2", "центр цапфы в плече"),
    ("lever_hub_length",         "=lever_arm_width - 2 * lever_hub_inset", ""),
    ("lever_handle_end",         "=lever_outer_radius + lever_handle_length", "конец ручки"),
    ("lever_handle_hole_center_y", "=lever_handle_end - lever_handle_hole_offset", "центр окна"),
    ("lever_bend_y",             "=lever_hub_diameter / 2", "линия излома — у ступицы, на оси"),
]

row = 2
for alias, value, comment in INPUTS:
    sh.set("A%d" % row, alias)
    sh.set("B%d" % row, value)
    sh.set("C%d" % row, comment)
    sh.setAlias("B%d" % row, alias)
    row += 1

for alias, formula, comment in DERIVED:
    sh.set("A%d" % row, alias)
    sh.set("B%d" % row, formula)
    sh.set("C%d" % row, comment)
    sh.setAlias("B%d" % row, alias)
    row += 1

doc.recompute()

# чистим тела прошлого запуска (таблица остаётся)
for obj in list(doc.Objects):
    try:
        if obj.TypeId != "Spreadsheet::Sheet":
            doc.removeObject(obj.Name)
    except Exception:
        pass


def V(alias):
    """Значение параметра во внутренних единицах (мм / градусы)."""
    return App.Units.Quantity(sh.get(alias)).Value


holder_r   = V("holder_half")
plate_t    = V("holder_thickness")
hole_r     = V("holder_hole_radius")
tooth_d    = V("tooth_depth")
tooth_h    = V("tooth_height")
tooth_w    = V("tooth_width")
hinge_h    = V("hinge_height")
pin_d      = V("hinge_pin_diameter")
pin_end    = V("hinge_pin_end")

# ------------------------------------------------------------------ утилиты
def box(x0, x1, y0_, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0_, z1 - z0, App.Vector(x0, y0_, z0))


def cyl(r, h, p, d=None):
    return Part.makeCylinder(r, h, p, d if d is not None else App.Vector(0, 0, 1))


def as_solid(shape, name):
    s = shape.removeSplitter()
    solids = s.Solids
    if len(solids) != 1:
        raise RuntimeError("%s: ожидался 1 солид, получено %d" % (name, len(solids)))
    return solids[0]


def arc(cx, cy, r, a0, a1):
    """Точки дуги (градусы), a0 -> a1."""
    n = max(3, int(abs(a1 - a0) / 2.0))
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / float(n))
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def prism_even(pts, name, z0, z1):
    """Призма по замкнутому полигону от z0 до z1."""
    clean = []
    for p in pts:
        if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-7:
            clean.append(p)
    if math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 1e-7:
        clean.pop()
    clean.append(clean[0])
    w = Part.makePolygon([App.Vector(p[0], p[1], 0.0) for p in clean])
    if not w.isClosed():
        raise RuntimeError("%s: контур не замкнут" % name)
    f = Part.Face(w)
    if f.isNull():
        raise RuntimeError("%s: грань не построена" % name)
    return f.extrude(App.Vector(0.0, 0.0, z1 - z0)).translate(App.Vector(0.0, 0.0, z0))


# ------------------------------------------------------------------ часть 1
# плоский диск
body = cyl(holder_r, plate_t, App.Vector(0.0, 0.0, 0.0))

# отверстие под корпус вилки
body = body.cut(cyl(hole_r, plate_t * 3.0, App.Vector(0.0, 0.0, -plate_t)))

# зубцы ВНУТРЬ от кромки отверстия, на +-90 гр., только нижние tooth_height
for sgn in (1, -1):
    x0 = sgn * (hole_r - tooth_d)
    x1 = sgn * (hole_r + plate_t)
    body = body.fuse(box(min(x0, x1), max(x0, x1),
                         -tooth_w / 2.0, tooth_w / 2.0,
                         0.0, tooth_h))

# цапфы-оси по бокам (3 и 9 часов), на уровне верхнего края
for sgn in (1, -1):
    d = App.Vector(float(sgn), 0.0, 0.0)
    body = body.fuse(cyl(pin_d / 2.0, pin_end - (holder_r - 2.0),
                         App.Vector(sgn * (holder_r - 2.0), 0.0, hinge_h), d))

holder_shape = as_solid(body, "Держатель")

# ---------------------------------------------------------------- часть 2: рычаг
lever_t  = V("lever_thickness")
ri       = V("lever_inner_radius")
ro       = V("lever_outer_radius")
y_foot   = V("lever_v_foot_y")
foot_x   = V("lever_foot_width") / 2.0
foot_h   = V("lever_foot_height")
mouth_x  = V("lever_foot_mouth") / 2.0
n_pad    = int(round(V("lever_pad_count")))
pad_r    = V("lever_pad_diameter") / 2.0
pad_s    = V("lever_pad_spacing")
hub_d    = V("lever_hub_diameter")
hub_l    = V("lever_hub_length")
hub_x    = V("lever_hub_center_x")
bore_d   = V("hinge_hook_diameter")
hw       = V("lever_handle_width")
hr       = V("lever_handle_corner_radius")
tip      = V("lever_handle_end")
hole_ry  = V("lever_handle_hole_length") / 2.0
hole_rx  = V("lever_handle_hole_width") / 2.0
hole_cy  = V("lever_handle_hole_center_y")

y_bot = y_foot + foot_h

# --- касание: внутренняя кромка плеча V выходит из окружности ri по касательной
dist  = math.hypot(mouth_x, y_foot)
a_end = math.atan2(-y_foot, mouth_x) + math.acos(ri / dist)      # рад, отрицательный
a_deg = math.degrees(a_end)
tx, ty = ri * math.cos(a_end), ri * math.sin(a_end)
ox, oy = ro * math.cos(a_end), ro * math.sin(a_end)
phi_h  = math.degrees(math.acos((hw / 2.0) / ro))

# наружный контур: пятка -> правое плечо -> обод -> ручка -> левое плечо -> пятка
outer = [(foot_x, -y_bot), (foot_x, -y_foot), (ox, oy)]
outer += arc(0.0, 0.0, ro, a_deg, phi_h)[1:]
outer.append((hw / 2.0, tip - hr))
outer += arc(hw / 2.0 - hr, tip - hr, hr, 0.0, 90.0)[1:]
outer += arc(-(hw / 2.0 - hr), tip - hr, hr, 90.0, 180.0)[1:]
outer.append((-hw / 2.0, ro * math.sin(math.radians(phi_h))))
outer += arc(0.0, 0.0, ro, 180.0 - phi_h, 180.0 - a_deg)[1:]
outer += [(-ox, oy), (-foot_x, -y_foot), (-foot_x, -y_bot)]
for i in range(n_pad):
    cx = (i - (n_pad - 1) / 2.0) * pad_s
    outer += arc(cx, -y_bot, pad_r, 180.0, 360.0)

lever = prism_even(outer, "наружный контур", 0.0, lever_t)

# просвет V (внутренняя кромка: дуга ri + два плеча + дно у пятки)
mouth = [(tx, ty)]
mouth += arc(0.0, 0.0, ri, a_deg, 180.0 - a_deg)[1:]
mouth += [(-mouth_x, -y_foot), (mouth_x, -y_foot)]
lever = lever.cut(prism_even(mouth, "просвет V", -lever_t, lever_t * 2.0))

# окно под палец
grip = [(hole_rx * math.cos(math.radians(a)), hole_cy + hole_ry * math.sin(math.radians(a)))
        for a in range(0, 360, 5)]
lever = lever.cut(prism_even(grip, "окно", -lever_t, lever_t * 2.0))

# ступицы (бобышки под цапфы) и отверстия под цапфы
for sgn in (1, -1):
    d = App.Vector(float(sgn), 0.0, 0.0)
    lever = lever.fuse(cyl(hub_d / 2.0, hub_l,
                           App.Vector(sgn * (hub_x - hub_l / 2.0), 0.0, hinge_h), d))
for sgn in (1, -1):
    d = App.Vector(float(-sgn), 0.0, 0.0)
    lever = lever.cut(cyl(bore_d / 2.0, hub_l + 2.0,
                          App.Vector(sgn * (hub_x + hub_l / 2.0 + 1.0), 0.0, hinge_h), d))

# изгиб: обе стороны вверх от оси цапф, радиусом (без щелей)
bend    = V("lever_bend_y")               # линия изгиба у ступицы
r_bend  = V("lever_bend_radius")          # радиус по средней линии
ang_h   = V("lever_handle_angle")         # градусы
ang_w   = V("lever_wall_angle")
z_mid   = lever_t / 2.0
z_c     = z_mid + r_bend                  # центр радиуса изгиба (над плитой)
big     = 10.0 * (ro + y_bot + tip)

# труба r = ri..ro — чтобы сектор изгиба совпал с кромками диска
ring = cyl(ro, big, App.Vector(0.0, 0.0, -big / 2.0)).cut(
       cyl(ri, big, App.Vector(0.0, 0.0, -big / 2.0)))


def bend_sector(y_line, angle, sgn):
    """Сектор изгиба: срез плиты, повёрнутый на angle вокруг центра радиуса."""
    pts = [App.Vector(-big, y_line, 0.0), App.Vector(big, y_line, 0.0),
           App.Vector(big, y_line, lever_t), App.Vector(-big, y_line, lever_t),
           App.Vector(-big, y_line, 0.0)]
    f = Part.Face(Part.makePolygon(pts))
    sec = f.revolve(App.Vector(0.0, y_line, z_c), App.Vector(1.0, 0.0, 0.0), sgn * angle)
    return sec.common(ring)


top = lever.common(box(-big, big, bend, big, -big, big))
mid = lever.common(box(-big, big, -bend, bend, -big, big))
bot = lever.common(box(-big, big, -big, -bend, -big, big))

top.rotate(App.Vector(0.0, bend, z_c), App.Vector(1.0, 0.0, 0.0), ang_h)
bot.rotate(App.Vector(0.0, -bend, z_c), App.Vector(1.0, 0.0, 0.0), -ang_w)

lever = top.fuse(mid).fuse(bot)
lever = lever.fuse(bend_sector(bend, ang_h, 1)).fuse(bend_sector(-bend, ang_w, -1))

lever_shape = as_solid(lever, "Рычаг")

# ------------------------------------------------------------------ документ
holder = doc.addObject("Part::Feature", "PlugHolder")
holder.Label = "Держатель вилки"
holder.Shape = holder_shape
holder.ViewObject.ShapeColor = (0.85, 0.70, 0.10)

lever_obj = doc.addObject("Part::Feature", "Lever")
lever_obj.Label = "Рычаг"
lever_obj.Shape = lever_shape
lever_obj.ViewObject.ShapeColor = (0.72, 0.72, 0.76)

doc.recompute()

# ------------------------------------------------------------------ отчёт
rep = []
rep.append("disc D%.1f x %.1f" % (2 * holder_r, plate_t))
rep.append("hole D%.2f, passage by teeth D%.2f"
           % (2 * hole_r, V("tooth_inner_diameter")))
rep.append("teeth: %.1f wide x %.1f deep, z 0..%.1f (inward, +-90 deg)"
           % (tooth_w, tooth_d, tooth_h))
rep.append("pins: D%.1f at z=%.2f (top edge), x %.1f..%.1f"
           % (pin_d, hinge_h, holder_r, pin_end))
rep.append("volume = %.0f mm3" % holder_shape.Volume)
try:
    chk = holder_shape.check(True)
except Exception as exc:
    chk = "BOP: %s" % exc
rep.append("valid = %s | check = %s" % (holder_shape.isValid(), chk))
rep.append("bbox = %s" % holder_shape.BoundBox)

rep.append("")
rep.append("lever: V mouth %.1f (at ri=%.1f) .. %.1f (at foot), tangent %.2f deg"
           % (2 * ri, ri, 2 * mouth_x, a_deg))
rep.append("lever: T=(%.2f, %.2f) O=(%.2f, %.2f)" % (tx, ty, ox, oy))
rep.append("lever: foot %.1f x %.1f, y -%.1f..-%.1f, pads %d x D%.1f/step %.1f"
           % (2 * foot_x, foot_h, y_foot, y_bot, n_pad, 2 * pad_r, pad_s))
rep.append("lever: handle %.1f x %.1f, tip y=%.1f, window %.1f x %.1f at y=%.1f"
           % (hw, V("lever_handle_length"), tip, 2 * hole_rx, 2 * hole_ry, hole_cy))
rep.append("lever: hub D%.1f x %.1f at x=+-%.1f, bore D%.2f"
           % (hub_d, hub_l, hub_x, bore_d))
rep.append("lever: bend y=+-%.1f at the hub, R%.1f, handle %+.0f / wall %+.0f deg (both up)"
           % (bend, r_bend, ang_h, ang_w))
rep.append("lever volume = %.0f mm3" % lever_shape.Volume)
try:
    lchk = lever_shape.check(True)
except Exception as exc:
    lchk = "BOP: %s" % exc
rep.append("lever valid = %s | check = %s" % (lever_shape.isValid(), lchk))
rep.append("lever bbox = %s" % lever_shape.BoundBox)
rep.append("common(holder, lever) = %.4f mm3" % holder_shape.common(lever_shape).Volume)
rep.append("min distance holder-lever = %.3f mm" % holder_shape.distToShape(lever_shape)[0])


def inside(p):
    return holder_shape.isInside(App.Vector(*p), 1e-6, True)


probes = [
    ("центр отверстия z=2.5",    (0.0, 0.0, 2.5), False),
    ("кольцо (0, 30, 2.5)",      (0.0, 30.0, 2.5), True),
    ("зубец +X (r=17.2, z=1)",   (17.2, 0.0, 1.0), True),
    ("над зубцом (r=17.2,z=3)",  (17.2, 0.0, 3.0), False),
    ("без зубца (r=17.2, y)",    (0.0, 17.2, 1.0), False),
    ("палец +X (x=41.5)",        (41.5, 0.0, hinge_h), True),
    ("палец -X (x=-41.5)",       (-41.5, 0.0, hinge_h), True),
    ("над пальцем",              (41.5, 0.0, hinge_h + pin_d / 2.0 + 0.5), False),
]
for name, p, expect in probes:
    got = inside(p)
    rep.append("probe %-26s %s -> %s %s" % (name, p, got, "OK" if got == expect else "!!"))

print("\n".join(rep))
