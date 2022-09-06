import urllib
import ast
import requests
import datetime

from flask import Blueprint, url_for, render_template, request, flash
from werkzeug.utils import redirect
# from datetime import datetime
from sqlalchemy import desc

from app.models import User, BuyPoint, ReserveCourt, PayDB
from app import db
from app.forms import BuyPointForm, ReserveCourtAreaDateForm, ReserveCourtCourtForm, ReserveCourtForm, ReserveCourtTimeForm
from ..qr_generate import make_qr_code, decode_qr

bp = Blueprint("main", __name__, url_prefix='/')

price_to_point_dict = {
    10000:"10000 LUV",
    30000:"33000 LUV",
    50000:"55000 LUV",
    70000:"77000 LUV",
    100000:"110000 LUV", 
}

price_to_point = {
    10000:10000,
    30000:33000,
    50000:55000,
    70000:77000,
    100000:110000, 
}

area_to_court_dict = {
    "어린이대공원점": ['1번 코트', '2번 코트', '3번 코트'], 
    "성수자양점": ['3층 (1번코트)', '4층 (2번 코트)']
}

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



@bp.route('/')
def login_page():
    return redirect(url_for("auth.login_form"))

@bp.route('/user_menu/<email>')
def user_menu(email):
    user = User.query.filter_by(email=email).first()
    return  render_template("user/user_menu.html", user=user)

@bp.route('/user_menu/<email>/buy_point/', methods=('GET', 'POST'))
def buy_point(email):
    form = BuyPointForm()
    user = User.query.filter_by(email=email).first()
    date = datetime.date.today()
    
    buy_point_list = BuyPoint.query.filter_by(
        email=user.email, 
        date=date,
    ).all()
    
    if request.method == "POST" and form.validate_on_submit():
        
        price = form.price.data
        product = price_to_point_dict[price]
        
        if len(buy_point_list) == 0:
            time = 1
        else:
            time = len(buy_point_list) + 1
        
        record = BuyPoint(
            phone=user.phone,
            email=user.email,
            username= user.username,
            price=price,
            product=product,
            area="주식회사볼랩",
            date=date,
            time=time,
            buy=0,
        )
        db.session.add(record)
        db.session.commit()
        
        post_data = (
            {
                'cmd': 'payrequest',
                'userid': 'balllab',
                'goodname': product, 
                # 'price': price, 
                'price': 1000, 
                'recvphone': user.phone,
                "skip_cstpage":"y",
                "memo": "주식회사볼랩",
                "var1": date,
                "var2": time,
                "feedback_url":"#"
            }
        )
    
        data = urllib.parse.urlencode(post_data).encode('utf-8')
        req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")
        
        with urllib.request.urlopen(req, data=data) as f:
            resp = urllib.parse.unquote_to_bytes(f.read())
            resp = resp.decode('utf-8')[6]
            print("TEST", "State = ", resp, "Test")
        
        if resp == "1":
            return redirect(url_for("main.request_pay_point", email=user.email, product=product, price=price, date=date, time=time))
        else:
            redirect("#")
        
    return  render_template("user/buy_point.html", user=user, form=form)


@bp.route('/user_menu/<email>/<product>/<price>/<date>/<time>/request_pay/point', methods=('GET', 'POST'))
def request_pay_point(email, product, price, date, time):
    
    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        
        paycheck = PayDB.query.filter_by(
            recvphone=user.phone,
            goodname=product,
            date=date,
            time=time,
        ).all()
        
        buypointcheck = BuyPoint.query.filter_by(
            email=user.email,
            date=date,
            time=time,
        ).all()
        
        if len(paycheck) == 1:        
            if paycheck[0].pay_state == "4":
                user.point += price_to_point[int(price)]
                buypointcheck[0].buy = 1
                db.session.commit()
                    
                return redirect(url_for("main.confirm_pay", email=user.email))
        else:
            flash("결제가 완료되지 않았습니다.")
            return redirect("#")
    
    return render_template("user/request_pay_point.html")

