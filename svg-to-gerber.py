import argparse
import os
import sys

from drillgen import gen_drill

# Expect input dir to have the properly named files...

parser = argparse.ArgumentParser(description='SVG to Gerbers helper')
parser.add_argument('in_dir', help='input directory with SVGs')
parser.add_argument('out_dir', help='output directory')
parser.add_argument('scale', help='rescale', default=0.352778)  # idk why

args = parser.parse_args()

if not os.path.isdir(args.in_dir):
    print(f"Unable to open dir '{args.in_dir}'")
    sys.exit(1)
if not os.path.isdir(args.out_dir):
    print(f"Unable to open dir '{args.out_dir}'")
    sys.exit(1)

gen_drill(args.svg, args.output, args.scale)

def flatten(scale, in_dir, in_name, out_dir, out_name):
	os.system(f'svg-flatten'
	          f' --format gerber'
	          f' --scale {scale}'
	          f' -f {os.path.join(in_dir, in_name)}'
	          f' {os.path.join(out_dir, out_name)}')

def flatten_outline(scale, in_dir, in_name, out_dir, out_name):
	os.system(f'svg-flatten'
	          f' --format gerber-outline'
	          f' --scale {scale}'
	          f' {os.path.join(in_dir, in_name)}'
	          f' {os.path.join(out_dir, out_name)}')

flatten(args.scale, args.in_dir, 'bottomcopper.svg', args.out_dir, "B.Cu.gbr")
flatten(args.scale, args.in_dir, 'bottommask.svg', args.out_dir, "B_Mask.gbr")
flatten(args.scale, args.in_dir, 'topcopper.svg', args.out_dir, "F_Cu.gbr")
flatten(args.scale, args.in_dir, 'topmask.svg', args.out_dir, "F_Mask.gbr")
flatten(args.scale, args.in_dir, 'topsilk.svg', args.out_dir, "F_Silkscreen.gbr")
flatten_outline(args.scale, args.in_dir, 'outline.svg', args.out_dir, "Edge_Cuts.gbr")
