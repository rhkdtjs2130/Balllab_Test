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

[환경변수(윈도우) 설정 방법은 이쪽을 참고](https://wikidocs.net/81042)

APP_CONFIG_FILE=/Users/lkh256/Studio/Development/balllab_web/config/development.py 를 추가한다.   
(Caution !!)APP_CONFIG_FILE="본인에게 맞는 웹사이트 개발 폴더 내 development.py 경로"를 위의 링크를 보고 입력하면된다. 

환경변수 설정(Linux)
``` {bash}
vim ~/.bashrc
```


vim 사용법 i (입력), esc (입력모드 나가기), :wq! (저장후 나가기)
맨 아래에 다음 코드를 추가한다.
FLASK_DEBUG -> 디버깅 모드, 개발 모드
APP_CONFIG_FILE -> "웹사이트 개발 폴더 내 development.py 경로"

아래 코드는 dev를 터미널에 입력하면 debug 모드 app_config_file 설정, 그리고 가상환경을 키는 코드임 (Linux, Mac)

``` {bash}
alias dev="export FLASK_DEBUG=true;export APP_CONFIG_FILE=/Users/lkh256/Studio/Development/balllab_web/config/development.py;conda activate dev"
```

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
