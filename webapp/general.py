from flask import current_app, Blueprint, render_template, Response, redirect, request, url_for, flash, abort, jsonify
from flask_login import login_required
from webapp.models import Measurement, Setting
import Settings as S

bp = Blueprint("general", __name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

# Error: Page not Found
@bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Error: Conficting Information
@bp.errorhandler(500)
def input_error(f):
    return render_template('500.html'), 500