@bp.route("/user_menu/<email>/confirm_pay", methods=('GET', 'POST'))
def confirm_pay(email):
    
    user = User.query.filter_by(email=email).first()
    
    return render_template("user/confirm_pay.html", user=user)


### Reserve Court ###

@bp.route("/user_menu/<email>/reserve_court/select_area_date", methods=('GET', 'POST'))
def reserve_court_area_date(email):
    form = ReserveCourtAreaDateForm()
    user = User.query.filter_by(email=email).first()
    
    if request.method == 'POST' and form.validate_on_submit():
        area = form.area.data
        date = form.date.data
        return redirect(url_for("main.reserve_court_court", email=user.email, area=area, date=date))
    
    return render_template("user/reserve_court_area_date.html", form=form)

@bp.route("/user_menu/<email>/<area>/<date>/reserve_court/select_court_court", methods=('GET', 'POST'))
def reserve_court_court(email, area, date):
    form = ReserveCourtCourtForm()
    
    ## Get information about court reservations
    court = ReserveCourt.query.filter_by(area=area, date=date)
    user = User.query.filter_by(email=email).first()
    
    area_condition = area_to_court_dict[area]
    
    if request.method == 'POST' and form.validate_on_submit():
        court_area = area
        court_date = date
        court_name = form.court.data
        return redirect(url_for("main.reserve_court_time", email=user.email, court_area=court_area, court_date=court_date, court_name=court_name))
    
    return render_template("user/reserve_court_court.html", form=form, area_condition=area_condition, court=court)

@bp.route("/user_menu/<email>/<court_area>/<court_date>/<court_name>/select_time", methods=('GET', 'POST'))
def reserve_court_time(email, court_area, court_date, court_name):
    form = ReserveCourtTimeForm()
    
    ## Get information about court reservations
    court_info = ReserveCourt.query.filter_by(area=court_area, date=court_date, court=court_name, buy=1).all()
    user = User.query.filter_by(email=email).first()
    
    court_info = [int(x.time) for x in court_info]
    
    if request.method == 'POST' and form.validate_on_submit():
        reserve_times = request.form.getlist("time")
        return redirect(url_for("main.reserve_court", email=user.email, court_area=court_area, court_date=court_date, court_name=court_name, reserve_times=reserve_times))
    
    return render_template("user/reserve_court_time.html", form=form, court_info=court_info, timetable=timetable)

