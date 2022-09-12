from crypt import methods
import urllib
import ast
import requests
import datetime

from flask import Blueprint, url_for, render_template, request, flash
from werkzeug.utils import redirect
# from datetime import datetime
from sqlalchemy import desc

from app.models import User, BuyPoint, ReserveCourt, PayDB, DoorStatus
from app import db
from app.forms import DoorOpenForm

bp = Blueprint("admin", __name__, url_prefix='/')


@bp.route('/admin_menu/<email>')
def admin_menu(email):
    user = User.query.filter_by(email=email).first()
    return  render_template("admin/admin_menu.html", user=user)

@bp.route('/admin_menu/<email>/door_list', methods=["GET", "POST"])
def door_list(email):
    form = DoorOpenForm()
    user = User.query.filter_by(email=email).first()
    
    if request.method == "POST":
        data_dict = {
            'area':request.form['area']
        }
        requests.post("http://43.200.247.167/door_open", data=data_dict)
        flash("열렸습니다.")
        redirect("#")
    
    return  render_template("admin/door_list.html", user=user, form=form)