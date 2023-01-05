import urllib
import ast
import requests
import datetime
import smtplib

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Blueprint, url_for, render_template, request, flash
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from sqlalchemy import desc
from time import sleep
from werkzeug.utils import redirect
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, BuyPoint, ReserveCourt, PayDB, DoorStatus, PointTable, CourtPriceTable, ReservationStatus
from app import db
from app.forms import BuyPointForm, ReserveCourtAreaDateForm, ReserveCourtCourtForm, ReserveCourtForm, ReserveCourtTimeForm, DoorOpenForm, ChangePasswordForm, SendVideoForm

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
                "memo": f"주식회사볼랩_포인트 0 0 0",
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


    ## Payapp 에 요할 결제 금액 계산
    if total_price >= (user.point + user.admin_point):
        total_pay = total_price - user.point - user.admin_point
    elif (user.point + user.admin_point) > total_price:
        total_pay = 0
        
    if (user.point + user.admin_point) >= total_price:
        if user.admin_point >= total_price:
            used_admin_point = total_price
            less_price = 0
        else:
            used_admin_point = user.admin_point
            less_price = total_price - used_admin_point
            
        used_point = less_price
    
    else:
        used_point = user.point
        used_admin_point = user.admin_point

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
                    "memo": f"{court_area} {used_point} {total_price} {used_admin_point}",
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

            return redirect(url_for("main.request_pay_court", phone=user.phone, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_price, total_pay=total_pay, used_point=used_point, used_admin_point=used_admin_point))
        
        ## 포인트로 전체 결제가 가능한 경우
        else:
            return redirect(url_for("main.request_pay_court", phone=user.phone, date=court_date, area=court_area, time=tmp_list, court=court_name, total_price=total_price, total_pay=total_pay, used_point=used_point, used_admin_point=used_admin_point))

    return render_template("user/reserve_court.html", form=form, user=user, court_area=court_area, court_name=court_name, court_date=court_date, total_reserve_time=total_reserve_time, total_price=total_price, total_pay=total_pay, tmp_list=tmp_list, timetable=timetable)


