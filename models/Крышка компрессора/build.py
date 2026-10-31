# -*- coding: utf-8 -*-
"""Крышка компрессора — сборка модели из листа Parameters.

Запуск в FreeCAD (из корня репозитория):
    exec(open(r"models/Крышка компрессора/build.py", encoding="utf-8").read())

Скрипт идемпотентен: удаляет все объекты документа, кроме Spreadsheet::Sheet,
и собирает геометрию заново из значений листа Parameters.
Ни один размер здесь не задаётся числом — всё читается из таблицы.

Значения ниже (SEED) — подтверждённые пользователем исходные данные
(см. Параметры.md). Они используются ТОЛЬКО для создания листа, если его нет.
"""

import FreeCAD as App
import Part
import math

DOC_NAME = u"Крышка_компрессора"

SEED = [
    # (имя, значение, единица, пояснение)
    ("plate_diameter", 59.5, "mm", "диаметр круглой части контура"),
    ("plate_flat_offset_from_right", 51.6, "mm", "от правого края до прямой кромки"),
    ("plate_thickness", 1.2, "mm", "толщина листа"),
    ("plate_corner_radius", 0.5, "mm", "скругление углов среза"),
    ("plate_sagitta", 0.0, "mm", "выгиб пластины (0 = плоская)"),
    ("boss_width_top", 17.0, "mm", "ширина бугра поперёк кромки сверху"),
    ("boss_width_bottom", 21.8, "mm", "ширина бугра поперёк кромки снизу"),
    ("boss_length", 27.0, "mm", "размах бугра вдоль кромки"),
    ("boss_height", 7.6, "mm", "от нижней плоскости пластины"),
    ("boss_end_radius", 0.5, "mm", "скругление торцов (пока не используется)"),
    ("boss_base_fillet", 0.5, "mm", "галтель основания (пока не используется)"),
    ("hole_diameter", 2.7, "mm", "сквозное отверстие"),
    ("hole_pitch_x", 33.5, "mm", "между ближайшими краями, поперёк кромки"),
    ("hole_pitch_y", 36.7, "mm", "между ближайшими краями, вдоль кромки"),
    ("hole_pattern_offset", 0.0, "mm", "смещение рисунка от центра"),
    ("hole_chamfer_diameter", 0.0, "mm", "0 = без фаски"),
    ("hole_chamfer_angle", 0.0, "deg", "0 = без фаски"),
]

DERIVED = [
    ("plate_radius", "=plate_diameter / 2", "mm"),
    ("plate_flat_offset", "=plate_radius - plate_flat_offset_from_right", "mm"),
    ("boss_rise", "=boss_height - plate_thickness", "mm"),
    ("boss_taper", "=boss_width_bottom - boss_width_top", "mm"),
    ("hole_pitch_cc_x", "=hole_pitch_x + hole_diameter", "mm"),
    ("hole_pitch_cc_y", "=hole_pitch_y + hole_diameter", "mm"),
    ("hole_x", "=hole_pitch_cc_x / 2", "mm"),
    ("hole_y", "=hole_pitch_cc_y / 2", "mm"),
    ("plate_chord_half", "=sqrt(plate_radius^2 - plate_flat_offset^2)", "mm"),
    ("cavity_length", "=boss_width_bottom - plate_thickness", "mm"),
]


def get_doc():
    doc = App.listDocuments().get(DOC_NAME)
    return doc if doc is not None else App.newDocument(DOC_NAME)


def ensure_sheet(doc):
    sh = doc.getObject("Parameters")
    if sh is None:
        sh = doc.addObject("Spreadsheet::Sheet", "Parameters")
        sh.set("A1", "variable"); sh.set("B1", "value")
        sh.set("C1", "unit"); sh.set("D1", "meaning")
        r = 2
        for name, val, unit, note in SEED:
            sh.set("A%d" % r, name)
            sh.set("B%d" % r, "%.10g %s" % (val, unit))
            sh.set("C%d" % r, unit)
            sh.set("D%d" % r, note)
            sh.setAlias("B%d" % r, name)
            r += 1
        sh.set("A20", "derived"); sh.set("B20", "formula")
        sh.set("C20", "unit"); sh.set("D20", "meaning")
        r = 21
        for name, formula, unit in DERIVED:
            sh.set("A%d" % r, name)
            sh.set("B%d" % r, formula)
            sh.set("C%d" % r, unit)
            sh.setAlias("B%d" % r, name)
            r += 1
        doc.recompute()
    return sh


