from flask import render_template, g
from app import db
from app.errors import bp
from app.universal_routes import before_request_u


@bp.app_errorhandler(404)
def not_found_error(error):
    before_request_u()
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    before_request_u()
    db.session.rollback()
    return render_template('errors/500.html'), 500