@bp.route(
    '/user_menu/<phone>/<date>/<area>/<time>/<court>/<total_pay>/<total_price>/<used_admin_point>/<used_point>/request_pay/court', 
    methods=('GET', 'POST')
)
def request_pay_court(
    phone:str, 
    date:str, 
    area:str, 
    time:str, 
    court:str, 
    total_pay:str, 
    total_price:str, 
    used_point:str, 
    used_admin_point:str
):
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
                used_point=used_point,
                used_admin_point=used_admin_point,
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
                used_point=used_point,
                used_admin_point=used_admin_point,
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

            ## 회원 보유 포인트에서 사용한 포인트를 제외하기 (포인트 결제)
            user.point = user.point - int(used_point)
            user.admin_point = user.admin_point - int(used_admin_point)

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
            requests.post("https://balllab-reserve.com/door_open", data=data_dict)
            flash("열렸습니다")
            redirect("#")
        ## 이용 가능한 시간이 아닌 경우 error를 출력
        else:
            error = "이용 가능한 시간이 아닙니다."
            flash(error)

    return render_template("user/check_reservation.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)


@bp.route("/pay_check", methods=["POST"])
def pay_check():
    """PayAPP에서 보내주는 결제 정보를 처리하는 Backend Code

    Returns:
        None
    """
    # payapp에 들어가면 아래 정보들을 확인 가능함
    ## 보내주는 정보를 확인할 key 값 설정
    key_info = [
        "lV7FSRjIxUq4b+2PiWlgge1DPJnCCRVaOgT+oqg6zaM=",  # 어린이대공원점
        "K8PbtiU4wqJXpMBfBwWSPO1DPJnCCRVaOgT+oqg6zaM=",  # 성수자양점
    ]
    ## 보내주는 정보를 확인할 value 값 설정
    value_info = [
        "lV7FSRjIxUq4b+2PiWlggUdrk/uKlhCLAkjn5E6oM7w=",  # 어린이대공원점
        "K8PbtiU4wqJXpMBfBwWSPDtOlrsKL7Aq6S3j3uVtLKc=",  # 성수자양점
    ]

    ## 결제 처리가 완료된 경우 아래 코드가 작동함 (Key값과 Value값도 동일한 경우 -> 보안처리)
    if (request.form["linkkey"] in key_info) and (request.form["linkval"] in value_info) and (request.form['pay_state'] == "4"):
        
        ## payapp에서 보내주는 정보를 기반으로 PayDB에 업데이트할 정보를 입력
        db_update = PayDB(
            mul_no=request.form['mul_no'],
            goodname=request.form['goodname'],
            date=datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d'),
            area=request.form['memo'].split()[0],
            time=request.form['var2'],
            price=request.form['price'],
            recvphone=request.form['recvphone'],
            pay_date=datetime.datetime.strptime(request.form['pay_date'], '%Y-%m-%d %H:%M:%S'),
            pay_type=request.form['pay_type'],
            pay_state=request.form['pay_state'],
            used_point=int(request.form['memo'].split()[1]),
            used_admin_point=int(request.form['memo'].split()[3]),
        )
        ## DB 정보 업로드, 수정사항 반영 및 업로드
        db.session.add(db_update)
        db.session.commit()

        user = User.query.filter_by(phone=request.form['recvphone']).first()

        ## Point 구입인 경우
        if request.form['memo'] == f"주식회사볼랩_포인트 0 0 0":
            
            ## payapp에서 보내준 데이터를 처리해서 변수에 할당
            point_price = int(request.form['price'])
            point_date = datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d')
            time = request.form['var2']

            ## 구입한 상품을 가격을 기준으로 Point Table DB에서 갖고 오기
            product = PointTable.query.filter_by(
                price=point_price
            ).first().point

            ## 복수 처리 방지를 위해 BuyPoint DB에서 포인트 할당이 이루어졌는지 조회
            is_record = BuyPoint.query.filter_by(
                phone=user.phone,
                time=time,
            ).first()

            ## 할당된 경우가 없는 경우
            if is_record is None:
                ## 회원에게 포인트 부여
                user.point += int(product)
                db.session.commit()

                ## BuyPoint DB에 포인트 구입 이력 추가
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
                ## DB 수정사항 반영 및 업로드
                db.session.add(record)
                db.session.commit()

        ## 코트 예약의 경우
        else:
            ## payapp에서 보내주는 정보를 바탕으로 DB에 업로드할 정보를 변수에 할당
            registration_date = datetime.datetime.strptime(request.form['var1'], '%Y-%m-%d')
            registration_area = request.form['memo'].split()[0]
            registration_court = request.form['goodname']
            registration_time = ast.literal_eval(request.form['var2'])
            registration_total_price = request.form['memo'].split()[2]
            registration_used_point = request.form['memo'].split()[1]
            registration_used_admin_point = request.form['memo'].split()[3]

            ## 예약 확정을 위해 ReserveCourt DB에서 예약 신청 정보 불러오기
            reservation_table = ReserveCourt.query.filter_by(
                phone=request.form['recvphone'],
                date=registration_date,
                area=registration_area,
                court=registration_court
            ).filter(ReserveCourt.time.in_(registration_time)).all()

            ## 예약 신청 정보에 구입 확정을 코딩하고 payapp 결제 처리 아이디를 부여 'mul_no' (환불 처리용) 
            for reservation in reservation_table:
                reservation.buy = 1
                reservation.mul_no = request.form['mul_no']
                ## DB에 변경 사항 및 수정사항 업로드
                db.session.commit()
            
            ## 코트를 현금 결제한 경우 결제 확정시 사용한 포인트 차감
            user.point = user.point - int(registration_used_point)
            user.admin_point = user.admin_point - int(registration_used_admin_point)

            db.session.commit()

        return "SUCCESS"

    ## 코트 예약 환불 처리 (pay_state가 9 또는 64 인 경우가 환불 요청)
    elif (request.form["linkkey"] in key_info) and (request.form["linkval"] in value_info) and (request.form['pay_state'] == "9" or request.form['pay_state'] == "64"):
        ## 환불 처리할 건을 PayDB에서 결제 id 'mul_no' 기준으로 불러오기
        pay_info = PayDB.query.filter_by(mul_no=request.form['mul_no']).first()
        ## PayDB에 해당 건을 환불 처리 상태로 변환
        pay_info.pay_state = request.form['pay_state']
        ## DB에 수정사항 반영 및 업로드
        db.session.commit()
        return "SUCCESS"

    else:
        return "FAIL"

## Door Open
@bp.route("/door_open", methods=["POST"])
def door_open():
    """도어락 오픈 Backend Code
    POST 요청이 오면 도어락 오픈 처리

    Returns:
        "도어락 오픈"
    """
    ## POST 요청에서 전송된 데이터에서 오픈해야할 도어락 id를 변수에 할당
    area = request.form['area']
    ## DoorStatus DB에 오픈할 도어락을 검색
    doorstatus = DoorStatus.query.filter_by(area=area).first()
    ## 도어락을 오픈 상태로 변경
    doorstatus.status = "1"
    ## DB에 수정사항 반영 및 업로드
    db.session.commit()

    return "Open Door"

## Door Close
@bp.route("/door_close", methods=["POST"])
def door_close():
    """도어락 잠금 Backend Code
    POST 요청이 오면 도어락 잠금 처리

    Returns:
        "도어락 잠금 메세지 출력"
    """
    ## POST 요청에서 전송된 데이터에서 오픈해야할 도어락 id를 변수에 할당
    area = request.form['area']
    ## DoorStatus DB에 잠금할 도어락을 검색
    doorstatus = DoorStatus.query.filter_by(area=area).first()
    ## 도어락을 잠금 상태로 변경
    doorstatus.status = "0"
    ## DB에 수정사항 반영 및 업로드
    db.session.commit()

    return "Close Door"


@bp.route("/get_door_status", methods=["POST"])
def get_door_status():
    """POST 요청이 오면 DoorStatus DB에서 도어락 상태를 반환 Backend Code

    Returns:
        도어락 상태 반환
    """
    ## POST 요청에서 전송된 데이터에서 상태를 확인해야하는 도어락 id를 변수에 할당
    area = request.form['area']
    ## DoorStatus DB에서 도어락 상태 조회
    doorstatus = DoorStatus.query.filter_by(area=area).first()

    return doorstatus.status


@bp.route("/refund_reservation/<phone>/<mul_no>", methods=["GET", "POST"])
def refund_reservation(phone:str, mul_no:str):
    """환불 처리 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호
        mul_no (str): 환불할 결제 ID

    Returns:
        처음: 환불 페이지 html 렌더링
        POST: 예약 확인 페이지로 이동
    """
    ## 환불 처리할 유저 정보 불러오기
    user = User.query.filter_by(phone=phone).first()
    ## 환불 처리할 건을 PayDB에서 조회
    pay_info = PayDB.query.filter_by(mul_no=mul_no).first()
    ## 코트 예약 정보 DB에서 결제id에 해당하는 예약 건 불러오기
    reservation_info = ReserveCourt.query.filter_by(
        mul_no=mul_no,
    ).order_by(ReserveCourt.time).all()

    ## POST 요청한 경우 아래 if 문이 실행
    if request.method == "POST":

        ## 환불 가능 시점 구하는 로직 - 시작
        ### 여러 예약 건수 중 첫번쨰 시간 것을 갖고오기
        reservation_first = reservation_info[0]
        ### 첫 시간 갖고오기 (12:30 ~ 13:00 -> 12:30) 
        time_tmp = timetable[int(reservation_first.time)]
        time_start = time_tmp.split()[0]
        ### datetime.datetime으로 변환 정의
        time_str = f"{reservation_first.date} {time_start}"
        ### datetime.datetime으로 type 변환
        date_time_start = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        
        ### 48시간 전에 환불 가능하므로 시점을 기준으로 48시간 전 시점을 계산
        refund_due_date = date_time_start - datetime.timedelta(days=2)

        cur_date = datetime.datetime.now()
        ## 환불 가능 시점 구하는 로직 - 끝

        ## 환불 요청 시점이 환불 가능한 시점 보다 이전인 경우
        if cur_date < refund_due_date:
            
            ## 포인트로만 결제한 경우
            if pay_info.pay_type == "point_only":
                ## 회원 포인트에 환불할 포인트 반영
                user.point = user.point + pay_info.used_point
                user.admin_point = user.admin_point + pay_info.used_admin_point
                ## PayDB에 환불 상태로 변경
                pay_info.pay_state = '64'
                ## DB에 수정사항 반영 및 업로드
                db.session.commit()

                ## 예약 DB에서 구입 상태 취소
                for reservation in reservation_info:
                    reservation.buy = 0
                    ## DB에 수정사항 반영 및 업로드
                    db.session.commit()
                    
            ## 현금이 포함된 결제인 경우
            else:
                ## 예약한 코트 지점에 따른 환불 요청 아이디 설정
                if pay_info.area == "어린이대공원점":
                    user_id = "newballlab"
                    key_info = "lV7FSRjIxUq4b+2PiWlgge1DPJnCCRVaOgT+oqg6zaM="

                elif pay_info.area == "성수자양점":
                    user_id = "balllabss"
                    key_info = "K8PbtiU4wqJXpMBfBwWSPO1DPJnCCRVaOgT+oqg6zaM="

                ## 환불 처리할 정보 정의
                post_data = {
                    'cmd': 'paycancel',
                    'userid': user_id,
                    'linkkey': key_info,
                    'mul_no': pay_info.mul_no,
                    'cancelmemo': "48시간 전 예약 취소",
                }

                ## 전송할 데이터를 utf-8로 인코딩
                data = urllib.parse.urlencode(post_data).encode('utf-8')
                
                ## 전송할 데이터 API 페이지 정의
                req = urllib.request.Request("http://api.payapp.kr/oapi/apiLoad.html")

                ## API에 인코딩한 데이터를 Post 전송
                with urllib.request.urlopen(req, data=data) as f:
                    resp = urllib.parse.unquote_to_bytes(f.read())
                    resp = resp.decode('utf-8')[6]
                    print("TEST", "State = ", resp, "Test")

                ## 일반적으로는 1초 내로 환불 처리됌
                sleep(1)

                ## 환불 처리중 사용한 포인트 만큼 회원 포이트 보유량에 반영
                user.point = user.point + pay_info.used_point
                user.admin_point = user.admin_point + pay_info.used_admin_point
                ## DB에 수정사항 반영 및 업로드
                db.session.commit()

                ## 예약 DB에서 구입 상태 취소
                for reservation in reservation_info:
                    reservation.buy = 0
                    ## DB에 수정사항 반영 및 업로드
                    db.session.commit()
            ## 예약 취소가 되었다고 메세지 출력
            flash("예약이 취소되었습니다. 포인트 반환 및 환불 처리가 완료되었습니다.")
            return redirect(url_for('main.check_reservation', phone=user.phone))
        
        ## 환불 요청 시점이 환불 가능한 시점을 지난 경우
        else:
            flash("이용 예정 시각과 현재 시각과의 차이가 48시간 이내이므로 예약 취소가 불가능합니다.")
            return redirect(url_for('main.check_reservation', phone=user.phone))

    return render_template("user/refund_reservation.html", user=user)


@bp.route("/change_password/<phone>", methods=["GET", "POST"])
def change_password(phone:str):
    """비밀번호 편경 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호

    Returns:
        처음: 비밀번호 변경 페이지 html 렌더링
        Post 호출 시: 비밀번호 변경완료시 로그인 페이지로 이동
    """
    ## 회원 정보를 User DB에서 불러오기
    user = User.query.filter_by(phone=phone).first()
    ## 비밀번호 변경 Form 불러오기
    form = ChangePasswordForm()

    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == "POST" and form.validate_on_submit():
        
        ## 새로 사용할 비밀번호와 기존 비밀번호가 같은 경우
        if check_password_hash(user.password, form.new_password1.data):
            flash("이전 비밀번호와 새 비밀번호가 일치합니다.")
            return redirect("#")
        
        ## 새로 사용할 비밀번호와 기존 비밀번호가 다른 경우
        if check_password_hash(user.password, form.before_password.data):
            ## user 정보에 새로운 비밀번호 저장
            user.password = generate_password_hash(form.new_password1.data)
            ## 비밀번호 변경일자 설정
            user.password_date = datetime.date.today()
            ## DB에 수정사항 반영 및 업로드
            db.session.commit()
            flash("비밀번호 변경이 완료되었습니다. 바뀐 비밀번호로 로그인해주세요.")
            return redirect(url_for("auth.login_form"))
        else:
            flash("이전 비밀번호가 일치하지 않습니다.")
            return redirect("#")

    return render_template("user/change_password.html", user=user, form=form)

@bp.route("/user_menu/check_video/<phone>", methods=["GET", "POST"])
def check_video(phone:str):
    """(회원, 영상 전송) 영상 전송 페이지 Backend Code

    Args:
        phone (str): 회원 핸드폰 번호

    Returns:
        처음: 코트 예약 결제 확인 페이지 html 렌더링
    """
    ## 도어락 제어를 위한 Form 불러오기
    form = SendVideoForm()
    
    ## 현재 시점의 14일 전 날짜 정보 불러오기 (datetime.date)
    date = datetime.date.today() - datetime.timedelta(days=14)

    user = User.query.filter_by(phone=phone).first()

    ## 회원의 코트 예약 확정된 정보 불러오기 (현재 일 포함 및 이후 일자) 
    reservation_table = ReserveCourt.query.filter_by(phone=phone, buy=1)\
        .filter(ReserveCourt.court.in_(['1번', '3층', '4층']))\
        .filter(ReserveCourt.date >= date)\
        .order_by(ReserveCourt.date)\
        .order_by(ReserveCourt.time)\
        .all()
        
    ## Post 요청할 데이터 정리
    if request.method == "POST":
        
        ## 요청 시점에 영상 데이터가 있는지 Google Drive에서 검색하고 불러오기
        links = find_generate_video_link(
            court=request.form['area'],
            date=request.form['date'],
            time=request.form['time'],
        )
        
        ## 회원이 선택 약관에 동의한 경우 처리
        if user.agreement_option == 1:
            ## 영상이 없는 경우
            if len(links) == 0:
                flash("영상 촬영을 하지 않았습니다.")
                return render_template("user/check_video.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)
            ## 영상이 있는 경우
            else:
                ## 회원이 등록한 email로 영상 다운로드 링크 보내기
                send_mail(
                    file_list=links,
                    to_email=user.email
                )
                flash("영상을 전송했습니다.")
                return render_template("user/check_video.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)
        else:
            flash("선택 약관을 동의하지 않아 서비스를 이용할 수 없습니다.")
            return render_template("user/check_video.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)

    return render_template("user/check_video.html", user=user, reservation_table=reservation_table, timetable=timetable, form=form)

def find_generate_video_link(court:str, date:str, time:str) -> list:
    """(회원, 영상 전송) 영상 공유 링크 생성

    Args:
        court (str): 코트명
        date (str): 이용 일자
        time (str): 이용 시간

    Returns:
        file_links: 공유 링크가 담긴 list
    """
    ## Google Auth 인증 객체 불러오기
    gauth = GoogleAuth()
    
    # 인증서가 있는 경우 불러오기
    gauth.LoadCredentialsFile("mycreds.txt")
    
    if gauth.credentials is None:
        ## 토큰이 없는 경우 새로 인증하기
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        ## 토큰의 이용 기간이 지나면 Refresh하기
        gauth.Refresh()
    else:
        ## 저장된 토큰이 있으면 인증하기
        gauth.Authorize()
        
    # 인증서를 저장하기
    gauth.SaveCredentialsFile("mycreds.txt")
    
    drive = GoogleDrive(gauth)

    if court == "1번":
        ## 어린이대공원점
        file_id = '1-2cQcKlR-rk7PM79QTUk3ry9_s6iNBW9'
        
    elif court == "3층":
        ## 성수 3층
        file_id = "1-3aN_0KVFKSRZ2wzmNI5rBmsZ00IcTIm"
        
    elif court == "4층":
        ## 성수 4층
        file_id = "1-1zgtrMcN8hXvjOcGoZF-k0oaT1Ti0mj"
    
    file_list = drive.ListFile(
        {
            "q": f"'{file_id}' in parents and trashed=False",
        }
    ).GetList()
    
    ## 요청 일시 처리
    game_date = date
    game_time = timetable[int(time)]
    start_time = game_time.split()[0].replace(":", "-")
    end_time = game_time.split()[-1].replace(":", "-")
    
    ## 검색을 위한 이용 시작 시점과 종료 시점을 str type으로 처리
    start_game = f"{game_date} {start_time}-00"
    end_game = f"{game_date} {end_time}-00"
    
    ## 전체 영상 정보에서 해당 조건에 맞는지 검색하기
    file_list = [x for x in file_list if (x['title'].split('.')[0] >= start_game) and (x['title'].split('.')[0] <= end_game)]

    ## 빈 파일 링크 리스트 생성
    file_links = []

    ## 파일 리스트에 있는 정보를 데이터 전송을 위한 링크 생성
    for file in file_list:
        
        ## 공유가 가능하도록 파일의 접근 권한을 변경
        permission = file.InsertPermission(
            {
                'type': 'anyone',
                'value': 'anyone',
                'role': 'reader'
            }
        )
        ## 파일 전송용 링크 생성
        link = file['id']
        link = f'https://drive.google.com/file/d/{link}/view?usp=share_link'
        file_links.append(link)
    
    return file_links

def send_mail(file_list:list, to_email:str) -> None:
    """(회원, 영상 전송) 메일 전송 코드

    Args:
        filelist (list): 코트명
        to_email (str): 회원 email

    Returns:
        None
    """
    
    ## 구글 IMOP 서버 주소
    gmail_smtp = 'smtp.gmail.com'

    ## 서버 링크 설정
    smpt = smtplib.SMTP_SSL(
        host=gmail_smtp, 
    )

    ## 메일 서버에 로그인할 아이디 페스워드 설정
    email_id = "admin@balllab.co.kr"
    email_password = "aujdkzlychlbnnen"

    ## 로그인 요청하기
    smpt.login(
        user=email_id,
        password=email_password
    )

    ## 메일 전송을 위한 객체 선언
    msg = MIMEMultipart()

    ## Mail 전송을 위한 기본 정보 입력
    msg['Subject'] = f"요청하신 영상 데이터 전달드립니다."
    msg['From'] = email_id
    msg['To'] = to_email
    
    ## 메일 내용 작성
    content = f"안녕하세요.\n요청하신 영상 파일 {len(file_list)}개 공유드립니다.\n"

    ## 메일에 파일 링크 삽입
    for file in file_list:
        content += f"{file}\n"
    content += "감사합니다.\n주식회사 볼랩 드림"
    
    ## 메일 내용을 Mail 객체에 삽입
    content_part = MIMEText(content, "plain")
    msg.attach(content_part)

    ## 메일 전송하기
    smpt.sendmail(email_id, to_email, msg.as_string())
    
    ## 메일 서버 닫기
    smpt.quit()
    
    return None