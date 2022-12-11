import datetime

from flask import Blueprint, url_for, render_template, flash, request, session, g, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect

from app.forms import UserLoginForm, UserCreateForm, AgreementForm, FindPassword
from app.models import User
from app import db

## Blueprint (ip adress/auth/) 설정
bp = Blueprint("auth", __name__, url_prefix='/auth')

## (ip adress/auth/login/)
@bp.route('/login/', methods=['GET', 'POST'])
def login_form():
    """로그인 페이지 Backend code

    Returns:
        처음: Login page html 렌더링
        Post 호출 시: Main menu 페이지로 이동
    """
    ## Login Form 불러오기
    form = UserLoginForm()

    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        ## 핸드폰 번호를 기준으로 회원 정보 불러오기
        user = User.query.filter_by(phone=form.phone.data).first()
        
        ## 회원 정보가 없는 경우
        if not user:
            error = "존재하지 않는 사용자입니다."
        ## 패스워드가 0000 인 경우
        elif (form.password.data == "0000") and (user.password == "0000"):
            # 회원정보 수정 페이지로 이동
            return redirect(url_for("auth.signup_0000", phone=user.phone))
        ## 비밀번호가 틀린 경우
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 올바르지 않습니다."

        if error is None:
            session.clear()
            session['user_id'] = user.id
            _next = request.args.get('next', '')
            if _next:
                return redirect(_next)
            else:
                return redirect(url_for('main.user_menu', phone=user.phone))
        ## Error 출력
        flash(error)

    return render_template("auth/login.html", form=form)


@bp.route('/agreement/', methods=['GET', 'POST'])
def signup_agreement():
    """이용 약관 페이지 Backend Code

    Returns:
        처음: 이용 약관 페이지 html 렌더링
        Post 호출 시: 회원 정보 입력 페이지로 이동
    """
    ## Agreement Form 불러오기
    form = AgreementForm()

    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        ## 필수 약관 체크한 경우
        if form.agree_1.data == "1" and form.agree_2.data == "1":
            ## 선택 사항 체크안한 경우
            if form.agree_3.data is None:
                agree_3 = 0
            else:
                agree_3 = 1
            return redirect(url_for("auth.signup", agree_3=agree_3))
        else:
            ## 필수 사항 체크 안한경우 팝업
            flash("동의를 하지 않으면 현재는 가입이 불가능합니다.")
            return redirect(url_for("auth.login_form"))

    return render_template("auth/signup_agreement.html", form=form)


@bp.route('/signup/<agree_3>', methods=('GET', 'POST'))
def signup(agree_3:str):
    """회원 가입 정보 입력 페이지 Backend Code

    Args:
        agree_3 (str): 약관 체크 여부

    Returns:
        처음: 회원 가입 정보 입력 페이지 html 렌더링
        Post 호출 시: 회원 가입 정보 체크 페이지로 이동
    """
    ## 회원가입 Form 불러오기
    form = UserCreateForm()
    
    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        ## 회원정보 불러오기
        user = User.query.filter_by(phone=form.phone.data).first()
        if not user:
            ## 유저 정보가 없는 경우 DB에 입력된 데이터를 업로드
            user = User(
                phone=form.phone.data,
                email=form.email.data,
                username=form.username.data,
                birth=form.birth.data,
                password=generate_password_hash(form.password1.data),
                password_date=datetime.date.today(),
                register_date=datetime.date.today(),
                agreement_option=int(agree_3)
            )
            ## DB에 새로운 행 추가하기
            db.session.add(user)
            ## DB 수정사항 반영 및 업로드
            db.session.commit()
            return redirect(url_for('auth.signup_check', phone=user.phone))
        else:
            flash('이미 존재하는 사용자입니다.')

    return render_template('auth/signup.html', form=form)


