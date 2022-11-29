from crypt import methods
import urllib
import ast
import requests
import datetime

from flask import Blueprint, url_for, render_template, request, flash
from werkzeug.utils import redirect
from sqlalchemy import desc
from time import sleep

from app.models import User, ReserveCourt, PayDB, GrantPoint, PointTable, CourtPriceTable, ReservationStatus, CourtList
from app import db
from app.forms import DoorOpenForm, FilterReservationForm, UserFilterForm, ChangeUserInfoForm, ReserveCourtAreaDateForm, ReserveCourtTimeForm, ReserveCourtForm, PointManagementForm, CourtManagementForm, CourtOnOffForm, ReserveCourtCourtForm

## 코드 이용 시간 정의
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


@bp.route('/admin_menu/<phone>')
def admin_menu(phone: str):
    user = User.query.filter_by(phone=phone).first()
    return render_template("admin/admin_menu.html", user=user)


@bp.route('/admin_menu/<phone>/door_list', methods=["GET", "POST"])
def door_list(phone: str):
    form = DoorOpenForm()
    user = User.query.filter_by(phone=phone).first()

    if request.method == "POST":
        data_dict = {
            'area': request.form['area']
        }
        requests.post("http://43.200.247.167/door_open", data=data_dict)
        flash("열렸습니다.")
        redirect("#")

    return render_template("admin/door_list.html", user=user, form=form)


@bp.route('/admin_reservation/<phone>', methods=["GET", "POST"])
def admin_reservation(phone: str):
    date = datetime.date.today()

    user = User.query.filter_by(phone=phone).first()

    reservation_table = ReserveCourt.query.filter_by(buy=1)\
        .filter(ReserveCourt.date >= date)\
        .order_by(ReserveCourt.date)\
        .order_by(ReserveCourt.time)\
        .all()

    form = FilterReservationForm()

    if request.method == 'POST':

        if (form.date.data != None) and (form.username.data != '') and (form.phone.data != ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
                username=form.username.data,
                phone=form.phone.data,
            ).filter(ReserveCourt.date == form.date.data)\
                .order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data != None) and (form.username.data != "") and (form.phone.data == ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
                username=form.username.data,
            ).filter(ReserveCourt.date == form.date.data)\
                .order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data != None) and (form.username.data == '') and (form.phone.data != ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
                phone=form.phone.data,
            ).filter(ReserveCourt.date == form.date.data)\
                .order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data != None) and (form.username.data == '') and (form.phone.data == ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
            ).filter(ReserveCourt.date == form.date.data)\
                .order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data == None) and (form.username.data != '') and (form.phone.data != ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
                username=form.username.data,
                phone=form.phone.data,
            ).order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data == None) and (form.username.data != "") and (form.phone.data == ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
                username=form.username.data,
            ).order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data == None) and (form.username.data == '') and (form.phone.data != ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
                phone=form.phone.data,
            ).order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

        elif (form.date.data == None) and (form.username.data == '') and (form.phone.data == ''):
            reservation_table = ReserveCourt.query.filter_by(
                buy=1,
            ).order_by(ReserveCourt.date)\
                .order_by(ReserveCourt.time)\
                .all()
            date = form.date.data

    return render_template("admin/check_reservation.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form, cur_date=date)


@bp.route("/admin/refund_reservation/<phone>/<mul_no>", methods=["GET", "POST"])
def refund_reservation(phone: str, mul_no: str):
    pay_info = PayDB.query.filter_by(mul_no=mul_no).first()
    admin = User.query.filter_by(phone=phone).first()
    reservation_info = ReserveCourt.query.filter_by(
        mul_no=mul_no).order_by(ReserveCourt.time).all()

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
                'mul_no': pay_info.mul_no,
                'cancelmemo': "관리자 예약 취소",
            }

            data = urllib.parse.urlencode(post_data).encode('utf-8')
            req = urllib.request.Request(
                "http://api.payapp.kr/oapi/apiLoad.html")

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
        return redirect(url_for('admin.admin_reservation', phone=admin.phone))

    return render_template("admin/refund_reservation.html", admin=admin)


@bp.route('/admin/user_check/<phone>', methods=['GET', 'POST'])
def user_check(phone: str):
    user_table = User.query.all()
    admin = User.query.filter_by(phone=phone).first()
    form = UserFilterForm()

    if request.method == 'POST' and form.validate_on_submit():

        if form.username.data != "":
            user_table = User.query.filter_by(
                username=form.username.data).all()

        elif form.phone.data != "":
            user_table = User.query.filter_by(phone=form.phone.data).all()

    return render_template("admin/user_check.html", admin=admin, user_table=user_table, form=form)


