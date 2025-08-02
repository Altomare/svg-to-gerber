import argparse
import math
import os
import sys
from enum import Enum
from numpy import float64
from svgelements import SVG, Circle, CubicBezier, Path


def format_nb(nb):
    frac, whole = math.modf(nb)
    frac *= pow(10, 6)
    return f"{int(whole)}{int(frac):06}"


class GerberWriter:
    def __init__(self, drill_map):
        self.drill_map = drill_map

    def _write_header(self, out):
        # Max 9.999m size, 6 decimals
        out.write(f"%FSLAX46Y46*%\n")
        out.write(f"%MOMM*%\n")
        out.write(f"%LPD*%\n")

    def _write_apertures(self, out):
        for aperture in CircleAperture._apertures.values():
            # Aperture idents usually start at 10 in Gerbers. Why?
            out.write(f"%ADD{aperture.ident + 10}C,{aperture.diameter:.6f}*%\n")

    def _write_oval_apertures(self, out):
        for aperture in OvalAperture._apertures.values():
            out.write(f"%ADD{aperture.ident + 10}O,{aperture.height:.6f}X{aperture.width:.6f}*%\n")

    def _apply_aperture(self, out, aperture):
        out.write(f"D{aperture.ident + 10}*\n")

    def _write_drill(self, out, drill):
        out.write(f"X{format_nb(drill.x)}Y{format_nb(drill.y)}D03*\n")

    def write_file(self, filename):
        with open(filename, 'w') as out:
            self._write_header(out)
            self._write_apertures(out)
            self._write_oval_apertures(out)

            current_aperture = None
            for drill in self.drill_map.circle_drills + self.drill_map.oval_drills:
                if drill.aperture != current_aperture:
                    current_aperture = drill.aperture
                    self._apply_aperture(out, current_aperture)
                self._write_drill(out, drill)

            out.write("M02*\n")


class ExcellonWriter:
    def __init__(self, drill_map):
        self.drill_map = drill_map

    def _write_apertures(self, out):
        for aperture in CircleAperture._apertures.values():
            out.write(f"T{aperture.ident + 1}C{aperture.diameter:.3f}\n")

    def _apply_aperture(self, out, aperture):
        out.write(f"T{aperture.ident + 1}\n")

    def _write_drill(self, out, drill):
        out.write(f"X{format_nb(drill.x)}Y{format_nb(drill.y)}*\n")

    def write_file(self, filename):
        with open(filename, 'w') as out:
            # Header, format 2 commands, metric
            out.write(f"M48\n")
            out.write(f"FMAT,2\n")
            out.write(f"METRIC\n")

            self._write_apertures(out)
            # TODO: OVAL

            # End of header, set absolute mode & drill mode
            out.write(f"%\n")
            out.write(f"G90\n")
            out.write(f"G05\n")

            current_aperture = None
            for drill in self.drill_map.circle_drills:
                if drill.aperture != current_aperture:
                    current_aperture = drill.aperture
                    self._apply_aperture(out, current_aperture)
                self._write_drill(out, drill)

            # End of program
            out.write(f"M30\n")


class DrillMap:
    def __init__(self):
        self.circle_drills = None
        self.oval_drills = None
        pass


class GlobalProperties:
    def __init__(self, int_digits, decimal_digits):
        self.int_digits = int_digits
        self.decimal_digits = decimal_digits


class CircleAperture:
    _aperture_ident = 0
    _apertures = {}

    def __init__(self, diameter):
        self.diameter = diameter
        self.ident = CircleAperture._aperture_ident
        CircleAperture._aperture_ident += 1

    @staticmethod
    def get(diameter):
        if diameter not in CircleAperture._apertures:
            CircleAperture._apertures[diameter] = CircleAperture(diameter)
        return CircleAperture._apertures[diameter]

    def __str__(self):
        return f"CircleAperture(w={self.width}, h={self.height})"


class OvalAperture:
    _apertures = {}

    def __init__(self, width, height):
        
        self.width = width
        self.height = height
        # Share ident with circle. God that's bad...
        self.ident = CircleAperture._aperture_ident
        CircleAperture._aperture_ident += 1

    @staticmethod
    def get(width, height):
        if (width, height) not in OvalAperture._apertures:
            OvalAperture._apertures[(width, height)] = OvalAperture(width, height)
        return OvalAperture._apertures[(width, height)]

    def __str__(self):
        return f"OvalAperture(w={self.width}, h={self.height})"


