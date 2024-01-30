import argparse
from colorama import Fore, Style
import math
import shutil
import os
import sys
import signal
from subprocess import Popen, PIPE

from drillgen import gen_drill


def find_svg_flatten():
    if shutil.which('svg-flatten'):
        return shutil.which('svg-flatten')
    elif shutil.which('wasi-svg-flatten'):
        return shutil.which('wasi-svg-flatten')
    return None


def flatten(scale, in_dir, in_name, out_dir, out_name, fmt):
    if not os.path.isfile(os.path.join(in_dir, in_name)):
        print(f"[{out_name[:-4]}] {Fore.YELLOW}Couldn't find {in_name}{Style.RESET_ALL}")
        return

    print(f'[{out_name[:-4]}] {in_name} -> {out_name}')

    line = [
        f'{svg_flatten}',
        '--format', fmt,
        '--scale', f'{scale:.6}',
    ]
    # For some reason -f is position dependent in wasi-svg-flatten...
    if fmt == 'gerber':
        line.append("-f")
    line.append(f'{os.path.join(in_dir, in_name)}')
    line.append(f'{os.path.join(out_dir, out_name)}')
    # print(' '.join(line))
    p = Popen(line, stdout=PIPE, stderr=PIPE, stdin=PIPE)

    err_logs = p.stderr.read()
    if err_logs:
        print(f"{Fore.YELLOW}{err_logs.decode()}{Style.RESET_ALL}", end='')

    # Read eror code
    streamdata = p.communicate()[0]
    if (p.returncode != 0):
        print(f"{Fore.RED}Error{Style.RESET_ALL}")
        exit_cleanup()


def exit_cleanup():
    # TODO: Delete files
    sys.exit(1)


def signal_handler(sig, frame):
    print("User interrupt")
    error_cleanup()


signal.signal(signal.SIGINT, signal_handler)

parser = argparse.ArgumentParser(description='SVG to Gerbers helper')
parser.add_argument('in_dir', help='input directory with SVGs')
parser.add_argument('out_dir', help='output directory')
parser.add_argument('board_name', help='name')
parser.add_argument('dpi', help='DPI', choices=[72,96], type=int)

args = parser.parse_args()

if not os.path.isdir(args.in_dir):
    print(f"Unable to open dir '{args.in_dir}'")
    sys.exit(1)

if not os.path.isdir(args.out_dir):
    print(f"Unable to open dir '{args.out_dir}'")
    sys.exit(1)

svg_flatten = find_svg_flatten()
if svg_flatten is None:
    print("Error: can't find svg-flatten")
    sys.exit(1)

# --usvg-dpi doesn't work on wasi-svg-flatten, calculate scale instead
flatten_scale = 96 / int(args.dpi)
flatten_scale = math.sqrt(flatten_scale)

gen_drill(os.path.join(args.in_dir, "drill.svg"),
          os.path.join(args.out_dir, args.board_name + ".drl"),
          args.dpi)

# Expect input dir to have the properly named files...
flatten(flatten_scale, args.in_dir, 'bottomcopper.svg', args.out_dir, args.board_name + ".gbl", 'gerber')
flatten(flatten_scale, args.in_dir, 'bottomsilk.svg', args.out_dir, args.board_name + ".gbo", 'gerber')
flatten(flatten_scale, args.in_dir, 'bottommask.svg', args.out_dir, args.board_name + ".gbs", 'gerber')
flatten(flatten_scale, args.in_dir, 'outline.svg', args.out_dir, args.board_name + ".gko", 'gerber-outline')
flatten(flatten_scale, args.in_dir, 'topcopper.svg', args.out_dir, args.board_name + ".gtl", 'gerber')
flatten(flatten_scale, args.in_dir, 'topmask.svg', args.out_dir, args.board_name + ".gts", 'gerber')
flatten(flatten_scale, args.in_dir, 'topsilk.svg', args.out_dir, args.board_name + ".gto", 'gerber')
flatten(flatten_scale, args.in_dir, 'L2copper.svg', args.out_dir, args.board_name + ".g2l", 'gerber')
flatten(flatten_scale, args.in_dir, 'L3copper.svg', args.out_dir, args.board_name + ".g3l", 'gerber')
