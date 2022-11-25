import urllib
import ast
import requests
import datetime
import ast

from flask import Blueprint, url_for, render_template, request, flash
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import desc
from time import sleep

from app.models import User, BuyPoint, ReserveCourt, PayDB, DoorStatus, PointTable, CourtPriceTable, ReservationStatus
from app import db
from app.forms import BuyPointForm, ReserveCourtAreaDateForm, ReserveCourtCourtForm, ReserveCourtForm, ReserveCourtTimeForm, DoorOpenForm, ChangePasswordForm

bp = Blueprint("main", __name__, url_prefix='/')

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

door_map_dict = {
    "1번":"center_1",
    "2번":"center_1",
    "3번":"center_1",
    '3층':'center_2_3f',
    '4층':'center_2_4f',
}


@bp.route('/')
def login_page():
    return redirect(url_for("auth.login_form"))

@bp.route('/user_menu/<phone>')
def user_menu(phone):
    user = User.query.filter_by(phone=phone).first()
    return  render_template("user/user_menu.html", user=user)

@bp.route('/user_menu/<phone>/buy_point/', methods=('GET', 'POST'))
def buy_point(phone):
    form = BuyPointForm()
    user = User.query.filter_by(phone=phone).first()
    date = datetime.date.today()
    
    point_tables = PointTable.query.order_by(PointTable.price).all()
    
    buy_point_list = BuyPoint.query.filter_by(
        phone=user.phone, 
        # date=date,
    ).all()
    
    if request.method == "POST" and form.validate_on_submit():
        
        price = form.price.data
        product = PointTable.query.filter_by(price=price).first().point
        
        if len(buy_point_list) == 0:
            time = 1
        else:
            time = len(buy_point_list) + 1
        
        time = f"point_{time}"
        
        post_data = (
            {
                'cmd': 'payrequest',
                'userid': 'newballlab',
                'goodname': f"{product} LUV", 
                'price': price, 
                'recvphone': user.phone,
                "skip_cstpage":"y",
                "memo": f"주식회사볼랩_포인트 0",
                "var1": date,
                "var2": time,
            }
        )
    
        data = urllib.parse.urlencode(post_data).encode('utf-8')
        req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")
        
        with urllib.request.urlopen(req, data=data) as f:
            resp = urllib.parse.unquote_to_bytes(f.read())
            resp = resp.decode('utf-8')[6]
            print("TEST", "State = ", resp, "Test")
        
        if resp == "1":
            return redirect(url_for("main.request_pay_point", phone=user.phone, product=product, price=price, date=date, time=time))
        else:
            redirect("#")
        
    return  render_template("user/buy_point.html", user=user, form=form, point_tables=point_tables)


@bp.route('/user_menu/<phone>/<product>/<price>/<date>/<time>/request_pay/point', methods=('GET', 'POST'))
def request_pay_point(phone, product, price, date, time):
    
    if request.method == 'POST':
        user = User.query.filter_by(phone=phone).first()
        
        paycheck = PayDB.query.filter_by(
            recvphone=user.phone,
            goodname=f"{product} LUV",
            time=time,
        ).order_by(PayDB.pay_date.desc()).all()
        
        if len(paycheck) == 1:        
            if paycheck[0].pay_state == "4":
                return redirect(url_for("main.confirm_pay", phone=user.phone))
        else:
            flash("결제가 완료되지 않았습니다.")
            return redirect("#")
    
    return render_template("user/request_pay_point.html")

@bp.route("/user_menu/<phone>/confirm_pay", methods=('GET', 'POST'))
def confirm_pay(phone):
    
    user = User.query.filter_by(phone=phone).first()
    
    return render_template("user/confirm_pay.html", user=user)


### Reserve Court ###

