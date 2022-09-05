# %%
import requests
# %%
respond = requests.get("http://127.0.0.1:5000/user_menu/lkh256%40gmail.com/request_pay/point")
# %%
respond.json()
# %%
respond.text
# %%
url = "http://127.0.0.1:5000/user_menu/lkh256%40gmail.com/request_pay/point"
url = "https://balllab.co.kr"

dataform = {
    "userid":"balllab"
}

data = requests.post(url, data=dataform)
# %%

import requests

data = {
    "area":"주식회사볼랩",
    "date":"2022-09-05",
    "time":"1",
    "court":"1번",
    "email":"lkh256@gmail.com" 
    
}

url = "http://127.0.0.1:5000/user/qrcode_check"
respond = requests.post(url=url, data=data).json()
print(respond)
# %%
