#!/usr/bin/env python3

import re
import sys
import logging
import argparse



LOG = logging.getLogger("obj2stl")



def sub(a, b):
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    )



def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )



def obj2stl(obj_file):
    LOG.info(obj_file.name)

    obj_text = obj_file.read()

    vert_list = []
    face_list = []

    obj_text = re.compile(r"\s*\\\n\s*").sub(" ", obj_text)

    x_min = None
    y_min = None
    z_min = None
    x_max = None
    y_max = None
    z_max = None

    for line in obj_text.splitlines():
        line = re.sub("#.*$", "", line)
        line = line.strip()
        if not line:
            continue

        g_match = re.match("g", line)
        if g_match:
            continue

        vn_match = re.match("vn ([-0-9e.]+) ([-0-9e.]+) ([-0-9e.]+)", line)
        if vn_match:
            continue

        v_match = re.match("v ([-0-9e.]+) ([-0-9e.]+) ([-0-9e.]+)", line)
        if v_match:
            point = [float(v) for v in v_match.groups()]
            (x, y, z) = point
            x_min = x if x_min is None else min(x_min, x)
            y_min = y if y_min is None else min(y_min, y)
            z_min = z if z_min is None else min(z_min, z)
            x_max = x if x_max is None else max(x_max, x)
            y_max = y if y_max is None else max(y_max, y)
            z_max = z if z_max is None else max(z_max, z)
            vert_list.append(point)
            continue

        f_match = re.match("f( [-0-9e./]+)+$", line)
        if f_match:
            face = [int(v.split("/")[0]) for v in line.split()[1:]]
            face_list.append(face)
            continue

        LOG.error(line)
        sys.exit(1)

    non_triangular = 0

    sys.stdout.write("solid Default\n")
    for face in face_list:
        if len(face) != 3:
            non_triangular += 1
            continue

        a = sub(vert_list[face[1] - 1], vert_list[face[0] - 1])
        b = sub(vert_list[face[2] - 1], vert_list[face[1] - 1])
        n = cross(a, b)
        sys.stdout.write("  facet normal %f %f %f\n    outer loop\n" % n)

        for v in face:
            vert = vert_list[v - 1]
            sys.stdout.write("      vertex %f %f %f\n" % (
                vert[0], vert[1], vert[2]))
        sys.stdout.write("    endloop\n  endfacet\n")
    sys.stdout.write('endsolid Default\n')

    if non_triangular:
        LOG.error("%d non-triangular faces.")
        sys.exit(1)

    LOG.info("%s faces.", len(face_list))



def main():
    LOG.addHandler(logging.StreamHandler())

    parser = argparse.ArgumentParser(
        description="Convert polygons in an OBJ file to STL ASCII format.")
    parser.add_argument(
        "--verbose", "-v",
        action="count", default=0,
        help="Print verbose information for debugging.")
    parser.add_argument(
        "--quiet", "-q",
        action="count", default=0,
        help="Suppress warnings.")

    parser.add_argument(
        "--unit", "-u",
        action="store", default="",
        help="Units, eg. “mm”, “px”.")

    parser.add_argument(
        "obj",
        metavar="OBJ",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Path to OBJ file.")

    args = parser.parse_args()

    level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)[
        max(0, min(3, 1 + args.verbose - args.quiet))]
    LOG.setLevel(level)

    obj2stl(args.obj)



if __name__ == "__main__":
    main()