@bp.route("/user_menu/<phone>/reserve_court/select_area_date", methods=('GET', 'POST'))
def reserve_court_area_date(phone):
    form = ReserveCourtAreaDateForm()
    user = User.query.filter_by(phone=phone).first()
    today_tmp = datetime.date.today()
    cur_date = today_tmp.strftime("%Y-%m-%d")
    max_date = (today_tmp + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    if request.method == 'POST' and form.validate_on_submit():
        area = form.area.data
        date = form.date.data
        return redirect(url_for("main.reserve_court_court", phone=user.phone, area=area, date=date))
    
    return render_template("user/reserve_court_area_date.html", form=form, cur_date=cur_date, max_date=max_date)

@bp.route("/user_menu/<phone>/<area>/<date>/reserve_court/select_court", methods=('GET', 'POST'))
def reserve_court_court(phone, area, date):
    form = ReserveCourtCourtForm()
    
    ## Get information about court reservations
    court = ReserveCourt.query.filter_by(area=area, date=date)
    user = User.query.filter_by(phone=phone).first()
    
    court_status_table = ReservationStatus.query.filter_by(area=area, status="1").order_by(ReservationStatus.id).all()
    
    if request.method == 'POST' and form.validate_on_submit():
        court_area = area
        court_date = date
        court_name = form.court.data
        return redirect(url_for("main.reserve_court_time", phone=user.phone, court_area=court_area, court_date=court_date, court_name=court_name))
    
    return render_template("user/reserve_court_court.html", form=form, court_status_table=court_status_table, court=court)

@bp.route("/user_menu/<phone>/<court_area>/<court_date>/<court_name>/select_time", methods=('GET', 'POST'))
def reserve_court_time(phone, court_area, court_date, court_name):
    form = ReserveCourtTimeForm()
    
    ## Get information about court reservations
    court_info = ReserveCourt.query.filter_by(area=court_area, date=court_date, court=court_name, buy=1).all()
    user = User.query.filter_by(phone=phone).first()
    
    court_info = [int(x.time) for x in court_info]

    is_today = datetime.datetime.today()
    court_day = datetime.datetime.strptime(court_date, '%Y-%m-%d').date()
    
    if court_day == is_today.date():
        if is_today.hour >= 10:
            hour = f"{is_today.hour}:00"
        else:
            hour = f"0{is_today.hour}:00"
            
        block_begin = max([n for n, x in enumerate(timetable) if hour in x]) + 1
        block_table = [n for n in range(block_begin)]
        
        court_info = court_info + block_table
        
    
    if request.method == 'POST' and form.validate_on_submit():
        reserve_times = request.form.getlist("time")
        return redirect(url_for("main.reserve_court", phone=user.phone, court_area=court_area, court_date=court_date, court_name=court_name, reserve_times=reserve_times))
    
    return render_template("user/reserve_court_time.html", form=form, court_info=court_info, timetable=timetable)

@bp.route("/user_menu/<phone>/<court_area>/<court_date>/<court_name>/<reserve_times>/reserve_court", methods=('GET', 'POST'))
def reserve_court(phone, court_area, court_date, court_name, reserve_times):
    form = ReserveCourtForm()
    
    user = User.query.filter_by(phone=phone).first()
    
    reserve_times = ast.literal_eval(reserve_times)
    
    if type(reserve_times) != int:
        tmp_list = []
        for reserv_time in reserve_times:
            tmp_list.append(int(reserv_time))
    else:
        tmp_list = [reserve_times]
        
    if len(tmp_list) > 1:
        total_reserve_time = len(tmp_list) / 2 ## 시간
    else:
        total_reserve_time = 0.5
    
    court_price = CourtPriceTable.query.filter_by(area = court_area).first().price
    
    total_price = int(total_reserve_time * 2 * court_price)
    
    if total_price >= user.point:
        total_pay = total_price - user.point
        used_point = user.point
    elif user.point > total_price:
        total_pay = 0
        used_point = user.point - total_price
        
    if request.method == 'POST':
        for tmp_time in tmp_list:
            
            reserve_check = ReserveCourt.query.filter_by(
                date=datetime.datetime.strptime(court_date, "%Y-%m-%d"), 
                area=court_area, 
                court=court_name,
                time=str(tmp_time),
                buy=1,
            ).first()
            
            if reserve_check == None:
                ## Reserve Court ##
                court_reserve = ReserveCourt(
                    date = datetime.datetime.strptime(court_date, "%Y-%m-%d"),
                    area = court_area, 
                    time = str(tmp_time),
                    court = court_name, 
                    phone = user.phone, 
                    email = user.email, 
                    username = user.username, 
                    buy = 0, 
                )
                db.session.add(court_reserve)
                db.session.commit()
            else:
                continue
            
        tmp_list = [str(x) for x in tmp_list]
        
        if total_pay != 0:
            
            if court_area == "어린이대공원점":
                user_id = "newballlab"
            elif court_area == "성수자양점":
                user_id = "balllabss"
            
            post_data = (
                {
                    'cmd': 'payrequest',
                    'userid': user_id,
                    'goodname': court_name, 
                    'price': total_pay,
                    'recvphone': user.phone,
                    "skip_cstpage":"y",
                    "memo": f"{court_area} {used_point} {total_price}",
                    "var1": court_date,
                    "var2": str(tmp_list),
                }
            )
                
            data = urllib.parse.urlencode(post_data).encode('utf-8')
            req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")
            
            with urllib.request.urlopen(req, data=data) as f:
                resp = urllib.parse.unquote_to_bytes(f.read())
                resp = resp.decode('utf-8')[6]
                print("TEST", "State = ", resp, "Test")
            
            return redirect(url_for("main.request_pay_court", phone=user.phone, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_price, total_pay=total_pay))
        
        else:
            return redirect(url_for("main.request_pay_court", phone=user.phone, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_price, total_pay=total_pay))
    
    return render_template("user/reserve_court.html", form=form, user=user, court_area=court_area, court_name=court_name, court_date=court_date, total_reserve_time=total_reserve_time, total_price=total_price, total_pay=total_pay, tmp_list=tmp_list, timetable=timetable)


@bp.route('/user_menu/<phone>/<date>/<area>/<time>/<court>/<total_pay>/<total_price>/request_pay/court', methods=('GET', 'POST'))
def request_pay_court(phone, date, area, time, court, total_pay, total_price):
    tmp_time = ast.literal_eval(time)
    if type(tmp_time) == int:
        tmp_time = [tmp_time]
    user = User.query.filter_by(phone=phone).first()
    reservation_table = ReserveCourt.query.filter_by(date=date, phone=phone, area=area, court=court)\
        .filter(ReserveCourt.time.in_(tmp_time))\
        .all()

    if (request.method == 'POST'):
        
        if total_pay != "0":
            paycheck = PayDB.query.filter_by(
                recvphone=user.phone,
                goodname=court,
                date=date,
                area=area,
                time=time, 
                price=total_pay,
                used_point=str(int(total_price) - int(total_pay)),
            ).order_by(PayDB.mul_no.desc()).first()
            
            if paycheck != None:
                return redirect(url_for("main.confirm_pay", phone=user.phone))
            else:
                flash("결제가 완료되지 않았습니다.")
                return redirect("#")
        else:
            pay_db = PayDB.query.all()
            
            pay_add = PayDB(
                mul_no = f"point_{len(pay_db)}",
                goodname = court,
                date = datetime.datetime.strptime(date, "%Y-%m-%d"),
                area = area,
                time = time,
                price = total_pay,
                used_point = total_price,
                recvphone = user.phone,
                pay_date = datetime.datetime.now(), 
                pay_type = "point_only",
                pay_state = "4",
            )
            
            db.session.add(pay_add)
            db.session.commit()
            
            for reservation in reservation_table:
                reservation.buy = 1
                reservation.mul_no = f"point_{len(pay_db)}"
                
                db.session.commit()
                        
            if user.point >= int(total_price):
                user.point = user.point - int(total_price)
            else:
                user.point = 0
                
            db.session.commit()
                
            return redirect(url_for("main.confirm_pay", phone=user.phone))
            
    
    return render_template("user/request_pay_court.html", total_pay=total_pay)


@bp.route("/user_menu/check_reservation/<phone>", methods=["GET", "POST"])
def check_reservation(phone):
    form = DoorOpenForm()
    date = datetime.date.today()
    
    user = User.query.filter_by(phone=phone).first()
    
    reservation_table = ReserveCourt.query.filter_by(phone=phone, buy=1)\
        .filter(ReserveCourt.date >= date)\
        .order_by(ReserveCourt.date)\
        .order_by(ReserveCourt.time)\
        .all()
        
    if request.method == "POST":
        time_tmp = timetable[int(request.form['time'])]
        time_start = time_tmp.split()[0]
        time_end = time_tmp.split()[-1]
        
        time_str = f"{request.form['date']} {time_start}"
        date_time_start = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        date_time_start = date_time_start - datetime.timedelta(minutes=5)
        
        time_str = f"{request.form['date']} {time_end}"
        date_time_end = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        date_time_end = date_time_end + datetime.timedelta(minutes=5)
        
        cur_date = datetime.datetime.today()
        
        if (cur_date >= date_time_start) and (cur_date <= date_time_end):
            data_dict = {
                'area': door_map_dict[request.form['area']],
            }
            requests.post("http://43.200.247.167/door_open", data=data_dict)
            flash("열렸습니다")
            redirect("#")
        else:
            error = "이용 가능한 시간이 아닙니다."
            flash(error)
    
    return render_template("user/check_reservation.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)
    
    

@bp.route("/pay_check", methods=["POST"])
def pay_check():
    key_info = [
        "lV7FSRjIxUq4b+2PiWlgge1DPJnCCRVaOgT+oqg6zaM=", ## 어린이대공원점
        "K8PbtiU4wqJXpMBfBwWSPO1DPJnCCRVaOgT+oqg6zaM=", ## 성수자양점
    ]
    value_info = [
        "lV7FSRjIxUq4b+2PiWlggUdrk/uKlhCLAkjn5E6oM7w=", ## 어린이대공원점
        "K8PbtiU4wqJXpMBfBwWSPDtOlrsKL7Aq6S3j3uVtLKc=", ## 성수자양점
    ]
    
    if (request.form["linkkey"] in key_info) and (request.form["linkval"] in value_info) and (request.form['pay_state'] == "4"):
        
        db_update = PayDB(
            mul_no = request.form['mul_no'],
            goodname = request.form['goodname'],
            date = datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d'),
            area = request.form['memo'].split()[0],
            time = request.form['var2'],
            price = request.form['price'],
            recvphone = request.form['recvphone'],
            pay_date = datetime.datetime.strptime(request.form['pay_date'], '%Y-%m-%d %H:%M:%S'),
            pay_type = request.form['pay_type'],
            pay_state = request.form['pay_state'],
            used_point = int(request.form['memo'].split()[1]),
        )
            
        db.session.add(db_update)
        db.session.commit()
        
        user = User.query.filter_by(phone=request.form['recvphone']).first()
        
        ## Point
        if request.form['memo'] == f"주식회사볼랩_포인트 0":
            
            point_price = int(request.form['price'])
            point_date = datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d')
            time = request.form['var2']
            
            product = PointTable.query.filter_by(price=point_price).first().point
            
            is_record = BuyPoint.query.filter_by(
                phone=user.phone,
                time = time,
            ).first()
            
            if is_record is None:
                ## Assgin Point First
                user.point += int(product)
                db.session.commit()
                
                ## Add Logs
                record = BuyPoint(
                    phone=user.phone,
                    email=user.email,
                    username= user.username,
                    price=point_price,
                    product=f"{product} LUV",
                    area="주식회사볼랩",
                    date=point_date,
                    buy = 1, 
                    time=time,
                )
                
                db.session.add(record)
                db.session.commit()
            
        ## Regrestration Court
        else:
            registration_date = datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d')
            registration_area =  request.form['memo'].split()[0]
            registration_court = request.form['goodname']
            registration_time = ast.literal_eval(request.form['var2'])
            registration_total_price = request.form['memo'].split()[2]
            
            reservation_table = ReserveCourt.query.filter_by(
                phone=request.form['recvphone'],
                date=registration_date, 
                area=registration_area, 
                court=registration_court
            ).filter(ReserveCourt.time.in_(registration_time)).all()
            
            for reservation in reservation_table:
                reservation.buy = 1
                reservation.mul_no = request.form['mul_no']
                
                db.session.commit()
                
            if user.point >= int(registration_total_price):
                user.point = user.point - int(registration_total_price)
            else:
                user.point = 0
                
            db.session.commit()
        
        return "SUCCESS"
    
    ## Refund
    elif (request.form["linkkey"] in key_info) and (request.form["linkval"] in value_info) and (request.form['pay_state'] == "9" or request.form['pay_state'] == "64"):
        
        pay_info = PayDB.query.filter_by(mul_no=request.form['mul_no']).first()
        pay_info.pay_state = request.form['pay_state']
        db.session.commit()
        return "SUCCESS"
        
    else:
        return "FAIL"

## Door Open
@bp.route("/door_open", methods=["POST"])
def door_open():
    
    area = request.form['area']
    doorstatus = DoorStatus.query.filter_by(area=area).first()
    doorstatus.status = "1"
    db.session.commit()
    
    return "Open Door"

## Door Close
@bp.route("/door_close", methods=["POST"])
def door_close():
    
    area = request.form['area']
    doorstatus = DoorStatus.query.filter_by(area=area).first()
    doorstatus.status = "0"
    db.session.commit()
    
    return "Close Door"

@bp.route("/get_door_status", methods=["POST"])
def get_door_status():
    
    area = request.form['area']
    doorstatus = DoorStatus.query.filter_by(area=area).first()
    
    return doorstatus.status

@bp.route("/refund_reservation/<phone>/<mul_no>", methods=["GET", "POST"])
def refund_reservation(phone, mul_no):
    
    user = User.query.filter_by(phone=phone).first()
    pay_info = PayDB.query.filter_by(mul_no=mul_no).first()
    reservation_info = ReserveCourt.query.filter_by(mul_no=mul_no).order_by(ReserveCourt.time).all()
    
    if request.method == "POST":
        
        reservation_first = reservation_info[0]
        
        time_tmp = timetable[int(reservation_first.time)]
        time_start = time_tmp.split()[0]
        
        time_str = f"{reservation_first.date} {time_start}"
        date_time_start = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        refund_due_date = date_time_start - datetime.timedelta(days=2)
        
        cur_date = datetime.datetime.now()
        
        if cur_date < refund_due_date:
        
            if pay_info.pay_type == "point_only":
                user.point = user.point + pay_info.used_point
                pay_info.pay_state = '64'
                db.session.commit()
                
                for reservation in reservation_info:
                    reservation.buy = 0
                    db.session.commit()
                    
            else:
                if pay_info.area == "어린이대공원점":
                    user_id = "newballlab"
                    key_info = "lV7FSRjIxUq4b+2PiWlgge1DPJnCCRVaOgT+oqg6zaM="
                    
                elif pay_info.area == "성수자양점":
                    user_id = "balllabss"
                    key_info = "K8PbtiU4wqJXpMBfBwWSPO1DPJnCCRVaOgT+oqg6zaM="
                
                post_data = {
                    'cmd': 'paycancel',
                    'userid': user_id,
                    'linkkey': key_info,
                    'mul_no':pay_info.mul_no,
                    'cancelmemo': "48시간 전 예약 취소",
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
            return redirect(url_for('main.check_reservation', phone=user.phone))
        else:
            flash("이용 예정 시각과 현재 시각과의 차이가 48시간 이내이므로 예약 취소가 불가능합니다.")
            return redirect(url_for('main.check_reservation', phone=user.phone))
    
    return render_template("user/refund_reservation.html", user=user)

@bp.route("/change_password/<phone>", methods=["GET", "POST"])
def change_password(phone):
    user = User.query.filter_by(phone=phone).first()
    form = ChangePasswordForm()
    
    if request.method == "POST" and form.validate_on_submit():
        if check_password_hash(user.password, form.new_password1.data):
            flash("이전 비밀번호와 새 비밀번호가 일치합니다.")
            return redirect("#")
        if check_password_hash(user.password, form.before_password.data):
            user.password = generate_password_hash(form.new_password1.data)
            user.password_date = datetime.date.today()
            db.session.commit()
            flash("비밀번호 변경이 완료되었습니다. 바뀐 비밀번호로 로그인해주세요.")
            return redirect(url_for("auth.login_form"))
        else:
            flash("이전 비밀번호가 일치하지 않습니다.")
            return redirect("#")
    
    return render_template("user/change_password.html", user=user, form=form)