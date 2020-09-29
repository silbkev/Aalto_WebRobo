#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
# System modules:
import argparse

# Custom modules:
import Robot as rob


def main(use_dummy_images, verbose_robot, verbose_options, use_stream):
    robot = rob.Robot(use_dummy_images, verbose_level=verbose_robot, vrb=verbose_options)
    robot.vim.save_stream = use_stream  # Set whether to save the image for stream
    robot.run()


# Initiate the parser:
parser = argparse.ArgumentParser(
    description='Basic robot line following routine.'
)

# Options:
parser.add_argument('-d', '--dummy_images',
                    default=False, action='store_true',
                    help='Use cached dummy images for the run')

# Numbers:
parser.add_argument('-vR', '--verbose_robot', metavar="VR",
                    type=int, default=1,
                    help='Verbose level for prints')

parser.add_argument('-vI', '--verbose_image', metavar="VI",
                    type=int, default=-1,
                    help='Verbose level for prints')

# Numbers:
parser.add_argument('-vV', '--verbose_vision', metavar='VV',
                    type=int, default=-1,
                    help='Verbose level for prints')

# Numbers:
parser.add_argument('-vC', '--verbose_control', metavar='VC',
                    type=int, default=-1,
                    help='Verbose level for prints')

# Numbers:
parser.add_argument('-vP', '--verbose_planner', metavar='VP',
                    type=int, default=-1,
                    help='Verbose level for prints')


parser.add_argument('-dS', '--disable_stream',
                    default=True, action='store_false',
                    help='Disable stream save for performance boost')

# Parse arguments:
args = parser.parse_args()

verbose_options={
        'ctrl': args.verbose_control,
        'plnr': args.verbose_planner,
        'vis': args.verbose_vision,
        'cam': args.verbose_image,
    }
# Execute:
main(
    use_dummy_images=args.dummy_images,
    verbose_robot=args.verbose_robot,
    verbose_options=verbose_options,
    use_stream=args.disable_stream
)