def build():
    doc = get_doc()
    sh = ensure_sheet(doc)

    def P(name):
        return App.Units.Quantity(sh.get(name)).Value

    # --- параметры (все — из таблицы) ---
    t = P("plate_thickness")
    cr = P("plate_corner_radius")
    R = P("plate_radius")
    xflat = P("plate_flat_offset")
    yc = P("plate_chord_half")
    ay = P("boss_length") / 2.0
    Wb = P("boss_width_bottom")
    Wt = P("boss_width_top")
    Lb = P("boss_length")
    rise = P("boss_rise")
    cav_len = P("cavity_length")
    hd = P("hole_diameter")
    hx = P("hole_x")
    hy = P("hole_y")
    poff = P("hole_pattern_offset")
    chd = P("hole_chamfer_diameter")
    cha = P("hole_chamfer_angle")

    eps = 1e-6
    R120 = App.Rotation(App.Vector(1, 1, 1), 120)   # X->Y->Z->X
    RX90 = App.Rotation(App.Vector(1, 0, 0), 90)    # y->z, выдавливание +Z -> -Y

    # --- чистим документ, кроме таблицы ---
    for o in list(doc.Objects):
        if o.TypeId != "Spreadsheet::Sheet":
            doc.removeObject(o.Name)
    doc.recompute()

    # --- 1. пластина (D-контур) ---
    plate = Part.makeCylinder(R, t, App.Vector(0, 0, 0), App.Vector(0, 0, 1)).common(
        Part.makeBox(2 * R, 4 * R, 4 * t, App.Vector(xflat, -2 * R, -t)))
    chord_edges = [e for e in plate.Edges
                   if abs(e.Vertexes[0].Point.x - e.Vertexes[1].Point.x) < eps
                   and abs(e.Vertexes[0].Point.y - e.Vertexes[1].Point.y) < eps
                   and abs(abs(e.Vertexes[0].Point.y) - yc) < 1e-3
                   and abs(e.Vertexes[0].Point.x - xflat) < 1e-3]
    plate = plate.makeFillet(cr, chord_edges)

    # --- 2. дуга вдоль кромки: полуэллипс в YZ, выдавлен по X ---
    def arch_region(half_span, height, depth, x_start):
        arc = Part.ArcOfEllipse(
            Part.Ellipse(App.Vector(0, t, 0), half_span, height), 0, math.pi).toShape()
        wire = Part.Wire([arc,
                          Part.LineSegment(App.Vector(-half_span, t, 0),
                                           App.Vector(-half_span, -t, 0)).toShape(),
                          Part.LineSegment(App.Vector(-half_span, -t, 0),
                                           App.Vector(half_span, -t, 0)).toShape(),
                          Part.LineSegment(App.Vector(half_span, -t, 0),
                                           App.Vector(half_span, t, 0)).toShape()])
        s = Part.Face(wire).extrude(App.Vector(0, 0, depth))
        s.transformShape(R120.toMatrix())
        s.translate(App.Vector(x_start, 0, 0))
        return s

    A = arch_region(ay, rise, Wb, xflat)

    # --- 3. трапеция поперёк кромки: вертикаль у кромки, скос к центру ---
    p1 = App.Vector(xflat, t)
    p2 = App.Vector(xflat, t + rise)
    p3 = App.Vector(xflat + Wt, t + rise)
    p4 = App.Vector(xflat + Wb, t)
    B = Part.Face(Part.Wire([Part.LineSegment(p1, p2).toShape(),
                             Part.LineSegment(p2, p3).toShape(),
                             Part.LineSegment(p3, p4).toShape(),
                             Part.LineSegment(p4, p1).toShape()])) \
        .extrude(App.Vector(0, 0, Lb))
    B.transformShape(RX90.toMatrix())
    B.translate(App.Vector(0, Lb / 2.0, 0))

    boss = A.common(B)
    solid = plate.fuse(boss).removeSplitter()

    # --- 4. полость: открыта у кромки и снизу ---
    Ai = arch_region(ay - t, rise - t, cav_len + t, xflat - t)

    dx, dz = Wb - Wt, -rise
    ln = math.hypot(dx, dz)
    nx, nz = dz / ln, -dx / ln                 # нормаль внутрь материала
    sxp, szp = xflat + Wt + t * nx, t + rise + t * nz
    k = dx / dz
    ztop = t + rise - t

    def xon(z):
        return sxp + k * (z - szp)

    q1 = App.Vector(xflat - t, -t)
    q2 = App.Vector(xflat - t, ztop)
    q3 = App.Vector(xon(ztop), ztop)
    q4 = App.Vector(xon(-t), -t)
    Bi = Part.Face(Part.Wire([Part.LineSegment(q1, q2).toShape(),
                              Part.LineSegment(q2, q3).toShape(),
                              Part.LineSegment(q3, q4).toShape(),
                              Part.LineSegment(q4, q1).toShape()])) \
        .extrude(App.Vector(0, 0, Lb))
    Bi.transformShape(RX90.toMatrix())
    Bi.translate(App.Vector(0, Lb / 2.0, 0))

    solid = solid.cut(Ai.common(Bi))

    # --- 5. отверстия ---
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = App.Vector(sx * hx + poff, sy * hy, -t)
            solid = solid.cut(Part.makeCylinder(hd / 2.0, 4 * t, c, App.Vector(0, 0, 1)))
            if chd > 0 and cha > 0:
                hgt = (chd - hd) / 2.0 / math.tan(math.radians(cha / 2.0))
                solid = solid.cut(Part.makeCone(chd / 2.0, hd / 2.0, hgt,
                                                App.Vector(c.x, c.y, t),
                                                App.Vector(0, 0, -1)))

    solid = solid.removeSplitter()

    obj = doc.addObject("Part::Feature", "Cover_Plate")
    obj.Label = "Cover_Plate"
    obj.Shape = solid.Solids[0]
    doc.recompute()

    b = obj.Shape.BoundBox
    print("Cover_Plate: vol %.2f  faces %d  valid %s" % (
        obj.Shape.Volume, len(obj.Shape.Faces), obj.Shape.isValid()))
    print("bbox X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f" % (
        b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
    return obj


build()