@bp.route('/admin/user_check/change_user_info/<admin_phone>/<user_phone>', methods=['GET', 'POST'])
def change_user_info(admin_phone: str, user_phone: str):
    user = User.query.filter_by(phone=user_phone).first()
    form = ChangeUserInfoForm()

    if request.method == 'POST' and form.validate_on_submit():
        diff_point = form.point.data - user.point

        user.username = form.username.data
        user.phone = form.phone.data
        user.birth = form.birth.data
        user.point = form.point.data
        db.session.commit()

        admin = User.query.filter_by(phone=admin_phone).first()

        grant_point = GrantPoint(
            date=datetime.datetime.today(),
            admin_name=admin.username,
            admin_phone=admin.phone,
            user_name=user.username,
            user_phone=user.phone,
            point=diff_point,
        )
        db.session.add(grant_point)
        db.session.commit()

        flash("반영 되었습니다.")
        user = User.query.filter_by(phone=user_phone).first()

    return render_template("admin/change_user_info.html", user=user, admin_phone=admin_phone, form=form)


@bp.route('/admin/reserve_court/<admin_phone>/', methods=['GET', 'POST'])
def reserve_court(admin_phone: str):

    form = ReserveCourtAreaDateForm()
    cur_date = datetime.date.today()

    if request.method == 'POST' and form.validate_on_submit():
        return redirect(url_for('admin.reserve_court_time', admin_phone=admin_phone, court_area=form.area.data, court_date=form.date.data))

    return render_template("admin/reserve_court_area_date.html", form=form, cur_date=cur_date)


@bp.route('/admin/reserve_court_separate/<admin_phone>/', methods=['GET', 'POST'])
def reserve_court_separate(admin_phone: str):

    form = ReserveCourtAreaDateForm()
    cur_date = datetime.date.today()

    if request.method == 'POST' and form.validate_on_submit():
        return redirect(url_for('admin.reserve_court_select_separate', admin_phone=admin_phone, court_area=form.area.data, court_date=form.date.data))

    return render_template("admin/reserve_court_area_date.html", form=form, cur_date=cur_date)


@bp.route('/admin/reserve_court_select_separate/<admin_phone>/<court_area>/<court_date>', methods=['GET', 'POST'])
def reserve_court_select_separate(admin_phone: str, court_area: str, court_date: str):

    form = ReserveCourtCourtForm()

    court_status_table = ReservationStatus.query.filter_by(
        area=court_area, status="1").order_by(ReservationStatus.id).all()

    if request.method == 'POST' and form.validate_on_submit():
        court_area = court_area
        court_date = court_date
        court_name = form.court.data
        return redirect(url_for('admin.reserve_court_time_separate', admin_phone=admin_phone, court_area=court_area, court_date=court_date, court_name=court_name))

    return render_template("admin/reserve_court_select_separate.html", form=form, court_status_table=court_status_table)


@bp.route('/admin/reserve_court_separate/time/<court_area>/<court_name>/<court_date>/<admin_phone>', methods=['GET', 'POST'])
def reserve_court_time_separate(admin_phone: str, court_area: str, court_date: str, court_name: str):
    form = ReserveCourtTimeForm()
    court_info = ReserveCourt.query.filter_by(
        area=court_area, court=court_name, date=court_date, buy=1).all()
    court_info = [int(x.time) for x in court_info]

    if request.method == "POST" and form.validate_on_submit():
        reserve_times = request.form.getlist("time")
        return redirect(url_for("admin.reserve_court_check_separate", admin_phone=admin_phone, court_area=court_area, court_name=court_name, court_date=court_date, reserve_times=reserve_times))

    return render_template("admin/reserve_court_time.html", form=form, timetable=timetable, court_info=court_info)


@bp.route('/admin/reserve_court/time/<court_area>/<court_date>/<admin_phone>', methods=['GET', 'POST'])
def reserve_court_time(admin_phone: str, court_area: str, court_date: str):
    form = ReserveCourtTimeForm()
    court_info = ReserveCourt.query.filter_by(
        area=court_area, date=court_date, buy=1).all()
    court_info = [int(x.time) for x in court_info]

    if request.method == "POST" and form.validate_on_submit():
        reserve_times = request.form.getlist("time")
        return redirect(url_for("admin.reserve_court_check", admin_phone=admin_phone, court_area=court_area, court_date=court_date, reserve_times=reserve_times))

    return render_template("admin/reserve_court_time.html", form=form, timetable=timetable, court_info=court_info)


