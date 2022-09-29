import argparse
import math
import os
import sys
from numpy import float64
from svgelements import SVG, Circle


# Max 9.999m size, 6 decimals
G_INT_SIZE = 4
G_DEC_SIZE = 6


def format_nb(nb):
    frac, whole = math.modf(nb)
    frac *= pow(10, G_DEC_SIZE)
    # print(nb, whole, frac)
    # print(f"{int(whole)}{int(frac):06}")
    return f"{int(whole)}{int(frac):06}"


class GlobalProperties:
    def __init__(self, int_digits, decimal_digits):
        self.int_digits = int_digits
        self.decimal_digits = decimal_digits

    def write(self, out):
        coord_digits = f"{self.int_digits}{self.decimal_digits}"
        out.write(f"%FSLAX{coord_digits}Y{coord_digits}*%\n")
        out.write(f"%MOMM*%\n")
        out.write(f"%LPD*%\n")


class CircleAperture:
    _aperture_ident = 10
    _apertures = {}

    def __init__(self, diameter):
        self.diameter = diameter
        self.ident = CircleAperture._aperture_ident
        CircleAperture._aperture_ident += 1

    @staticmethod
    def write_all(out):
        # Decimal precision
        for aperture in CircleAperture._apertures.values():
            # out.write("%TA.AperFunction,ComponentDrill*%\n")
            out.write(f"%ADD{aperture.ident}C,{aperture.diameter:.6f}*%\n")
            # out.write("%TD*%\n")

    def write_apply(self, out):
        out.write(f"D{self.ident}*\n")

    @staticmethod
    def get(diameter):
        if diameter not in CircleAperture._apertures:
            CircleAperture._apertures[diameter] = CircleAperture(diameter)
        return CircleAperture._apertures[diameter]


class Drill:
    def __init__(self, x, y, diameter):
        self.x = x
        self.y = y
        self.aperture = CircleAperture.get(diameter)

    def write(self, out):
        out.write(f"X{format_nb(self.x)}Y{format_nb(self.y)}D03*\n")


def gen_drill(input_svg, output, scale):
    drills = []

    scale = float64(scale)
    svg = SVG.parse(input_svg)
    for element in svg.elements():
        if isinstance(element, Circle):
            x = element.implicit_center[0]
            y = svg.implicit_height - element.implicit_center[1]
            aperture = element.implicit_r * 2

            x *= scale
            y *= scale
            aperture *= scale

            drills.append(Drill(x, y, aperture))

    drills.sort(key=lambda x: x.aperture.diameter)
    global_props = GlobalProperties(G_INT_SIZE, G_DEC_SIZE)
    current_aperture = None

    with open(output, 'w') as out:
        global_props.write(out)
        CircleAperture.write_all(out)

        for drill in drills:
            if drill.aperture != current_aperture:
                current_aperture = drill.aperture
                current_aperture.write_apply(out)
            drill.write(out)
        out.write("M02*\n")

    # print(f"{0.06:06}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate drill gerber from SVG')
    parser.add_argument('svg', help='input svg')
    parser.add_argument('output', help='output gerber')
    parser.add_argument('scale', help='rescale')

    args = parser.parse_args()

    if not os.path.isfile(args.svg):
        print(f"Unable to find file '{args.svg}'")
        sys.exit(1)

    gen_drill(args.svg, args.output, args.scale)
