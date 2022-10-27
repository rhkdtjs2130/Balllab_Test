# Balllab Web Server


### Package 설치
``` {bash}
pip install flask
pip install flask-migrate
```

``` {bash}
cd "any directory that you want to save repository"
git clone https://github.com/balllab-korea/balllab_web.git
cd balllab_web
```

### 환경변수 설정
[환경변수 설정방법은 이쪽을 참고](https://wikidocs.net/81042)

### Debugging 서버 실행
``` {bash}
flask db init

## 모델을 새로 생성하거나 변경할떄 사용
flask db migrate

## 모델 변경 내역을 database에 적용할때 사용
flask db upgrade


## debugging 서버 실행
flask run
```