@bp.route("/admin/reserve_court_separate/reserve_court_check/<admin_phone>/<court_area>/<court_name>/<court_date>/<reserve_times>/", methods=('GET', 'POST'))
def reserve_court_check_separate(admin_phone: str, court_area: str, court_date: str, court_name: str, reserve_times: str):
    form = ReserveCourtForm()

    user = User.query.filter_by(phone=admin_phone).first()

    reserve_times = ast.literal_eval(reserve_times)

    if type(reserve_times) != int:
        tmp_list = []
        for reserv_time in reserve_times:
            tmp_list.append(int(reserv_time))
    else:
        tmp_list = [reserve_times]

    if len(tmp_list) > 1:
        total_reserve_time = len(tmp_list) / 2  # 시간
    else:
        total_reserve_time = 0.5

    court_price = CourtPriceTable.query.filter_by(
        area=court_area).first().price

    total_price = int(total_reserve_time * 2 * court_price)

    court_nm_list = [court_name]

    total_price = total_price * len(court_nm_list)

    if total_price >= user.point:
        total_pay = total_price - user.point
    elif user.point > total_price:
        total_pay = 0

    if request.method == 'POST':
        pay_db = PayDB.query.all()
        for court_nm in court_nm_list:
            for tmp_time in tmp_list:

                reserve_check = ReserveCourt.query.filter_by(
                    date=datetime.datetime.strptime(court_date, "%Y-%m-%d"),
                    area=court_area,
                    court=court_nm,
                    time=str(tmp_time),
                ).first()

                if reserve_check == None:
                    ## Reserve Court ##
                    court_reserve = ReserveCourt(
                        date=datetime.datetime.strptime(
                            court_date, "%Y-%m-%d"),
                        area=court_area,
                        time=str(tmp_time),
                        court=court_nm,
                        phone=user.phone,
                        email=user.email,
                        username=user.username,
                        mul_no=f"point_{len(pay_db)}",
                        buy=1,
                    )
                    db.session.add(court_reserve)
                    db.session.commit()
                else:
                    ## Reserve Court ##
                    reserve_check.buy = 1
                    reserve_check.mul_no = f"point_{len(pay_db)}"
                    db.session.commit()

        pay_add = PayDB(
            mul_no=f"point_{len(pay_db)}",
            goodname=f"관리자예약_{court_area}_{court_name}",
            date=datetime.datetime.strptime(court_date, "%Y-%m-%d"),
            area=court_area,
            time=str(tmp_list),
            price=total_pay,
            used_point=total_price,
            recvphone=user.phone,
            pay_date=datetime.datetime.now(),
            pay_type="point_only",
            pay_state="4",
        )

        db.session.add(pay_add)
        db.session.commit()

        if user.point >= int(total_price):
            user.point = user.point - int(total_price)
        else:
            user.point = 0

        db.session.commit()

        flash("예약 되었습니다.")

        return redirect(url_for("admin.admin_menu", phone=admin_phone))

    return render_template("admin/reserve_court_check.html", form=form, user=user, court_area=court_area, court_name=court_name, court_date=court_date, total_reserve_time=total_reserve_time, total_price=total_price, total_pay=total_pay, tmp_list=tmp_list, timetable=timetable)


@bp.route("/admin/reserve_court/reserve_court_check/<admin_phone>/<court_area>/<court_date>/<reserve_times>/", methods=('GET', 'POST'))
def reserve_court_check(admin_phone: str, court_area: str, court_date: str, reserve_times: str):
    form = ReserveCourtForm()

    user = User.query.filter_by(phone=admin_phone).first()

    reserve_times = ast.literal_eval(reserve_times)

    if type(reserve_times) != int:
        tmp_list = []
        for reserv_time in reserve_times:
            tmp_list.append(int(reserv_time))
    else:
        tmp_list = [reserve_times]

    if len(tmp_list) > 1:
        total_reserve_time = len(tmp_list) / 2  # 시간
    else:
        total_reserve_time = 0.5

    court_price = CourtPriceTable.query.filter_by(
        area=court_area).first().price

    total_price = int(total_reserve_time * 2 * court_price)

    court_tmp = ReservationStatus.query.filter_by(area=court_area).all()
    court_nm_list = [court.court_nm for court in court_tmp]

    total_price = total_price * len(court_nm_list)

    if total_price >= user.point:
        total_pay = total_price - user.point
    elif user.point > total_price:
        total_pay = 0

    if request.method == 'POST':
        pay_db = PayDB.query.all()
        for court_nm in court_nm_list:
            for tmp_time in tmp_list:

                reserve_check = ReserveCourt.query.filter_by(
                    date=datetime.datetime.strptime(court_date, "%Y-%m-%d"),
                    area=court_area,
                    court=court_nm,
                    time=str(tmp_time),
                ).first()

                if reserve_check == None:
                    ## Reserve Court ##
                    court_reserve = ReserveCourt(
                        date=datetime.datetime.strptime(
                            court_date, "%Y-%m-%d"),
                        area=court_area,
                        time=str(tmp_time),
                        court=court_nm,
                        phone=user.phone,
                        email=user.email,
                        username=user.username,
                        mul_no=f"point_{len(pay_db)}",
                        buy=1,
                    )
                    db.session.add(court_reserve)
                    db.session.commit()
                else:
                    ## Reserve Court ##
                    reserve_check.buy = 1
                    reserve_check.mul_no = f"point_{len(pay_db)}"
                    db.session.commit()

        pay_add = PayDB(
            mul_no=f"point_{len(pay_db)}",
            goodname=f"관리자예약_{court_area}_전체",
            date=datetime.datetime.strptime(court_date, "%Y-%m-%d"),
            area=court_area,
            time=str(tmp_list),
            price=total_pay,
            used_point=total_price,
            recvphone=user.phone,
            pay_date=datetime.datetime.now(),
            pay_type="point_only",
            pay_state="4",
        )

        db.session.add(pay_add)
        db.session.commit()

        if user.point >= int(total_price):
            user.point = user.point - int(total_price)
        else:
            user.point = 0

        db.session.commit()

        flash("예약 되었습니다.")

        return redirect(url_for("admin.admin_menu", phone=admin_phone))

    return render_template("admin/reserve_court_check.html", form=form, user=user, court_area=court_area, court_name=court_nm_list, court_date=court_date, total_reserve_time=total_reserve_time, total_price=total_price, total_pay=total_pay, tmp_list=tmp_list, timetable=timetable)


