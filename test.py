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
    'area':'center_2_3f',
    # 'area':'center_2_4f'
}

while True:
    sleep(0.5)
    result = requests.post("http://43.200.247.167/get_door_status", data=data).json()

    if result == 0:
        ## Aleady closed
        continue
    else:
        try:
            ## Execute Bluetooth open door function
            socket = BluetoothSocket( RFCOMM )
            socket.connect(("00:19:10:09:1B:42", 1))
            print("bluetooth connected!")
            sleep(0.5)

            msg = "1"
            socket.send(msg)

            print("finished")
            socket.close()
            
            ## Change door status to closed
            requests.post("http://43.200.247.167/door_close", data=data)
        except:
            print("Error Occurred")
        