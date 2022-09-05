# %%
import datetime

import qrcode
import numpy as np
import matplotlib.pyplot as plt
import cv2

def make_qr_code(
    area, date, time, court, email
) -> tuple:
    
    ## Make dictionary about user data with generated passwd
    input_data = {
        "area":area,
        "date":date, 
        "time":time,
        "court":court,
        "email":email,
    }
    
    ## Generate QR Image
    qr = qrcode.QRCode(
        version=1, 
        box_size=10, 
        border = 5
    )

    ## Insert given information in qr image
    qr.add_data(input_data)
    qr.make(fit=True)
    
    ## Make QR Image
    img = qr.make_image(
        fill='black', 
        back_color='white'
    )
    
    return img

def decode_qr(
    img:np.ndarray
) -> dict:
    
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(img)
    
    return data

# %%

if __name__ == '__main__':
    img, passwd = make_qr_code(guest_id="subject_id", regist_time="2020-01-01")
    img.save("./sample.png")
    
    img = cv2.imread("./sample.png")
    decode_qr(img)

    plt.imshow(img)

    data = decode_qr(img=img)
    print(data)