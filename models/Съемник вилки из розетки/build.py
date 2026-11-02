# -*- coding: utf-8 -*-
# Съёмник вилки из розетки (Schuko: CEE 7/3 / CEE 7/4)
# ЧАСТЬ 1 — ДЕРЖАТЕЛЬ: плоский диск Ø70x5.
#  - отверстие Ø38 (проходит корпус вилки, держится за буртик Ø40);
#  - два зубца ВНУТРЬ от кромки отверстия (на ±90°), только нижние 2 мм;
#  - по бокам (3 и 9 часов) — цапфы-оси у верхнего края детали.
# Скрипт идемпотентный: пересоздаёт Spreadsheet "Parameters" и все тела.
#
# Запуск: exec(open(r"...\build.py", encoding="utf-8").read())

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
    # --- часть 2
    ("lever_thickness",          "5 mm",    "проект: толщина рычага (та же плоскость)"),
    ("lever_gap",                "1 mm",    "проект: зазор рычага по диску"),
    ("lever_ring_width",         "8.4 mm",  "проект: ширина обода рычага"),
    ("lever_hub_diameter",       "10 mm",   "проект: диаметр ступицы рычага (под цапфу)"),
    ("lever_hub_length",         "10 mm",   "проект: длина ступицы по оси"),
    ("lever_hub_offset",         "6 mm",    "проект: смещение ступицы от кромки диска"),
    ("lever_handle_length",      "30 mm",   "проект: вылет ручки за обод"),
    ("lever_handle_width",       "40 mm",   "проект: ширина ручки"),
]

DERIVED = [
    ("holder_half",              "=holder_diameter / 2", ""),
    ("holder_hole_radius",       "=holder_hole_diameter / 2", ""),
    ("tooth_inner_diameter",     "=holder_hole_diameter - 2 * tooth_depth",
                                 "просвет по зубцам (должен быть >= корпуса вилки)"),
    ("hinge_height",             "=holder_thickness", "оси у верхнего края детали"),
    ("hinge_pin_end",            "=holder_half + hinge_pin_length", "наружный конец цапфы"),
    ("hinge_hook_diameter",      "=hinge_pin_diameter + 2 * print_clearance", "отверстие в рычаге"),
    ("lever_inner_diameter",     "=holder_diameter + 2 * lever_gap", "внутренний Ø обода рычага"),
    ("lever_outer_diameter",     "=lever_inner_diameter + 2 * lever_ring_width", "наружный Ø обода"),
    ("lever_hub_center_x",       "=holder_half + lever_hub_offset", "центр ступицы рычага"),
    ("lever_handle_end",         "=lever_outer_diameter / 2 + lever_handle_length", "конец ручки"),
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
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0))


def cyl(r, h, p, d=None):
    return Part.makeCylinder(r, h, p, d if d is not None else App.Vector(0, 0, 1))


def as_solid(shape, name):
    s = shape.removeSplitter()
    solids = s.Solids
    if len(solids) != 1:
        raise RuntimeError("%s: ожидался 1 солид, получено %d" % (name, len(solids)))
    return solids[0]


# ------------------------------------------------------------------ часть 1
# плоский диск
body = cyl(holder_r, plate_t, App.Vector(0.0, 0.0, 0.0))

# отверстие под корпус вилки
body = body.cut(cyl(hole_r, plate_t * 3.0, App.Vector(0.0, 0.0, -plate_t)))

# зубцы ВНУТРЬ от кромки отверстия, на +-90 гр., только нижние tooth_height
for sgn in (1, -1):
    x_in = sgn * (hole_r - tooth_d)
    x_out = sgn * (hole_r + plate_t)
    body = body.fuse(box(min(x_in, x_out), max(x_in, x_out),
                         -tooth_w / 2.0, tooth_w / 2.0,
                         0.0, tooth_h))

# цапфы-оси по бокам (3 и 9 часов), на уровне верхнего края
for sgn in (1, -1):
    d = App.Vector(float(sgn), 0.0, 0.0)
    body = body.fuse(cyl(pin_d / 2.0, pin_end - (holder_r - 2.0),
                         App.Vector(sgn * (holder_r - 2.0), 0.0, hinge_h), d))

holder_shape = as_solid(body, "Держатель")

# ---------------------------------------------------------------- часть 2: рычаг
lever_t   = V("lever_thickness")
lever_in  = V("lever_inner_diameter") / 2.0
lever_out = V("lever_outer_diameter") / 2.0
hub_d     = V("lever_hub_diameter")
hub_l     = V("lever_hub_length")
hub_x     = V("lever_hub_center_x")
bore_d    = V("hinge_hook_diameter")
handle_w  = V("lever_handle_width")
handle_end = V("lever_handle_end")

# плоское кольцо вокруг диска
lever = cyl(lever_out, lever_t, App.Vector(0.0, 0.0, 0.0))
lever = lever.cut(cyl(lever_in, lever_t * 3.0, App.Vector(0.0, 0.0, -lever_t)))

# ручка (продолжение обода, в той же плоскости)
lever = lever.fuse(box(-handle_w / 2.0, handle_w / 2.0, lever_in, handle_end,
                       0.0, lever_t))

# ступицы под цапфы (местные бобышки)
for sgn in (1, -1):
    d = App.Vector(float(sgn), 0.0, 0.0)
    lever = lever.fuse(cyl(hub_d / 2.0, hub_l,
                           App.Vector(sgn * (hub_x - hub_l / 2.0), 0.0, hinge_h), d))

# отверстия ступиц под цапфы
for sgn in (1, -1):
    d = App.Vector(float(sgn), 0.0, 0.0)
    lever = lever.cut(cyl(bore_d / 2.0, hub_l * 2.0,
                          App.Vector(sgn * (hub_x - hub_l), 0.0, hinge_h), d))

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
