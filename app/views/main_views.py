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

## 코트 이름 센터 별 문 아이디 매핑
door_map_dict = {
    "1번": "center_1",
    "2번": "center_1",
    "3번": "center_1",
    '3층': 'center_2_3f',
    '4층': 'center_2_4f',
}


@bp.route('/')
def login_page():
    """ IP address/ 가 호출되면 IP adress/auth/login/ 으로 Redirect

    Returns:
        처음: 로그인 페이지로 리다이렉스
    """
    return redirect(url_for("auth.login_form"))


@bp.route('/user_menu/<phone>')
def user_menu(phone:str):
    """유저 메뉴 페이지 Backend Code

    Args:
        phone (str): 핸드폰 번호

    Returns:
        처음: 유저 메뉴 페이지 html 렌더링
    """
    user = User.query.filter_by(phone=phone).first()
    return render_template("user/user_menu.html", user=user)


@bp.route('/user_menu/<phone>/buy_point/', methods=('GET', 'POST'))
def buy_point(phone:str):
    """포인트 결제 페이지 Backend Code

    Args:
        phone (str): 핸드폰 번호

    Returns:
        처음: 포인트 선택 창 html 렌더링
        POST: 결제 확인 페이지로 이동
    """
    ## Point 구입 페이지 Form 불러오기
    form = BuyPointForm()
    user = User.query.filter_by(phone=phone).first()
    date = datetime.date.today()

    ## PointTable DB에서 Point 가격 정보 불러오기
    point_tables = PointTable.query.order_by(PointTable.price).all()

    ## BuyPoint DB에서 회원이 구입한 포인트 이력 불러오기
    buy_point_list = BuyPoint.query.filter_by(
        phone=user.phone,
    ).all()

    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == "POST" and form.validate_on_submit():
        
        ## Form에 입력된 Price 정보 불러오기
        price = form.price.data
        ## Price에 해당하는 Point 정보 불러오기
        product = PointTable.query.filter_by(price=price).first().point

        ## Point 구입 이력이 없는 경우 time을 1로 설정
        if len(buy_point_list) == 0:
            time = 1
            
        ## 구입 이력이 있는경우 길이 + 1
        else:
            time = len(buy_point_list) + 1

        time = f"point_{time}"

        ## payapp에 결제 요청할 정보를 dictionary로 정리
        post_data = (
            {
                'cmd': 'payrequest',
                'userid': 'newballlab',
                'goodname': f"{product} LUV",
                'price': price,
                'recvphone': user.phone,
                "skip_cstpage": "y",
                "memo": f"주식회사볼랩_포인트 0",
                "var1": date,
                "var2": time,
            }
        )

        ## 전송할 데이터를 utf-8로 인코딩
        data = urllib.parse.urlencode(post_data).encode('utf-8')
        
        ## 전송할 데이터 API 페이지 정의
        req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")

        ## API에 인코딩한 데이터를 Post 전송
        with urllib.request.urlopen(req, data=data) as f:
            resp = urllib.parse.unquote_to_bytes(f.read())
            resp = resp.decode('utf-8')[6]
            print("TEST", "State = ", resp, "Test")
            
        ## 통신이 정상적으로 됬을 경우 결제 확인 페이지로 이동
        if resp == "1":
            return redirect(url_for("main.request_pay_point", phone=user.phone, product=product, time=time))
        ## 통신이 정상적으로 됬을 경우 결제 확인 페이지로 이동
        else:
            redirect("#")

    return render_template("user/buy_point.html", user=user, form=form, point_tables=point_tables)