@bp.route('/signup/check/<phone>', methods=('GET', 'POST'))
def signup_check(phone:str):
    """회원 정보 체크 페이지 Backend Code

    Args:
        phone (str): 핸드폰 번호

    Returns:
        처음: Login page html 렌더링
        Post 호출 시: Main menu page로 이동
    """
    ## 새로 DB에 업로드한 데이터가 잘 업로드 되었는지 확인하기 위해 유저 정보 불러오기
    user = User.query.filter_by(phone=phone).first()
    return render_template('auth/signup_check.html', user=user)


@bp.route('/admin_login/', methods=['GET', 'POST'])
def admin_login_form():
    """관리자 로그인 페이지 Backend code

    Returns:
        처음: 관리자 로그인 페이지 html 렌더링
        Post 호출 시: 관리자 menu 페이지로 이동
    """
    ## 관리자페이지 Login Form 불러오기
    form = UserLoginForm()
    
    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        ## 회원 정보 불러오기
        user = User.query.filter_by(phone=form.phone.data).first()
        ## Error
        if not user:
            error = "존재하지 않는 사용자입니다."
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 올바르지 않습니다."
        ## 관리자 권한이 있는지를 확인
        elif user.user_type != 1:
            error = "관리자 권한이 없습니다."
        if error is None:
            session.clear()
            session['user_id'] = user.id
            _next = request.args.get('next', '')
            if _next:
                return redirect(_next)
            else:
                return redirect(url_for('admin.admin_menu', phone=user.phone))

        flash(error)

    return render_template("auth/login_admin.html", form=form)


@bp.route('/signup_0000/<phone>', methods=["GET", "POST"])
def signup_0000(phone:str):
    """회원정보 수정 페이지 Backend Code

    Args:
        phone (str): 핸드폰 번호

    Returns:
        처음: 회원정보 수정 페이지 html 렌더링
        Post 호출 시: 회원 로그인 페이지로 이동
    """
    ## 회원가입 Form 불러오기
    form = UserCreateForm()
    
    ## 회원가입 정보 불러오기
    user = User.query.filter_by(phone=phone).first()
    
    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == "POST" and form.validate_on_submit():
        ## 새로 입력한 정보를 기존의 회원 정보에 입력하기
        user.email = form.email.data
        user.password = generate_password_hash(form.password1.data)
        user.password_date = datetime.date.today()
        ## DB 수정사항 반영
        db.session.commit()
        flash("연동이 완료되었습니다. 바뀐 정보로 로그인해주세요.")
        return redirect(url_for("auth.login_form"))

    return render_template("auth/signup_0000.html", user=user, form=form)


@bp.route('/find_password/', methods=["GET", "POST"])
def find_password():
    """비밀번호 변경 페이지 Backend Code

    Returns:
        처음: Login page html 렌더링
        Post 호출 시: Main menu page로 이동
    """
    ## 비밀번호 찾기 Form 불러오기
    form = FindPassword()
    
    ## POST 요청 및 form에 정의한 것과 동일한 경우 아래 if 문이 실행
    if request.method == "POST" and form.validate_on_submit():
        
        ## 회원 정보 불러오기
        user = User.query.filter_by(phone=form.phone.data).first()
        
        ## 회원정보가 없는 경우
        if not user:
            flash("회원 정보가 없습니다.")
            return redirect(url_for("auth.login_form"))
        
        ## 회원정보에 있는 이메일과 새로 입력한 이메일이 다른 경우
        if user.email != form.email.data:
            flash("회원 정보가 일치하지 않습니다.")
            return redirect(url_for("auth.login_form"))
        
        ## 비밀번호 초기화
        user.password = "0000"
        ## DB 수정사항 반영 및 업로드
        db.session.commit()
        flash("비밀번호가 0000으로 초기화 되었습니다. 로그인하시면 비밀번호 변경 페이지로 이동합니다.")
        return redirect(url_for("auth.login_form"))

    return render_template("auth/find_password.html", form=form)
