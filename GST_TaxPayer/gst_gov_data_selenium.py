
import os
import time
import shutil
import csv
import json
import os.path
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # Optional, for automatic driver management
from tensorflow.keras.models import load_model
import requests
from tensorflow.keras import layers, models
import numpy as np
import cv2
from sklearn.model_selection import train_test_split
from datetime import datetime

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
    # print(preds)
    pred_text = ''.join(CHARACTERS[np.argmax(p)] for p in preds)
    return pred_text


# Create a Service object
service = Service(ChromeDriverManager().install())  # or specify your path directly here

# Pass the Service object to the WebDriver
driver = webdriver.Chrome(service=service)


url = "https://services.gst.gov.in/services/searchtpbypan"
def startGstinScraping():
    global gstin_payload, gstins_and_status_arr
    df = pd.read_excel(r'D:\Nexensus_Projects\GST_TaxPayer\panDeatils.xlsx', engine='openpyxl') # Change Name
    # # print(df.columns)
    PANS = df["PANS"].to_list()[:]# index numb
    # print("PANS===",PANS)2121
    #PANS =['AAACT2727Q']0
    driver.get(url)
    driver.maximize_window()
    time.sleep(3)
    for pan in PANS:
        print(pan)
        time.sleep(1)
        driver.find_element(By.ID, 'for_gstin').send_keys(pan)
        time.sleep(5)

        while True:
            captcha_element = driver.find_element(By.ID, 'imgCaptcha')
            os.makedirs('resolved_captchaset', exist_ok=True)
            os.makedirs('unresolved_captchaset', exist_ok=True)

            # Temporary file to hold the screenshot before naming
            temp_path = r'D:\Nexensus_Projects\GST_TaxPayer\captcha_screenshots\captcha.png'
            captcha_element.screenshot(temp_path)
            print("Screenshot saved temporarily as captcha.png")

            time.sleep(1)
            captcha_value = predict_captcha(model, temp_path)
            time.sleep(1)

            driver.find_element(By.ID, 'fo-captcha').send_keys(captcha_value)
            time.sleep(1)
            driver.find_element(By.ID, "lotsearch").click()
            time.sleep(3)

            # Target filename based on predicted text
            filename = f"{captcha_value}.png"

            if not any(i.text == "Enter valid letters shown in the image below" for i in driver.find_elements(By.CLASS_NAME, 'err')):
                print("Correct Captcha")
                shutil.move(temp_path, os.path.join('resolved_captchaset', filename))
                break
            else:
                print("Wrong Captcha")
                shutil.move(temp_path, os.path.join('unresolved_captchaset', filename))
        # driver.find_element(By.ID, 'fo-captcha').send_keys(" ")
        # driver.maximize_window()
        time.sleep(5)  # Time to delay or fast the captcha input
        gstins_and_status_arr = []
        try:
            li_elements = driver.find_elements(By.CLASS_NAME, 'page-item')
            length = len(li_elements)
            gstin_payload = {"PANS": pan, "gstinResList": None}



            # Case for Single Page
            if length == 0:
                table_id = driver.find_element(By.CLASS_NAME, 'table.tbl.inv.exp.table-bordered.ng-table')
                source_code = table_id.get_attribute("outerHTML")
                table = pd.read_html(source_code)
                print(table)
                table = table[0][['GSTIN/UIN', 'GSTIN/UIN Status','State']]
                table = table.rename(columns={'GSTIN/UIN': 'gstin', 'GSTIN/UIN Status': 'authStatus', 'State': 'State'})
                table = table.iloc[1:, :]
                tables = table.to_dict(orient="records")
                gstins_and_status_arr.extend(tables)


            # Case for more than One Page
            else:
                page = 1

                while page < length - 1:
                    li_elements = driver.find_elements(By.CLASS_NAME, 'page-item')
                    for li in li_elements:
                        try:
                            li_elements[page].find_element(By.TAG_NAME, 'a').click()
                            table_id = driver.find_element(By.CLASS_NAME, 'table.tbl.inv.exp.table-bordered.ng-table')
                            source_code = table_id.get_attribute("outerHTML")
                            table = pd.read_html(source_code)
                            print(table)
                            table = table[0][['GSTIN/UIN', 'GSTIN/UIN Status', 'State']]
                            table = table.rename(columns={'GSTIN/UIN': 'gstin', 'GSTIN/UIN Status': 'authStatus', 'State': 'State'})
                            table = table.iloc[1:, :]
                            tables = table.to_dict(orient="records")
                            gstins_and_status_arr.extend(tables)

                        except Exception as e:
                            print('No document', e)
                        break
                    page = page + 1
        except Exception as e:
            print("Exception",e)
            print("No gstin found for pan={}".format(pan))
            textfile = open(r"D:\Nexensus_Projects\GST_TaxPayer\panError.txt", "a+")
            textfile.write(pan + "\n")
            textfile.close()

        gstin_payload['gstinResList'] = gstins_and_status_arr
        print(json.dumps(gstin_payload))
        # time.sleep(10)
        write_to_csv(gstin_payload)


def write_to_csv(gstin_payload):
    file = r'D:\Nexensus_Projects\GST_TaxPayer\panDetails_ScrapedData.csv'# PANS88
    file_exists = os.path.isfile(file)
    print(file_exists)
    with open(file, 'a') as csvfile:
        headers = ['PAN', 'GSTIN']
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', fieldnames=headers)
        if not file_exists:
            writer.writeheader()

        writer.writerow({'PAN': gstin_payload['PANS'], 'GSTIN': json.dumps(gstin_payload)})


startGstinScraping()
driver.quit()
# print("Hello World")