@bp.route('/user_menu/<phone>/<product>/<time>/request_pay/point', methods=('GET', 'POST'))
def request_pay_point(phone:str, product:str, time:str):
    """포인트 결제가 완료되었는지 확인하는 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호
        product (str): 구입한 제품
        time (str): 구입 시점

    Returns:
        처음: 결제 확인 페이지 html 렌더링
        POST: 결제 확인후 안내 페이지로 이동
    """
    ## POST 요청한 경우 아래 if 문이 실행
    if request.method == 'POST':
        user = User.query.filter_by(phone=phone).first()
        
        ## PayDB에 결제 상태 정보 불러오기
        paycheck = PayDB.query.filter_by(
            recvphone=user.phone,
            goodname=f"{product} LUV",
            time=time,
        ).order_by(PayDB.pay_date.desc()).all()

        ## 결제 정보가 있는 경우
        if len(paycheck) == 1:
            if paycheck[0].pay_state == "4":
                return redirect(url_for("main.confirm_pay", phone=user.phone))
            
        ## 결제 정보가 없는 경우
        else:
            flash("결제가 완료되지 않았습니다.")
            return redirect("#")

    return render_template("user/request_pay_point.html")


@bp.route("/user_menu/<phone>/confirm_pay", methods=('GET', 'POST'))
def confirm_pay(phone:str):
    """결제 확인 후 안내 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호

    Returns:
        처음: 결제 확인후 안내 페이지 html 렌더링
    """
    user = User.query.filter_by(phone=phone).first()

    return render_template("user/confirm_pay.html", user=user)


