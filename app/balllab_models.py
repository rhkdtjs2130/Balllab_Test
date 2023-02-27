from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    username = db.Column(db.String(120), unique=False, nullable=False)
    birth = db.Column(db.String(120), unique=False, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    password_date = db.Column(db.Date, nullable=False, server_default="2022-09-20")
    point = db.Column(db.Integer, nullable=False, server_default="0")
    admin_point = db.Column(db.Integer, nullable=False, server_default="0")
    user_type = db.Column(db.Integer, nullable=False, server_default="0")
    agreement = db.Column(db.Integer, nullable=False, server_default="1")
    agreement_option = db.Column(db.Integer, nullable=False, server_default="1")
    register_date = db.Column(db.Date, nullable=False, server_default="2022-09-21")
    
class BuyPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(150), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    username = db.Column(db.String(120), unique=False, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    product = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, unique=False, nullable=False)
    time = db.Column(db.String(120), unique=False, nullable=False)
    buy = db.Column(db.Integer, nullable=False, server_default="0")
    
class ReserveCourt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=False, nullable=False)
    area = db.Column(db.String(120), unique=False, nullable=False)
    time = db.Column(db.String(120), unique=False, nullable=False)
    court = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.String(150), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    username = db.Column(db.String(120), unique=False, nullable=False)
    buy = db.Column(db.Integer, nullable=False, server_default="0")
    mul_no = db.Column(db.String(120), unique=False, server_default="0")
    qr_path = db.Column(db.String(120), unique=False)
    
class PayDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mul_no = db.Column(db.String(120), unique=False, nullable=False, server_default="NA")
    goodname = db.Column(db.String(120), unique=False)
    date = db.Column(db.Date, nullable=True)
    area = db.Column(db.String(120), unique=False, nullable=True)
    time = db.Column(db.String(120), nullable=True)
    price = db.Column(db.Integer, unique=False, nullable=False)
    used_point = db.Column(db.Integer, nullable=False, unique=False)
    used_admin_point = db.Column(db.Integer, nullable=False, unique=False, server_default='0')
    recvphone = db.Column(db.String(120), unique=False, nullable=False)
    pay_date = db.Column(db.DateTime, nullable=False)
    pay_type = db.Column(db.String(120), nullable=False)
    pay_state = db.Column(db.String(120), nullable=False)
    
class DoorStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(120), nullable=False, server_default='0')
    
class ReservationStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(120), unique=False, nullable=False)
    court = db.Column(db.String(120), unique=False, nullable=False)
    court_nm = db.Column(db.String(120), unique=False, nullable=False, server_default='0')
    status = db.Column(db.String(120), nullable=False, server_default='0')
    
class CourtList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(120), unique=False, nullable=False)

class PointTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False, server_default='10000')
    point = db.Column(db.Integer, nullable=False, server_default='10000')
    
class CourtPriceTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(120), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False, server_default='10000')
    
class GrantPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, unique=False, nullable=False)
    admin_name = db.Column(db.String(120), unique=False, nullable=False)
    admin_phone = db.Column(db.String(150), unique=False, nullable=False)
    user_name = db.Column(db.String(120), unique=False, nullable=False)
    user_phone = db.Column(db.String(150), unique=False, nullable=False)
    point = db.Column(db.Integer, nullable=False, server_default="0")


##### 다운드롭 메뉴에서 데이터를 정제하여 가져오는 과정에 많은 에러가 발생
##### 기존에 생성된 db.Model 클래스 방식으로 진행이 되면 안되고, models.Model 클래스로 QuerySet 매니저를 사용하게 끔, 클래스를 생성 해주어야 함
##### 생성은 되었으나, Flask db migrate 과정에서 모듈 순환참조 오류가 발생
##### 보통 이경우는 파이썬 모듈명과 작업 폴더내 파일명이 동일해서 발생되는 문제임.....;;; 이거 현재 문제를 찾는중
##### 위 문제가 해결이 안되면, HTML 문서에 일일이 입력을 해야 하는 번거로움

### 추후, 편리성을 위해서, DB만 바꾸어주면, HTML에서도 자동으로 수정되는 편리함 

## LessonPriceManager클래스는 LessonPrice 모델 클래스에 대한 커스텀 매니저로, get_area_list 메서드를 포함

from app import models

class LessonPriceManager(models.Manager):
    def get_area_list(self):
        return self.distinct('area').values_list('area', flat=True)

## objects 변수를 LessonPriceManager의 인스턴스로 설정
class LessonPrice(models.Model):
    id = models.IntegerField(primary_key=True)
    area = models.CharField(max_length=120)
    lesson_name = models.CharField(max_length=120)
    enrollment = models.IntegerField(default=1)
    lesson_price = models.IntegerField(default=10000)

    objects = LessonPriceManager()

############################################################################################################################################    

class LessonCoach(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(120), nullable=False)
    coach_name = db.Column(db.String(120), nullable=False)

class ReservationLesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(120), unique=True, nullable=False)
    lesson_name = db.Column(db.String(120), nullable=False)
    coach_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.String(150), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    time = db.Column(db.String(120), unique=False, nullable=False)