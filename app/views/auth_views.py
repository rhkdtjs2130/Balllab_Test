from flask import Blueprint, url_for, render_template, flash, request, session, g, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import redirect

from app.forms import UserLoginForm, UserCreateForm
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
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 올바르지 않습니다."
        if error is None:
            session.clear()
            session['user_id'] = user.id
            _next = request.args.get('next', '')
            if _next:
                return redirect(_next)
            else:
                return redirect(url_for('main.user_menu', email=user.email))
        flash(error)
    return render_template("auth/login.html", form=form)

@bp.route('/agreement/')
def signup_agreement():
    return render_template("auth/signup_agreement.html")

@bp.route('/signup/', methods=('GET', 'POST'))
def signup():
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
            )
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.signup_check', email=user.email))
        else:
            flash('이미 존재하는 사용자입니다.')
    return render_template('auth/signup.html', form=form)

@bp.route('/signup/check/<email>', methods=('GET', 'POST'))
def signup_check(email):
    user = User.query.filter_by(email=email).first()
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
                return redirect(url_for('admin.admin_menu', email=user.email))
        flash(error)
    return render_template("auth/login_admin.html", form=form)