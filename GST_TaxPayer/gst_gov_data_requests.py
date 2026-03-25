
import os
import time
import shutil
import csv
import json
import os.path
import pandas as pd
from tensorflow.keras.models import load_model
import requests
from tensorflow.keras import layers, models
import numpy as np
import cv2
from sklearn.model_selection import train_test_split
from datetime import datetime
import random
import time

start_time = time.time()

CAPTCHA_LENGTH = 6
CHARACTERS = '0123456789'
###### Code to load existing saved trained model ##########################################
model = load_model(r'D:\\Nexensus_Projects\\GST_TaxPayer\\captcha_model_updated_20250604_152033.h5')

## Function to predict captcha text ####################################################################
def predict_captcha(model, image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (200, 50)) / 255.0
    img = img.reshape(1, 50, 200, 1)
    preds = model.predict(img)
    pred_text = ''.join(CHARACTERS[np.argmax(p)] for p in preds)
    return pred_text

url = "https://services.gst.gov.in/services/searchtpbypan"
def startGstinScraping():
    global gstin_payload, gstins_and_status_arr
    df = pd.read_excel(r'D:\\Nexensus_Projects\\GST_TaxPayer\\panDeatils.xlsx', engine='openpyxl') # Change Name
    # # print(df.columns)
    PANS = df["PANS"].to_list()[:]# index numb

    for pan in PANS:
        print(pan)
        gstin_payload = {"PANS": pan, "gstinResList": None}

        try:
            while True:
                session = requests.Session()
                rnd = random.random()
                captcha_url = f'https://services.gst.gov.in/services/captcha?rnd={rnd}'
                captcha_response = session.get(captcha_url)
                if captcha_response.status_code != 200:
                    print("Failed to fetch captcha")
                    return
                # Temporary file to hold the screenshot before naming
                temp_path = r'D:\\Nexensus_Projects\\GST_TaxPayer\\captcha_screenshots\\captcha.png'
                with open(temp_path, "wb") as f:
                    f.write(captcha_response.content)
                    print("Screenshot saved temporarily as captcha.png")
                os.makedirs('resolved_captchaset', exist_ok=True)
                os.makedirs('unresolved_captchaset', exist_ok=True)

                captcha_value = predict_captcha(model, temp_path)
                print("captcha value", captcha_value)

                api_url = 'https://services.gst.gov.in/services/api/get/gstndtls'
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://services.gst.gov.in/services/searchtpbypan',
                    'Origin': 'https://services.gst.gov.in'
                }
                payload = {
                    'panNO': pan,
                    'captcha': captcha_value
                }
                response = session.post(api_url, json=payload, headers=headers)

                print(f"Status Code: {response.status_code}")
                # print("Response Text:")
                # print(response.text)

                # Target filename based on predicted text
                filename = f"{captcha_value}.png"
                if response.status_code == 200:
                    data = response.json()
                    print(data.keys())
                    if "errorCode" in data.keys():
                        if data["errorCode"] == "SWEB_9000":
                            print("Wrong Captcha")
                            shutil.move(temp_path, os.path.join('unresolved_captchaset', filename))
                        else:
                            print("Correct Captcha")
                            shutil.move(temp_path, os.path.join('resolved_captchaset', filename))
                            print("No Record found for this pan :", pan)
                            data['gstinResList'] = []
                            break
                    else:
                        print("Correct Captcha")
                        shutil.move(temp_path, os.path.join('resolved_captchaset', filename))
                        break

                else:
                    print("Request failed.")

        except Exception as e:
            print("Exception",e)
            print("No gstin found for pan={}".format(pan))
            textfile = open(r"D:\\Nexensus_Projects\\GST_TaxPayer\\panError.txt", "a+")
            textfile.write(pan + "\n")
            textfile.close()

        gstin_payload['gstinResList'] = data['gstinResList']
        print(json.dumps(gstin_payload))
        # time.sleep(10)
        write_to_csv(gstin_payload)
        time.sleep(0.1)


def write_to_csv(gstin_payload):
    file = r'D:\\Nexensus_Projects\\GST_TaxPayer\\panDetails_ScrapedData.csv'# PANS88
    file_exists = os.path.isfile(file)
    print(file_exists)
    with open(file, 'a') as csvfile:
        headers = ['PAN', 'GSTIN']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', fieldnames=headers)
        if not file_exists:
            writer.writeheader()

        writer.writerow({'PAN': gstin_payload['PANS'], 'GSTIN': json.dumps(gstin_payload)})

startGstinScraping()
print("Total time taken: {:.2f} seconds".format(time.time() - start_time))