@bp.route("/user_menu/<email>/<court_area>/<court_date>/<court_name>/<reserve_times>/reserve_court", methods=('GET', 'POST'))
def reserve_court(email, court_area, court_date, court_name, reserve_times):
    form = ReserveCourtForm()
    
    user = User.query.filter_by(email=email).first()
    
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
        
    if court_area == "어린이대공원점":
        court_price = 10000
    else:
        court_price = 20000
    
    total_price = int(total_reserve_time * 2 * court_price)
    
    if total_price >= user.point:
        total_pay = total_price - user.point
    elif user.point > total_price:
        total_pay = 0
        
    if request.method == 'POST':
        for tmp_time in tmp_list:
            
            reserve_check = ReserveCourt.query.filter_by(
                date=datetime.datetime.strptime(court_date, "%Y-%m-%d"), 
                area=court_area, 
                court=court_name,
                time=tmp_time,
            ).first()
            
            if reserve_check == None:
                ## Reserve Court ##
                court_reserve = ReserveCourt(
                    date = datetime.datetime.strptime(court_date, "%Y-%m-%d"),
                    area = court_area, 
                    time = tmp_time,
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
        
        post_data = (
            {
                'cmd': 'payrequest',
                'userid': 'balllab',
                'goodname': court_name, 
                # 'price': total_price,
                'price': 1000, 
                'recvphone': user.phone,
                "skip_cstpage":"y",
                "memo": court_area,
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
        
        return redirect(url_for("main.request_pay_court", email=user.email, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_pay))
    
    return render_template("user/reserve_court.html", form=form, user=user, court_area=court_area, court_name=court_name, court_date=court_date, total_reserve_time=total_reserve_time, total_price=total_price, total_pay=total_pay, tmp_list=tmp_list, timetable=timetable)


@bp.route('/user_menu/<email>/<date>/<area>/<time>/<court>/<total_price>/request_pay/court', methods=('GET', 'POST'))
def request_pay_court(email, date, area, time, court, total_price):
    user = User.query.filter_by(email=email).first()
    reservation_table = ReserveCourt.query.filter_by(date=date, area=area, court=court)\
        .filter(ReserveCourt.time.in_(ast.literal_eval(time)))\
        .all()

    if (request.method == 'POST'):
        
        paycheck = PayDB.query.filter_by(
            recvphone=user.phone,
            goodname=court,
            date=date,
            area=area,
            time=time, 
            # price=total_price,
            price=1000,
        ).all()
        
        if len(paycheck) == 1:        
            if paycheck[0].pay_state == "4":
                for reservation in reservation_table:
                    file_name = f"qr_code/{email}_{area}_{date}_{reservation.time}.png"
                    reservation.buy = 1
                    reservation.qr_path = file_name
                    
                    db.session.commit()
                    
                    ## ADD QR Genertation Code ##
                    qr_img = make_qr_code(
                        area=reservation.area,
                        date=reservation.date,
                        time=reservation.time,
                        court=reservation.court,
                        email=reservation.email
                    )
                    qr_img.save("./app/static/" + file_name)
                    
                return redirect(url_for("main.confirm_pay", email=user.email))
        else:
            flash("결제가 완료되지 않았습니다.")
            return redirect("#")
    
    return render_template("user/request_pay_court.html")


@bp.route("/user_menu/check_reservation/<email>", methods=["GET"])
def check_reservation(email):
    
    date = datetime.date.today()
    
    user = User.query.filter_by(email=email).first()
    
    subquery = db.query(ReserveCourt).distict(ReserveCourt.time)
    
    reservation_table = ReserveCourt.query.filter_by(email=email, buy=1)\
        .filter(ReserveCourt.date >= date)\
        .query(subquery)\
        .order_by(ReserveCourt.date)\
        .order_by(ReserveCourt.time)\
        .all()
    
    return render_template("user/check_reservation.html", user=user, reservation_table=reservation_table, timetable=timetable)
    
    
@bp.route("/user_menu/get_qrcode/<email>/<date>/<time>", methods=["GET"])
def get_qrcode(email, date, time):
    user = User.query.filter_by(email=email).first()
    
    reservation_table = ReserveCourt.query.filter_by(email=email, date=date, time=time, buy=1).first()
    
    return render_template("user/get_qrcode.html", user=user, reservation_table=reservation_table)
    

@bp.route("/pay_check", methods=["POST"])
def pay_check():
    key_info = "3c0VLPJBsy0//kO2e3TEe+1DPJnCCRVaOgT+oqg6zaM="
    value_info = "3c0VLPJBsy0//kO2e3TEexga0slLAiui2bsP1P985Rc="
    print(request.form['var1'])
    print(datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d'))
    if (request.form["linkkey"] == key_info) and (request.form["linkval"] == value_info) and (request.form['pay_state'] == "4"):
        
        db_update = PayDB(
            goodname = request.form['goodname'],
            date = datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d'),
            area = request.form['memo'],
            time = request.form['var2'],
            price = request.form['price'],
            recvphone = request.form['recvphone'],
            pay_date = datetime.datetime.strptime(request.form['pay_date'], '%Y-%m-%d %H:%M:%S'),
            pay_type = request.form['pay_type'],
            pay_state = request.form['pay_state']
        )
            
        db.session.add(db_update)
        db.session.commit()
        print("SUCCESS")
        return "SUCCESS"
    else:
        return "FAIL"

@bp.route("/user/qrcode_check", methods=["POST"])
def qrcode_check():
    print(request.form)
    reservation_check = ReserveCourt.query.filter_by(
        area=request.form['area'],
        date=request.form['date'],
        time=request.form['time'],
        court=request.form['court'],
        email=request.form['email'],
        buy=1
    ).all()
    
    if len(reservation_check) == 1:
        return {'result': 1}
    else:
        return {'result': 0}

