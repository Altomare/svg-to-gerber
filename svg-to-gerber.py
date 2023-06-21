import argparse
import shutil
import os
import sys

from drillgen import gen_drill

def find_svg_flatten():
	if shutil.which('svg-flatten'):
		return 'svg-flatten'
	elif shutil.which('wasi-svg-flatten'):
		return 'wasi-svg-flatten'
	raise Exception("Cannot find svg-flatten")

def flatten(scale, in_dir, in_name, out_dir, out_name):
	os.system(f'{svg_flatten}'
	          f' --format gerber'
	          f' --scale {scale:.6}'
	          f' -f {os.path.join(in_dir, in_name)}'
	          f' {os.path.join(out_dir, out_name)}')

def flatten_outline(scale, in_dir, in_name, out_dir, out_name):
	os.system(f'{svg_flatten}'
	          f' --format gerber-outline'
	          f' --scale {scale:.6}'
	          f' {os.path.join(in_dir, in_name)}'
	          f' {os.path.join(out_dir, out_name)}')

parser = argparse.ArgumentParser(description='SVG to Gerbers helper')
parser.add_argument('in_dir', help='input directory with SVGs')
parser.add_argument('out_dir', help='output directory')
parser.add_argument('board_name', help='name')
parser.add_argument('dpi', help='DPI. Usually 96 or 72')

args = parser.parse_args()

if not os.path.isdir(args.in_dir):
    print(f"Unable to open dir '{args.in_dir}'")
    sys.exit(1)

if not os.path.isdir(args.out_dir):
    print(f"Unable to open dir '{args.out_dir}'")
    sys.exit(1)

svg_flatten = find_svg_flatten()

# The --usvg-dpi doesn't work on wasi-svg-flatten, use scale instead
flatten_scale = 96 / int(args.dpi)

gen_drill(os.path.join(args.in_dir, "drill.svg"),
		  os.path.join(args.out_dir, args.board_name + ".xln"),
		  args.dpi)

# Expect input dir to have the properly named files...
flatten(flatten_scale, args.in_dir, 'bottomcopper.svg', args.out_dir, args.board_name + ".gbl")
flatten(flatten_scale, args.in_dir, 'bottomsilk.svg', args.out_dir, args.board_name + ".gbo")
flatten(flatten_scale, args.in_dir, 'bottommask.svg', args.out_dir, args.board_name + ".gbs")
flatten_outline(flatten_scale, args.in_dir, 'outline.svg', args.out_dir, args.board_name + ".gko")
flatten(flatten_scale, args.in_dir, 'topcopper.svg', args.out_dir, args.board_name + ".gtl")
flatten(flatten_scale, args.in_dir, 'topmask.svg', args.out_dir, args.board_name + ".gts")
flatten(flatten_scale, args.in_dir, 'topsilk.svg', args.out_dir, args.board_name + ".gto")

print("Try internal layers")
flatten(flatten_scale, args.in_dir, 'L2copper.svg', args.out_dir, args.board_name + ".g2l")
flatten(flatten_scale, args.in_dir, 'L3copper.svg', args.out_dir, args.board_name + ".g3l")