## Reserve Court
@bp.route("/user_menu/<phone>/reserve_court/select_area_date", methods=('GET', 'POST'))
def reserve_court_area_date(phone:str):
    """지점 및 이용 날짜 선택 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호

    Returns:
        처음: 지점 및 이용 날짜 선택 페이지 html 렌더링
        Post 호출 시: 코트 선택 페이지로 이동
    """
    ##  코트 및 이용 날짜 선택 Form 불러오기
    form = ReserveCourtAreaDateForm()
    user = User.query.filter_by(phone=phone).first()
    
    ## 현재 날짜 datetime.date 형식으로 정의 (최소)
    today_tmp = datetime.date.today()
    cur_date = today_tmp.strftime("%Y-%m-%d")
    
    ## 회원 예약 가능한 날짜 datetime.date 형식으로 정의 (최대)
    max_date = (today_tmp + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        area = form.area.data
        date = form.date.data
        return redirect(url_for("main.reserve_court_court", phone=user.phone, area=area, date=date))

    return render_template("user/reserve_court_area_date.html", form=form, cur_date=cur_date, max_date=max_date)


@bp.route("/user_menu/<phone>/<area>/<date>/reserve_court/select_court", methods=('GET', 'POST'))
def reserve_court_court(phone:str, area:str, date:str):
    """코트 설정 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호
        area (str): 선택한 지점
        date (str): 선택한 날짜

    Returns:
        처음: 코트 선택 페이지 html 렌더링
        Post 호출 시: 이용 시간 선택 페이지로 이동
    """
    ## 코트 선택 Form 불러오기
    form = ReserveCourtCourtForm()

    user = User.query.filter_by(phone=phone).first()

    ## 코트 오픈 정보를 DB에서 불러오기
    court_status_table = ReservationStatus.query.filter_by(
        area=area, 
        status="1",
    ).order_by(ReservationStatus.id).all()

    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        court_area = area
        court_date = date
        court_name = form.court.data
        return redirect(url_for("main.reserve_court_time", phone=user.phone, court_area=court_area, court_date=court_date, court_name=court_name))

    return render_template("user/reserve_court_court.html", form=form, court_status_table=court_status_table)


@bp.route("/user_menu/<phone>/<court_area>/<court_date>/<court_name>/select_time", methods=('GET', 'POST'))
def reserve_court_time(phone:str, court_area:str, court_date:str, court_name:str):
    """코트 이용 시간 선택 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호
        court_area (str): 선택한 지점
        court_date (str): 선택한 이용 날짜
        court_name (str): 선택한 코트 명

    Returns:
        처음: 이용 약관 페이지 html 렌더링
        Post 호출 시: 회원 정보 입력 페이지로 이동
    """
    form = ReserveCourtTimeForm()

    ## 코트 예약 정보를 DB에서 불러오기
    court_info = ReserveCourt.query.filter_by(
        area=court_area, 
        date=court_date, 
        court=court_name, 
        buy=1
    ).all()
    
    user = User.query.filter_by(phone=phone).first()

    ## 예약 완료된 시간을 int로 Code화
    court_info = [int(x.time) for x in court_info]

    ## 현재 날짜를 datetime.date로 변환
    is_today = datetime.datetime.today()
    ## 코트 예약 날짜를 datetime.date로 변환
    court_day = datetime.datetime.strptime(court_date, '%Y-%m-%d').date()

    ## 현재 시간 기준으로 과거 시점의 예약을 못하도록 막는 로직
    ## 예약 일자와 현재 일자가 같은 경우에 실행함
    if court_day == is_today.date():
        if is_today.hour >= 10:
            hour = f"{is_today.hour}:00"
        else:
            hour = f"0{is_today.hour}:00"
        ## block 해야하는 시점의 데이터를 timetable과 비교하여 Index 값을 찾기
        block_begin = max(
            [n for n, x in enumerate(timetable) if hour in x]
        ) + 1
        ## Block 해야하는 Index 정의
        block_table = [n for n in range(block_begin)]
        ## 예약 완료된 timetable index와 Block 해야하는 index를 합치기 
        court_info = court_info + block_table
        
    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        reserve_times = request.form.getlist("time")
        return redirect(url_for("main.reserve_court", phone=user.phone, court_area=court_area, court_date=court_date, court_name=court_name, reserve_times=reserve_times))

    return render_template("user/reserve_court_time.html", form=form, court_info=court_info, timetable=timetable)


@bp.route("/user_menu/<phone>/<court_area>/<court_date>/<court_name>/<reserve_times>/reserve_court", methods=('GET', 'POST'))
def reserve_court(phone:str, court_area:str, court_date:str, court_name:str, reserve_times:str):
    """코트 결제 요청 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호
        court_area (str): 선택한 지점
        court_date (str): 선택한 이용 날짜
        court_name (str): 선택한 코트 명
        reserve_times (str): 선택한 코트 이용시간

    Returns:
        처음: 코트 예약 결제 페이지 html 렌더링
        Post 호출 시: 결제 확인 페이지로 이동
    """
    form = ReserveCourtForm()

    user = User.query.filter_by(phone=phone).first()

    ## "[1, 2, 3]" -> [1, 2, 3] str을 list로 변환
    reserve_times = ast.literal_eval(reserve_times)

    ## 시간 복수 선택한 경우
    if type(reserve_times) != int:
        tmp_list = []
        for reserv_time in reserve_times:
            tmp_list.append(int(reserv_time))
    ## 단일 시간 선택한 경우
    else:
        tmp_list = [reserve_times]

    ## 시간 복수 선택한 경우 이용시간 계산
    if len(tmp_list) > 1:
        total_reserve_time = len(tmp_list) / 2  # 시간
    ## 시간 단일 선택한 경우 이용시간 계산
    else:
        total_reserve_time = 0.5

    ## 선택한 코트의 이용 비용 불러오기
    court_price = CourtPriceTable.query.filter_by(
        area=court_area
    ).first().price

    ## 최종 비용 계산하기
    total_price = int(total_reserve_time * 2 * court_price)

    ## 최종 비용이 보유한 포인트보다 큰 경우
    if total_price >= user.point:
        total_pay = total_price - user.point
        used_point = user.point
    ## 포인트가 최종 비용 보다 큰 경우
    elif user.point > total_price:
        total_pay = 0
        used_point = user.point - total_price

    ## POST 요청인 경우 아래 if 문이 실행
    if request.method == 'POST':
        ## 시간별로 ReserveCourt DB에 예약 정보를 넣음
        for tmp_time in tmp_list:
            ## 선택한 시간에 중복된 케이스가 있는지를 확인
            reserve_check = ReserveCourt.query.filter_by(
                date=datetime.datetime.strptime(court_date, "%Y-%m-%d"),
                area=court_area,
                court=court_name,
                time=str(tmp_time),
                buy=1,
            ).first()
            ## 중복되지 않은 경우 ReserveCourt DB에 예약 정보를 입력
            if reserve_check == None:
                ## Reserve Court ##
                court_reserve = ReserveCourt(
                    date=datetime.datetime.strptime(court_date, "%Y-%m-%d"),
                    area=court_area,
                    time=str(tmp_time),
                    court=court_name,
                    phone=user.phone,
                    email=user.email,
                    username=user.username,
                    buy=0,
                )
                ## DB 수정사항 반영 및 업로드
                db.session.add(court_reserve)
                db.session.commit()
            else:
                continue
        
        ## 선택한 시간을 str 타입으로 변환
        tmp_list = [str(x) for x in tmp_list]

        ## 보유한 포인트 사용 후, 차액 결제가 필요한 경우
        if total_pay != 0:

            ## 지점별 payapp 아이디 설정
            if court_area == "어린이대공원점":
                user_id = "newballlab"
                
            elif court_area == "성수자양점":
                user_id = "balllabss"

            ## Post 요청할 데이터 정리
            ### memo, var1, var2는 결제 요청 후, 결제 확인후 DB 기록시 구분자로 활용함
            post_data = (
                {
                    'cmd': 'payrequest',
                    'userid': user_id,
                    'goodname': court_name,
                    'price': total_pay,
                    'recvphone': user.phone,
                    "skip_cstpage": "y",
                    "memo": f"{court_area} {used_point} {total_price}",
                    "var1": court_date,
                    "var2": str(tmp_list), ## Text로만 가능하기 떄문에 list를 str으로 바꿔서 전달
                }
            )

            ## 전송할 데이터를 utf-8로 인코딩
            data = urllib.parse.urlencode(post_data).encode('utf-8')
            
            ## 전송할 데이터 API 페이지 정의
            req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")
            
            ## API에 인코딩한 데이터를 Post 전송
            with urllib.request.urlopen(req, data=data) as f:
                resp = urllib.parse.unquote_to_bytes(f.read())
                resp = resp.decode('utf-8')[6]
                print("TEST", "State = ", resp, "Test")

            return redirect(url_for("main.request_pay_court", phone=user.phone, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_price, total_pay=total_pay))
        
        ## 포인트로 전체 결제가 가능한 경우
        else:
            return redirect(url_for("main.request_pay_court", phone=user.phone, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_price, total_pay=total_pay))

    return render_template("user/reserve_court.html", form=form, user=user, court_area=court_area, court_name=court_name, court_date=court_date, total_reserve_time=total_reserve_time, total_price=total_price, total_pay=total_pay, tmp_list=tmp_list, timetable=timetable)


@bp.route('/user_menu/<phone>/<date>/<area>/<time>/<court>/<total_pay>/<total_price>/request_pay/court', methods=('GET', 'POST'))
def request_pay_court(phone:str, date:str, area:str, time:str, court:str, total_pay:str, total_price:str):
    """코트 결제가 완료되었는지 확인하는 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호
        date (str): 선택한 이용 날짜
        area (str): 선택한 지점
        time (str): 선택한 코트 이용시간
        court (str): 선택한 코트 명
        total_pay (str): 결제 요청 금액 (total_price - total_pay = used point)
        total_price (str): 결제할 금액

    Returns:
        처음: 코트 예약 결제 확인 페이지 html 렌더링
        Post 호출 시: 결제 확인후 안내 페이지 이동
    """
    ## "[1, 2, 3]" -> [1, 2, 3] str을 list로 변환
    tmp_time = ast.literal_eval(time)
    
    ## 단일 시간 예약한 경우 list 형식으로 변환
    if type(tmp_time) == int:
        tmp_time = [tmp_time]
        
    user = User.query.filter_by(phone=phone).first()
    
    ## 예약 확정 전 데이터를 DB에서 불러오기
    reservation_table = ReserveCourt.query.filter_by(
        date=date, 
        phone=phone, 
        area=area, 
        court=court
    ).filter(ReserveCourt.time.in_(tmp_time))\
    .all()

    ## POST 요청인 경우 아래 if 문이 실행
    if (request.method == 'POST'):

        ## payapp에 결제를 요청한 경우
        if total_pay != "0":
            ## PayDB에서 결제 완료 정보를 불러오기
            paycheck = PayDB.query.filter_by(
                recvphone=user.phone,
                goodname=court,
                date=date,
                area=area,
                time=time,
                price=total_pay,
                used_point=str(int(total_price) - int(total_pay)),
            ).order_by(PayDB.mul_no.desc()).first()

            ## 결제가 완료된 경우
            if paycheck != None:
                return redirect(url_for("main.confirm_pay", phone=user.phone))
            ## 결제가 완료되지 않은 경우
            else:
                flash("결제가 완료되지 않았습니다.")
                return redirect("#")
            
        ## 전액 포인트 결제인 경우
        else:
            ## PayDB에서 전체 데이터 불러오기
            pay_db = PayDB.query.all()

            ## PayDB에 Point 결제 정보 업로드 (payapp을 사용한 결제인 경우 자동으로 데이터를 쌓음)
            pay_add = PayDB(
                mul_no=f"point_{len(pay_db)}",
                goodname=court,
                date=datetime.datetime.strptime(date, "%Y-%m-%d"),
                area=area,
                time=time,
                price=total_pay,
                used_point=total_price,
                recvphone=user.phone,
                pay_date=datetime.datetime.now(),
                pay_type="point_only",
                pay_state="4",
            )

            ## DB에 포인트 결제정보 업로드 및 수정사항 반영
            db.session.add(pay_add)
            db.session.commit()

            ## 예약 정보 테이블에서 예약 확정으로 변환
            for reservation in reservation_table:
                reservation.buy = 1
                ## 결제 id 할당 (환불용)
                reservation.mul_no = f"point_{len(pay_db)}" 

                db.session.commit()

            ## 회원 보유 포인트에서 사용한 포인트를 제외하기
            if user.point >= int(total_price):
                user.point = user.point - int(total_price)
            ## 보유 포인트 보다 결제할 금액이 큰 경우 0으로 변환
            else:
                user.point = 0

            ## DB에 수정사항 반영 및 업로드
            db.session.commit()

            return redirect(url_for("main.confirm_pay", phone=user.phone))

    return render_template("user/request_pay_court.html", total_pay=total_pay)


@bp.route("/user_menu/check_reservation/<phone>", methods=["GET", "POST"])
def check_reservation(phone:str):
    """(회원, 코트입장) 도어락 원격 제어페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호

    Returns:
        처음: 코트 예약 결제 확인 페이지 html 렌더링
    """
    ## 도어락 제어를 위한 Form 불러오기
    form = DoorOpenForm()
    
    ## 현재 시점의 날짜 정보 불러오기 (datetime.date)
    date = datetime.date.today()

    user = User.query.filter_by(phone=phone).first()

    ## 회원의 코트 예약 확정된 정보 불러오기 (현재 일 포함 및 이후 일자) 
    reservation_table = ReserveCourt.query.filter_by(phone=phone, buy=1)\
        .filter(ReserveCourt.date >= date)\
        .order_by(ReserveCourt.date)\
        .order_by(ReserveCourt.time)\
        .all()
        
    ## Post 요청할 데이터 정리
    if request.method == "POST":
        ## 예약한 코트 이용 시간 불러오기 12:00 ~ 12:30인 경우
        time_tmp = timetable[int(request.form['time'])]
        ### 12:00
        time_start = time_tmp.split()[0]
        ### 12:30
        time_end = time_tmp.split()[-1]

        ## "20201129 12:00" -> Datatime 형식으로 변환
        time_str = f"{request.form['date']} {time_start}"
        date_time_start = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        ## 5분전 부터 입장 가능인 경우 20201129 11:55:00 으로 변환
        date_time_start = date_time_start - datetime.timedelta(minutes=5)

        ## "20201129 12:00" -> Datatime 형식으로 변환
        time_str = f"{request.form['date']} {time_end}"
        date_time_end = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        ## 종료 후 5분까지 입장 가능인 경우 20201129 12:35:00 으로 변환
        date_time_end = date_time_end + datetime.timedelta(minutes=5)

        ## 입장 시점의 날짜 및 시간 불러오기
        cur_date = datetime.datetime.today()

        ## 입장 시점이 입장 가능한 시간에 포함되는 경우 도어락 오픈 요청을 보냄
        if (cur_date >= date_time_start) and (cur_date <= date_time_end):
            data_dict = {
                'area': door_map_dict[request.form['area']],
            }
            requests.post("http://43.200.247.167/door_open", data=data_dict)
            flash("열렸습니다")
            redirect("#")
        ## 이용 가능한 시간이 아닌 경우 error를 출력
        else:
            error = "이용 가능한 시간이 아닙니다."
            flash(error)

    return render_template("user/check_reservation.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)


@bp.route("/pay_check", methods=["POST"])
def pay_check():
    key_info = [
        "lV7FSRjIxUq4b+2PiWlgge1DPJnCCRVaOgT+oqg6zaM=",  # 어린이대공원점
        "K8PbtiU4wqJXpMBfBwWSPO1DPJnCCRVaOgT+oqg6zaM=",  # 성수자양점
    ]
    value_info = [
        "lV7FSRjIxUq4b+2PiWlggUdrk/uKlhCLAkjn5E6oM7w=",  # 어린이대공원점
        "K8PbtiU4wqJXpMBfBwWSPDtOlrsKL7Aq6S3j3uVtLKc=",  # 성수자양점
    ]

    if (request.form["linkkey"] in key_info) and (request.form["linkval"] in value_info) and (request.form['pay_state'] == "4"):

        db_update = PayDB(
            mul_no=request.form['mul_no'],
            goodname=request.form['goodname'],
            date=datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d'),
            area=request.form['memo'].split()[0],
            time=request.form['var2'],
            price=request.form['price'],
            recvphone=request.form['recvphone'],
            pay_date=datetime.datetime.strptime(
                request.form['pay_date'], '%Y-%m-%d %H:%M:%S'),
            pay_type=request.form['pay_type'],
            pay_state=request.form['pay_state'],
            used_point=int(request.form['memo'].split()[1]),
        )

        db.session.add(db_update)
        db.session.commit()

        user = User.query.filter_by(phone=request.form['recvphone']).first()

        ## Point
        if request.form['memo'] == f"주식회사볼랩_포인트 0":

            point_price = int(request.form['price'])
            point_date = datetime.datetime.strptime(
                request.form['var1'], '%Y-%m-%d')
            time = request.form['var2']

            product = PointTable.query.filter_by(
                price=point_price).first().point

            is_record = BuyPoint.query.filter_by(
                phone=user.phone,
                time=time,
            ).first()

            if is_record is None:
                ## Assgin Point First
                user.point += int(product)
                db.session.commit()

                ## Add Logs
                record = BuyPoint(
                    phone=user.phone,
                    email=user.email,
                    username=user.username,
                    price=point_price,
                    product=f"{product} LUV",
                    area="주식회사볼랩",
                    date=point_date,
                    buy=1,
                    time=time,
                )

                db.session.add(record)
                db.session.commit()

        ## Regrestration Court
        else:
            registration_date = datetime.datetime.strptime(
                request.form['var1'], '%Y-%m-%d')
            registration_area = request.form['memo'].split()[0]
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
def refund_reservation(phone:str, mul_no:str):

    user = User.query.filter_by(phone=phone).first()
    pay_info = PayDB.query.filter_by(mul_no=mul_no).first()
    reservation_info = ReserveCourt.query.filter_by(
        mul_no=mul_no).order_by(ReserveCourt.time).all()

    if request.method == "POST":

        reservation_first = reservation_info[0]

        time_tmp = timetable[int(reservation_first.time)]
        time_start = time_tmp.split()[0]

        time_str = f"{reservation_first.date} {time_start}"
        date_time_start = datetime.datetime.strptime(
            time_str, "%Y-%m-%d %H:%M")
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
                    'mul_no': pay_info.mul_no,
                    'cancelmemo': "48시간 전 예약 취소",
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