class Drill:
    def __init__(self, x, y, diameter):
        self.x = x
        self.y = y
        self.aperture = CircleAperture.get(diameter)

    def __str__(self):
        return f"Drill(x={self.x}, y={self.y}, aperture={self.aperture})"


class OvalDrill:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.aperture = OvalAperture.get(width, height)

    def __str__(self):
        return f"OvalDrill(x={self.x}, y={self.y}, aperture={self.aperture})"


def is_path_circle(element):
    "If path is a drawn circle, return the extracted element"
    # Quick n dirty hack, terrible perf
    beziers = [segment for segment in element._segments if isinstance(segment,CubicBezier)]
    if len(beziers) not in (4, 6):
        # print(len(beziers), element.bbox())
        return None
    return element.bbox()


def gen_drill(input_svg, output,
              dpi=72,
              enable_oval_drills=False,
              max_oval_aperture=10,
              drill_format='gerber'):
    document = DrillMap()
    document.circle_drills = []
    document.oval_drills = []

    print(f"Output format: {drill_format}")

    scale = 10 * 2.54 / float64(dpi)
    svg = SVG.parse(input_svg)
    for element in svg.elements():
        if isinstance(element, Circle):
            if element.stroke.value == 255:
                continue
            x = element.implicit_center[0]
            y = svg.implicit_height - element.implicit_center[1]
            aperture = element.implicit_r * 2

            x *= scale
            y *= scale
            aperture *= scale

            document.circle_drills.append(Drill(x, y, aperture))
        elif isinstance(element, Path):
            bbox = is_path_circle(element)
            if not bbox:
                continue

            # .1mm precision is enough and avoids float errors
            w = round(abs(bbox[3] - bbox[1]), 1)
            h = round(abs(bbox[2] - bbox[0]), 1)
            if h == w:
                aperture = h
                x = svg.implicit_height -round(min(bbox[1], bbox[3]) + aperture / 2.0, 3)
                y = round(min(bbox[0], bbox[2]) + aperture / 2.0, 3)

                x *= scale
                y *= scale
                aperture *= scale

                document.circle_drills.append(Drill(y, x, aperture))
            elif enable_oval_drills:
                x = svg.implicit_height -round(min(bbox[1], bbox[3]) + w / 2.0, 3)
                y = round(min(bbox[0], bbox[2]) + h / 2.0, 3)
                if h > max_oval_aperture or w > max_oval_aperture:
                    print("Ignore too big, probably a false positive:", h, w)
                    continue
                x *= scale
                y *= scale
                h *= scale
                w *= scale
                document.oval_drills.append(OvalDrill(round(y, 3), round(x, 3), round(w, 3), round(h, 3)))

    document.circle_drills.sort(key=lambda x: x.aperture.diameter)
    document.oval_drills.sort(key=lambda x: x.aperture.height)
    document.oval_drills.sort(key=lambda x: x.aperture.width)

    if enable_oval_drills:
        print(f"Found {len(document.oval_drills)} oval drills")
        for drill in document.oval_drills:
            print(drill)

    if drill_format == 'excellon':
        if enable_oval_drills:
            print("Excellon is not supported with oval drills")
            return
        writer = ExcellonWriter(document)
        writer.write_file(output)
    else:
        writer = GerberWriter(document)
        writer.write_file(output)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate drill gerber from SVG')
    parser.add_argument('svg', help='input svg')
    parser.add_argument('output', help='output gerber')
    parser.add_argument('-f', '--format', help='output format', choices=['excellon', 'gerber'], default='gerber')
    parser.add_argument('-d', '--dpi', help='DPI', choices=[72,96], type=int, default=72)
    parser.add_argument('-o', '--enable_oval_drills', help='Detect and generate oval drilled holes', action="store_true")
    parser.add_argument('-m', '--max_oval_drill_size', help='Maximum size for oval drill generation', type=float, default=10.0)

    args = parser.parse_args()

    if not os.path.isfile(args.svg):
        print(f"Unable to find file '{args.svg}'")
        sys.exit(1)

    gen_drill(args.svg, args.output, args.dpi, drill_format=args.format, enable_oval_drills=args.enable_oval_drills)