@bp.route('/admin/product_management/<admin_phone>/', methods=['GET', 'POST'])
def product_management(admin_phone: str):
    user = User.query.filter_by(phone=admin_phone).first()
    return render_template("admin/product_management.html", user=user)


@bp.route('/admin/point_price_management/<admin_phone>/', methods=['GET', 'POST'])
def point_price_management(admin_phone: str):
    user = User.query.filter_by(phone=admin_phone).first()
    point_table = PointTable.query.order_by(PointTable.price).all()
    return render_template("admin/point_price_management.html", user=user, point_table=point_table)


@bp.route('/admin/point_price_change_management/<admin_phone>/<price>', methods=['GET', 'POST'])
def point_price_change_management(admin_phone: str, price: str):
    form = PointManagementForm()
    user = User.query.filter_by(phone=admin_phone).first()
    point_table = PointTable.query.filter_by(price=price).first()

    if request.method == 'POST' and form.validate_on_submit():
        point_table.point = form.point.data
        db.session.commit()
        flash("수정 완료되었습니다.")

    return render_template("admin/point_price_change_management.html", user=user, point_table=point_table, form=form)


@bp.route('/admin/court_price_management/<admin_phone>/', methods=['GET', 'POST'])
def court_price_management(admin_phone: str):
    user = User.query.filter_by(phone=admin_phone).first()
    court_table = CourtPriceTable.query.order_by(CourtPriceTable.id).all()
    return render_template("admin/court_price_management.html", user=user, court_table=court_table)


@bp.route('/admin/court_price_management/<court_area>/<admin_phone>/', methods=['GET', 'POST'])
def court_price_change_management(admin_phone: str, court_area: str):
    form = CourtManagementForm()
    user = User.query.filter_by(phone=admin_phone).first()
    court_table = CourtPriceTable.query.filter_by(area=court_area).first()

    if request.method == 'POST' and form.validate_on_submit():
        court_table.price = form.price.data
        db.session.commit()
        flash("수정 완료되었습니다.")

    return render_template("admin/court_price_change_management.html", user=user, court_table=court_table, form=form)


@bp.route('/admin/court_management/<admin_phone>/', methods=['GET', 'POST'])
def court_management(admin_phone: str):

    user = User.query.filter_by(phone=admin_phone).first()
    court_table = CourtList.query.order_by(CourtList.id).all()

    return render_template("admin/court_management.html", user=user, court_table=court_table)


@bp.route('/admin/court_status_management/<court_area>/<admin_phone>/', methods=['GET', 'POST'])
def court_status_management(admin_phone: str, court_area: str):

    user = User.query.filter_by(phone=admin_phone).first()
    court_table = ReservationStatus.query.filter_by(
        area=court_area).order_by(ReservationStatus.id).all()

    return render_template("admin/court_status_management.html", user=user, court_table=court_table)


@bp.route('/admin/court_onoff/<court_area>/<court_nm>/<admin_phone>/', methods=['GET', 'POST'])
def court_status_onoff(admin_phone: str, court_area: str, court_nm: str):

    form = CourtOnOffForm()

    user = User.query.filter_by(phone=admin_phone).first()
    court_table = ReservationStatus.query.filter_by(
        area=court_area, court_nm=court_nm).first()

    if request.method == "POST" and form.validate_on_submit():
        court_table.status = form.status.data
        db.session.commit()

        if form.status.data == "1":
            flash("예약 오픈 되었습니다.")
        else:
            flash("예약 클로즈 되었습니다.")

    return render_template("admin/court_status_onoff.html", user=user, court_table=court_table, form=form)
