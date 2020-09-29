from flask import make_response, current_app, Blueprint, render_template, \
                  Response, redirect, request, url_for, jsonify, flash
from flask_login import login_required
import Settings as S
from robot import Robot
import json
import time
import importlib

bp = Blueprint(
    "robot",
    __name__,
    url_prefix="/robot",
    static_folder="static",
    static_url_path="/static",
)

# robot = Robot(simulate=False, verbose_level=1, threaded=True)
# Handler for the run button
@bp.route('/set_running')
def set_running():
    is_running = request.args.get('checked')
    with current_app.app_context():
        # importlib.reload(S) would overwrite changes in UI!
        if is_running == "true":
            current_app.config['ROBOT'].run()
        else:
            current_app.config['ROBOT'].stop()
    return jsonify({"running" : is_running})

# Change the speed of the robot
@bp.route('/change_speed', methods=['GET', 'POST'])
def change_speed():
    speed = request.args.get('speed', type=float)
    S.MAX_SPEED = speed
    return jsonify({"speed" : speed})

# NOTE: We don't need this function if we don't intend to update the reading
# i.e. by pressing a button
@bp.route('/battery_level', methods=['GET'])
def get_battery_level():
    """ Return current battery robot level

        from: https://www.piborg.org/blog/thunderborg-examples
            Reads the current battery level from the main input.
            Returns the value as a voltage based on
            the 3.3 V rail as a reference.
        NOTE:
            If simulation is used, returns -1

        NOTE: Currently only as voltage, but a min and max
              could be added to Settings so we could scale
              to 0-100%
        NOTE: Not tested how plugged in affects the reading
    """
    with_datestamp = request.args.get('with_datestamp', False)
    with current_app.app_context():
        voltage = current_app.config['ROBOT'].get_battery_level()
    if with_datestamp:
        response = make_response(json.dumps([time.time() * 1000, voltage]))
        response.content_type = 'application/json'
        return response
    return jsonify({"voltage": voltage})

# Stream picture
@bp.route('/image_stream')
@login_required
def image_stream():
    def gen_stream(streamer):
        """Video streaming generator function."""
        while True:
            frame = streamer.frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

    with current_app.app_context():
        streamer = current_app.config["ROBOT"].vim

    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_stream(streamer),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Stream picture
@bp.route('/chart_stream')
@login_required
def chart_stream():
    iwant = request.args.get('iwantthis')
    with current_app.app_context():
        """ Data from controller.

            Shoudl be the latest values of plotted variables, in order
            matching with that in hchart.js

            NOTE: need to be converted to (k, value) tuples
            from: https://github.com/tdiethe/flask-live-charts/

            NOTE: Horrible implementation.
            TODO: get rid of static indicies
        """
        data = current_app.config["ROBOT"].controller.latest_values
        if not data:
            return '{}'
        k = data.pop(0)  # Remove the first item (the step index k)
        if iwant == 'CTRL':
            data = data[:3]
        elif iwant == 'PID':
            data = data[4:11]
        elif iwant == "SPEED":
            data = [data[-1]]
        else:
            raise ValueError("Invalid REQUEST argument when generating chart")
        data = [(k, v) for v in data]  # Convert to point format

    response = make_response(json.dumps(data))
    """ Video streaming route. Put this in the src attribute of an img tag."""
    response.content_type = 'application/json'
    return response

# Stream processed image
@bp.route('/processed_image_stream')
@login_required
def processed_image_stream():
    def gen_processed_stream(streamer):
        """Video streaming generator function for the processed image."""
        while True:
            frame = streamer.stream
            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

    with current_app.app_context():
        streamer = current_app.config["ROBOT"].vim

    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_processed_stream(streamer),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    """Change parameters that affect how the robot is behaving."""
    # Set the settings on "Save"-buton click:
    if request.method == 'POST':
        # Follow only something black:
        #S.VIS_ONLY_BLACK = request.form.get('onlyblack') is not None
        # Save image if line is not found:
        #S.VIS_SAVE_PROBLEMATIC_IMAGE = request.form.get('prob_img') is not None
        # Minimum speed:
        S.MIN_SPEED = float(request.form.get('minspeedlimit'))
        S.MIN_SPEED_LIMIT = S.MIN_SPEED
        # Maximum speed:
        S.MAX_SPEED_LIMIT = float(request.form.get('maxspeedlimit'))
        # Update the PID parameters:
        # NOTE: by looping only keys in user editable dicts, we prevent
        #       attacks by using special requests.
        for k in S.PID:
            S.PID[k] = request.form.get(k, S.PID[k], type=float)
        for k in S.VIS:
            # HACK: type conversion using existing values! woo!
            v = request.form.get(k, False, type=type(S.VIS[k]))
            S.VIS[k] = v
        # Redirect the user to dashboard to investigate effects of changes:
        return redirect(url_for('robot.dashboard'))

    # Entering the page, get the current values:
    # HACK: Transform boolean values to checkbox checked
    # NOTE: could be better and neater to use custom checkboxes!
    checkbox_values = {}
    other_values = {}
    for k, v in S.VIS.items():
        if isinstance(v, bool):
            checkbox_values[k] = "checked" if v else ""
        else:
            other_values[k] = v

    #onlyblack = ""
    #if S.VIS_ONLY_BLACK:
    #    onlyblack = "checked"
    #prob_img = ""
    #if S.VIS_SAVE_PROBLEMATIC_IMAGE:
    #    prob_img = "checked"


    # Return the page with current values:
    return render_template(
        'settings.html',
        #onlyblack = onlyblack,
        #prob_img = prob_img,
        minspeedlimit = S.MIN_SPEED_LIMIT,
        maxspeedlimit = S.MAX_SPEED_LIMIT,
        **checkbox_values,
        **other_values,
        **S.PID
    )

@bp.route('/save_settings', methods=['POST'])
@login_required
def save_user_settings():
    """ Save the current user settings in a json file
    TODO: Separate settings for separate users!
    """
    # Load settings in current file:
    with open(S.USER_SETTINGS_FILE, 'r') as f:
        old_settings = json.load(f)
    # Replace changed parameters:
    # TODO: change to use user_setting keys instead
    for k, v in iter(request.form.items()):
        if k in old_settings:
            old_settings[k] = float(v)
        # A bit hacky: PID / VIS settings:
        # THey are in a dict, sop update them is possible:
        if 'PID' not in old_settings:
            raise ValueError("PID values not defined in user settings!")
        if 'VIS' not in old_settings:
            raise ValueError("VIS values not defined in user settings!")
        if k in old_settings['PID']:
            old_settings['PID'][k] = float(v)
        if k in old_settings['VIS']:
            old_settings['VIS'][k] = type(old_settings['VIS'][k])(v)

    # Finally, save the user settings:
    with open(S.USER_SETTINGS_FILE, 'w') as f:
        f.write(json.dumps(old_settings, indent=4))

    flash('Settings saved succesfully!')

    return redirect(url_for('robot.settings'), code=303)



# Interact with the robot
@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    with current_app.app_context():
        running_state = current_app.config['ROBOT'].running
        voltage = current_app.config['ROBOT'].get_battery_level()
    running_button_state = ""
    if running_state:
        running_button_state = "checked"
    return render_template('dashboard.html',

        minspeedlimit = S.MIN_SPEED_LIMIT,
        maxspeedlimit = S.MAX_SPEED_LIMIT,
        current_speed=S.MAX_SPEED,
        running_button_state=running_button_state,
        voltage = voltage)


# Site that shows the stream
@bp.route('/stream')
@login_required
def show_stream():
    return render_template('stream.html')
