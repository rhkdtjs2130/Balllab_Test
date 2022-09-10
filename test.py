# %%
import requests

from time import sleep
from bluetooth import *

def open_door():
    socket = BluetoothSocket( RFCOMM )
    socket.connect(("00:19:10:09:1B:42", 1))
    print("bluetooth connected!")

    msg = "1"
    socket.send(msg)

    print("finished")
    socket.close()
    

# %%
data = {
    # 'area':'center_1',
    # 'area':'center_2_3f',
    'area':'center_2_4f'
}

while True:
    sleep(1)
    result = requests.post("http://127.0.0.1:5000/get_door_status", data=data).json()

    if result == 0:
        ## Aleady closed
        continue
    else:
        ## Execute Bluetooth open door function
        open_door()
        
        ## Change door status to closed
        requests.post("http://127.0.0.1:5000/door_close", data=data)
        