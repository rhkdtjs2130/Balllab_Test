from crypt import methods
import urllib
import ast
import requests
import datetime

from flask import Blueprint, url_for, render_template, request, flash
from werkzeug.utils import redirect
# from datetime import datetime
from sqlalchemy import desc
from time import sleep

from app.models import User, BuyPoint, ReserveCourt, PayDB, DoorStatus
from app import db
from app.forms import DoorOpenForm, FilterReservationForm

timetable = [
    "00:00 ~ 00:30",
    "00:30 ~ 01:00",
    "01:00 ~ 01:30",
    "01:30 ~ 02:00",
    "02:00 ~ 02:30",
    "02:30 ~ 03:00",
    "03:00 ~ 03:30",
    "03:30 ~ 04:00",
    "04:00 ~ 04:30",
    "04:30 ~ 05:00",
    "05:00 ~ 05:30",
    "05:30 ~ 06:00",
    "06:00 ~ 06:30",
    "06:30 ~ 07:00",
    "07:00 ~ 07:30",
    "07:30 ~ 08:00",
    "08:00 ~ 08:30",
    "08:30 ~ 09:00",
    "09:00 ~ 09:30",
    "09:30 ~ 10:00",
    "10:00 ~ 10:30",
    "10:30 ~ 11:00",
    "11:00 ~ 11:30",
    "11:30 ~ 12:00",
    "12:00 ~ 12:30",
    "12:30 ~ 13:00",
    "13:00 ~ 13:30",
    "13:30 ~ 14:00",
    "14:00 ~ 14:30",
    "14:30 ~ 15:00",
    "15:00 ~ 15:30",
    "15:30 ~ 16:00",
    "16:00 ~ 16:30",
    "16:30 ~ 17:00",
    "17:00 ~ 17:30",
    "17:30 ~ 18:00",
    "18:00 ~ 18:30",
    "18:30 ~ 19:00",
    "19:00 ~ 19:30",
    "19:30 ~ 20:00",
    "20:00 ~ 20:30",
    "20:30 ~ 21:00",
    "21:00 ~ 21:30",
    "21:30 ~ 22:00",
    "22:00 ~ 22:30",
    "22:30 ~ 23:00",
    "23:00 ~ 23:30",
    "23:30 ~ 24:00",
]

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

@bp.route('/admin_reservation/<email>', methods=["GET", "POST"])
def admin_reservation(email):
    date = datetime.date.today()
    
    user = User.query.filter_by(email=email).first()
    
    reservation_table = ReserveCourt.query.filter_by(buy=1)\
        .filter(ReserveCourt.date >= date)\
        .order_by(ReserveCourt.date)\
        .order_by(ReserveCourt.time)\
        .all()
    
    form = FilterReservationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        reservation_table = ReserveCourt.query.filter_by(
                buy=1, 
                username=form.username.data, 
            ).filter(ReserveCourt.date == form.date.data)\
            .order_by(ReserveCourt.date)\
            .order_by(ReserveCourt.time)\
            .all()
        date = form.date.data
    
    return  render_template("admin/check_reservation.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form, cur_date=date)

@bp.route("/admin/refund_reservation/<email>/<mul_no>", methods=["GET", "POST"])
def refund_reservation(email, mul_no):
    pay_info = PayDB.query.filter_by(mul_no=mul_no).first()
    admin = User.query.filter_by(email=email).first()
    reservation_info = ReserveCourt.query.filter_by(mul_no=mul_no).order_by(ReserveCourt.time).all()
    
    if request.method == "POST":
        user = User.query.filter_by(phone=pay_info.recvphone).first()
        
        if pay_info.pay_type == "point_only":
            user.point = user.point + pay_info.used_point
            pay_info.pay_state = '64'
            db.session.commit()
            
            for reservation in reservation_info:
                reservation.buy = 0
                db.session.commit()
                
        else:
            key_info = "3c0VLPJBsy0//kO2e3TEe+1DPJnCCRVaOgT+oqg6zaM="
            
            post_data = {
                'cmd': 'paycancel',
                'userid': 'balllab',
                'linkkey': key_info,
                'mul_no':pay_info.mul_no,
                'cancelmemo': "관리자 예약 취소",
            }
            
            data = urllib.parse.urlencode(post_data).encode('utf-8')
            req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")
            
            with urllib.request.urlopen(req, data=data) as f:
                resp = urllib.parse.unquote_to_bytes(f.read())
                resp = resp.decode('utf-8')[6]
                print("TEST", "State = ", resp, "Test")
            
            sleep(1)
                
            user.point = user.point + pay_info.used_point
            db.session.commit()
            
            for reservation in reservation_info:
                reservation.buy = 0
                db.session.commit()
                
        flash("예약이 취소되었습니다. 포인트 반환 및 환불 처리가 완료되었습니다.")
        return redirect(url_for('admin.admin_reservation', email=admin.email))
    
    return render_template("admin/refund_reservation.html", admin=admin)

@bp.route('/admin/reservation_onoff', methods=['GET', 'POST'])
def reservation_onoff():
    return None