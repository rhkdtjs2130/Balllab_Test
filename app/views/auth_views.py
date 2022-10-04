import datetime

from flask import Blueprint, url_for, render_template, flash, request, session, g, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect

from app.forms import UserLoginForm, UserCreateForm, AgreementForm, FindPassword
from app.models import User
from app import db

bp = Blueprint("auth", __name__, url_prefix='/auth')

@bp.route('/login/', methods=['GET', 'POST'])
def login_form():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        user = User.query.filter_by(phone=form.phone.data).first()
        if not user:
            error = "존재하지 않는 사용자입니다."
        elif (form.password.data == "0000") and (user.password == "0000"):
            return redirect(url_for("auth.signup_0000", phone=user.phone)) ## 정보 추가 페이지 가도록
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
        flash(error)
    return render_template("auth/login.html", form=form)

@bp.route('/agreement/', methods=['GET', 'POST'])
def signup_agreement():
    form = AgreementForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        if form.agree_1.data == "1" and form.agree_2.data == "1":
            if form.agree_3.data is None:
                agree_3 = 0
            else:
                agree_3 = 1
            return redirect(url_for("auth.signup", agree_3=agree_3))
        else:
            flash("동의를 하지 않으면 현재는 가입이 불가능합니다.")
            return redirect(url_for("auth.login_form"))
    
    return render_template("auth/signup_agreement.html", form=form)

@bp.route('/signup/<agree_3>', methods=('GET', 'POST'))
def signup(agree_3):
    form = UserCreateForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(phone=form.phone.data).first()
        if not user:
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
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.signup_check', phone=user.phone))
        else:
            flash('이미 존재하는 사용자입니다.')
    return render_template('auth/signup.html', form=form)

@bp.route('/signup/check/<phone>', methods=('GET', 'POST'))
def signup_check(phone):
    user = User.query.filter_by(phone=phone).first()
    return render_template('auth/signup_check.html', user=user)

@bp.route('/admin_login/', methods=['GET', 'POST'])
def admin_login_form():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        user = User.query.filter_by(phone=form.phone.data).first()
        ## Error
        ##
        if not user:
            error = "존재하지 않는 사용자입니다."
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 올바르지 않습니다."
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
def signup_0000(phone):
    form = UserCreateForm()
    user = User.query.filter_by(phone=phone).first()
    if request.method == "POST" and form.validate_on_submit():
        user.email = form.email.data
        user.password = generate_password_hash(form.password1.data)
        user.password_date = datetime.date.today()
        db.session.commit()
        flash("연동이 완료되었습니다. 바뀐 정보로 로그인해주세요.")
        return redirect(url_for("auth.login_form"))
    return render_template("auth/signup_0000.html", user=user, form=form)

@bp.route('/find_password/', methods=["GET", "POST"])
def find_password():
    form = FindPassword()
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(phone=form.phone.data).first()
        if not user:
            flash("회원 정보가 없습니다.")
            return redirect(url_for("auth.login_form"))
        if user.email != form.email.data:
            flash("회원 정보가 일치하지 않습니다.")
            return redirect(url_for("auth.login_form"))
        user.password = "0000"
        db.session.commit()
        flash("비밀번호가 0000으로 초기화 되었습니다. 로그인하시면 비밀번호 변경 페이지로 이동합니다.")
        return redirect(url_for("auth.login_form"))
    return render_template("auth/find_password.html", form=form)