import csv
import time
import json
import os.path
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
import random
import time
from tensorflow.keras.models import load_model
import cv2
import numpy as np
import shutil
start_time = time.time()

CAPTCHA_LENGTH = 6
CHARACTERS = '0123456789'
###### Code to load existing saved trained model ##########################################
model = load_model(r'D:\Nexensus_Projects\GST_TaxPayer\captcha_model_updated_20250604_152033.h5')

## Function to predict captcha text ####################################################################
def predict_captcha(model, image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (200, 50)) / 255.0
    img = img.reshape(1, 50, 200, 1)
    preds = model.predict(img)
    pred_text = ''.join(CHARACTERS[np.argmax(p)] for p in preds)
    return pred_text

# url = "https://services.gst.gov.in/services/searchtp"

def extract_data_from_json(gstin, json):
    print("Coming here for gstin :", gstin)
    data = {}
    data['GSTIN'] = gstin

    try:
        data['Legal Name of Business'] = json['lgnm'].title().strip()
    except Exception as e:
        print(e)
        data['Legal Name of Business'] = "N/A"
    
    try:
        data['Trade Name'] = json['tradeNam'].title().strip()
    except Exception as e:
        print(e)
        data['Trade Name'] = "N/A"
    
    try:
        data['Effective Date of registration'] = json['rgdt'].title().strip()
    except Exception as e:
        print(e)
        data['Effective Date of registration'] = "N/A"
    
    try:
        data['Constitution of Business'] = json['ctb'].title().strip()
    except Exception as e:
        print(e)
        data['Constitution of Business'] = "N/A"
    
    try:
        data['GSTIN / UIN  Status'] = json['sts'].title().strip()
    except Exception as e:
        print(e)
        data['GSTIN / UIN  Status'] = "N/A"
    
    try:
        data['Principal Place of Business'] = json['pradr']['adr'].title().strip()
    except Exception as e:
        print(e)
        data['Principal Place of Business'] = "N/A"
    
    try:
        data['Whether Aadhaar Authenticated?'] = json['adhrVFlag'].title().strip()
    except Exception as e:
        print(e)
        data['Whether Aadhaar Authenticated?'] = "N/A"
    
    try:
        data['Whether e-KYC Verified?'] = json['ekycVFlag'].title().strip()
    except Exception as e:
        print(e)
        data['Whether e-KYC Verified?'] = "N/A"
    return data


def startGstinScraping():
    try:
        # df = pd.read_csv(r'D:\Nexensus_Projects\GST_TaxPayer\gstin.csv')  # Change Name87
        # gstins = df["GSTIN"].to_list()  # index numb
        # for gstin in gstins:
        input_df = pd.read_csv(r"D:\Nexensus_Projects\GST_TaxPayer\panDetails_ScrapedData.csv")
        for i in range(len(input_df)):
            ls  = json.loads(input_df['GSTIN'][i])['gstinResList']
            # print(ls)
            if all(i['authStatus'].lower() == 'inactive' for i in ls):
                if len(ls) !=0:
                    print(ls)
                    gstin = ls[0]['gstin']
                    print(gstin)
                    final_data = {"GSTIN" : gstin}
                    # break
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
                            temp_path = r'D:\Nexensus_Projects\GST_TaxPayer\captcha_screenshots\captcha.png'
                            with open(temp_path, "wb") as f:
                                f.write(captcha_response.content)
                                print("Screenshot saved temporarily as captcha.png")
                            os.makedirs('resolved_captchaset', exist_ok=True)
                            os.makedirs('unresolved_captchaset', exist_ok=True)

                            captcha_value = predict_captcha(model, temp_path)
                            print("captcha value", captcha_value)

                            api_url = 'https://services.gst.gov.in/services/api/search/taxpayerDetails'
                            headers = {
                                'Content-Type': 'application/json',
                                'User-Agent': 'Mozilla/5.0',
                                'Referer': 'https://services.gst.gov.in/services/searchtp',
                                'Origin': 'https://services.gst.gov.in'
                            }
                            payload = {
                                'gstin': gstin,
                                'captcha': captcha_value
                            }
                            response = session.post(api_url, json=payload, headers=headers)

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
                                        print("No Record found for this pan :", gstin)
                                        # data['gstinResList'] = []
                                        # final_data = {"GSTIN" : gstin}
                                        break
                                else:
                                    print("Correct Captcha")
                                    shutil.move(temp_path, os.path.join('resolved_captchaset', filename))
                                    final_data = extract_data_from_json(gstin, data)
                                    break

                            else:
                                print("Request failed.")

                    except Exception as e:
                        print("Exception",e)
                        print("No details found for gstin={}".format(gstin))
                        textfile = open(r"D:\Nexensus_Projects\GST_TaxPayer\inactive_gstinError.txt", "a+")
                        textfile.write(gstin + "\n")
                        textfile.close()
                    finally:
                        # Define the fixed header structure
                        columns = ["GSTIN","Legal Name of Business","Trade Name","Effective Date of registration","Constitution of Business","GSTIN / UIN  Status","Principal Place of Business","Whether Aadhaar Authenticated?","Whether e-KYC Verified?"]
                        # final_data = {'GSTIN': "A", "Legal Name of Business": "B", "Principal Place of Business": "C"}
                        df = pd.DataFrame([final_data], columns=columns)
                        file_path = r'D:\Nexensus_Projects\GST_TaxPayer\inactive_gstinDetails_ScrapedData.csv'

                        # Check if the file exists
                        if not os.path.exists(file_path):
                            # If file doesn't exist, write with header
                            df.to_csv(file_path, index=False, mode='w', encoding='utf-8')
                        else:
                            # If file exists, append without writing the header
                            df.to_csv(file_path, index=False, mode='a', header=False, encoding='utf-8')

                        print("Data has been written to inactive_gstinDetails_ScrapedData.csv")
                        time.sleep(0.1)
                    # break
    except Exception as e:
        print("Exception :", e)


startGstinScraping()
