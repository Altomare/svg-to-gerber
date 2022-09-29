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
