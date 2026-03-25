import csv
import time
import json
import os.path
from bs4 import BeautifulSoup as bs
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # Optional, for automatic driver management

# Create a Service object
service = Service(ChromeDriverManager().install())  # or specify your path directly here

# Pass the Service object to the WebDriver
driver = webdriver.Chrome(service=service)
url = "https://services.gst.gov.in/services/searchtp"
# Set the path to the WebDriver (make sure you have downloaded it)
# driver_path = r'D:\cromedriver\chromedriver-win64\chromedriver.exe'  # For Chrome
# # driver_path = '/path/to/your/geckodriver'  # For Firefox
#
# # Initialize the WebDriver (Chrome in this case)
# driver = webdriver.Chrome(executable_path=driver_path)


def extract_data_from_html(gstin, html_content):
    soup = bs(html_content, 'html.parser')

    # Prepare data for CSV
    data = {}
    data['GSTIN'] = gstin

    # Extracting values with None checks
    inners = soup.find_all(class_='inner')
    if len(inners) == 4:
        # A function to handle the extraction of key-value pairs from each "inner"
        def extract_inner_data(inner_class):
            extracted_data = {}
            inner_classes = inner_class.find_all(class_='col-sm-4 col-xs-12')
            for inner_class in inner_classes:
                p_tags = inner_class.find_all('p')
                if len(p_tags) >= 2:  # Ensure there are at least 2 <p> tags
                    key = p_tags[0].text.strip()
                    value = p_tags[1].text.title().strip()
                    extracted_data[key] = value
            return extracted_data

        # Extract data from all 4 "inners"
        for i in range(4):
            inner_data = extract_inner_data(inners[i])
            data.update(inner_data)  # Merge the extracted data into the main dictionary

    # Write to CSV with headers and values
    file_path = r'D:\Nexensus_Projects\GST_TaxPayer\gstinScrapedDataSelenium.csv'

    # Check if the file exists
    file_exists = os.path.exists(file_path)

    # Write to CSV with headers and values
    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # If the file doesn't exist, write the header
        if not file_exists:
            writer.writerow(data.keys())  # Write headers

        # Write values
        writer.writerow(data.values())  # Write values

    print("Data has been written to business_info.csv")


def startGstinScraping():

    try:
        df = pd.read_csv(r'D:\Nexensus_Projects\GST_TaxPayer\gstin.csv')  # Change Name87
        gstins = df["GSTIN"].to_list()  # index numb
        for gstin in gstins:


            print(gstin)
            driver.get(url)
            time.sleep(2)
            driver.find_element(By.ID, 'for_gstin').send_keys(gstin)
            driver.find_element(By.ID, 'fo-captcha').send_keys(" ")
            driver.maximize_window()
            time.sleep(10)  # Time to delay or fast the captcha input

            table_id = driver.find_element(By.XPATH, '//*[@id="lottable"]/div[2]')
            source_code = table_id.get_attribute("outerHTML")
            extract_data_from_html(gstin, source_code)
        driver.quit()
    except Exception as e:
        print("Exception :", e)


startGstinScraping()
