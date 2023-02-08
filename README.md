# Gerber from SVGs

This is a bunch of scripts I use to generate gerbers from .svg files.
It mostly uses gerbolyze, except for the drill file generation.

The files come from Illustrator and need a 0.352778 scaling for some reason.

# Setup

You need Python3 installed, then install the requirements:
`pip install -r requirements.txt`

# Usage

`svg-to-gerber.py input_directory output_directory scale`

Input directory needs to contain the following files:
* bottomcopper.svg
* bottomsilk.svg
* bottommask.svg
* topcopper.svg
* topmask.svg
* topsilk.svg
* outline.svg
* drill.svg

# History & notes

2023-02-04:
	On the newer version of gerbolyze, scale seems to work differently.
	The source SVGs from Illustrator use a 72 dpi scale instead of 96.
	The --usvg-dpi doesn't appear to do much, so I had to use 1.333333
	scaling for those files. The weird 0.352778 value still applies to
	drillgen.
2023-02-07
	72 * 0.352778 = 25.400016
	Mystery scale is 25.4 / 72