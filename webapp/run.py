"""
    The ultimate script for running the robot.
    Supports starting the robot in both GUI and CMD interface modes.

"""
import argparse
import simple_stream as ss
import robot as rob
import Settings as S

import logging

# Initiate the parser:
parser = argparse.ArgumentParser(
    description='Basic robot line following routine.'
)

# Options:
parser.add_argument('-f', '--run_headless',
                    default=False, action='store_true',
                    help='Run the robot without UI')

parser.add_argument('-sS', '--use_simple_stream',
                    default=False, action='store_true',
                    help='Run the robot with simple stream UI')

parser.add_argument('-p', '--show_flask_prints',
                    default=False, action='store_true',
                    help='Show logging prints of Flask.')

parser.add_argument('-s', '--simulate',
                    default=False, action='store_true',
                    help='Run the robot with cached images.')

# TODO: Better  names / variables for arguments
parser.add_argument('-sI', '--simulate_image_idx', metavar="SI",
                    type=int, default=-1,
                    help='Single image for simulation')

parser.add_argument('-l', '--log_ctrl_params',
                    default=False, action='store_true',
                    help='Log the parameters of the controller.')

parser.add_argument('-lF', '--logging_frequency', metavar="LF",
                    type=int, default=5,
                    help='Logging frequency. Log after n iterations.')

parser.add_argument('-fP', '--flask_port', metavar="fP",
                    type=int, default=5000,
                    help='Port for Flask app. 80 needs sudo rights.')


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

# Parse arguments:
args = parser.parse_args()

verbose_options={
    'ctrl': args.verbose_control,
    'plnr': args.verbose_planner,
    'vis': args.verbose_vision,
    'cam': args.verbose_image,
}

# Logging:
S.LOG_CONTROLLER = args.log_ctrl_params
S.LOG_FREQUENCY = args.logging_frequency

# Disable flask prints:
if not args.show_flask_prints:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

if args.run_headless:
    robot = rob.Robot(simulate=args.simulate, verbose_level=args.verbose_robot, vrb=verbose_options)
    robot.vim.save_stream = False  # We use faster stream
    robot.sim_idx = None if args.simulate_image_idx == -1 else args.simulate_image_idx
    robot.run()
else:
#    robot.vim.save_stream = False  # We use faster stream
    if args.use_simple_stream:
        robot = rob.Robot(simulate=False, verbose_level=args.verbose_robot,
                          vrb=verbose_options, threaded=True)
        ui = ss.create_ui_app(robot)
        robot.start()
    else:
        import webapp
        #webapp.robot.robot.set_verbose_levels(verbose_options)
        robot = rob.Robot(simulate=args.simulate, verbose_level=args.verbose_robot,
                          vrb=verbose_options, threaded=True)
        ui = webapp.create_app(robot) #robot)
        #robot.start()
    ui.run(host='0.0.0.0', port=args.flask_port, debug=True, use_reloader=False)
robot.deactivate()
print("\n[MAIN] User shutdown")
