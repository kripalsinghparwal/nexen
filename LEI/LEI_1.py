import os
import time
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup as bs
from io import StringIO
import requests
import json
import urllib3
import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from io import StringIO


import json
import os
import time
import requests
import shutil
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")
import requests
import time
from bs4 import BeautifulSoup as bs
from seleniumbase import Driver

driver = Driver(uc=True, headless=False)

session = requests.Session()

def refresh_cf_clearance(lei):
    url = f"https://www.legalentityidentifier.in/leicert/{lei}/"

    print("Opening browser for fresh cookies...")

    driver.uc_open_with_reconnect(
        url,
        reconnect_time=6
    )

    time.sleep(10)

    cookie_dict = {
        c["name"]: c["value"]
        for c in driver.get_cookies()
    }

    print(
        "New cf_clearance:",
        cookie_dict.get("cf_clearance")
    )

    session.cookies.clear()

    for k, v in cookie_dict.items():
        session.cookies.set(k, v)

    return cookie_dict



def LeiResponseByServer(data):
    data_push_url = "http://103.233.79.196:8070/companies/updates_/companyLeis"

    header = {
        "Content-Type": "application/json"
        }
    #for datas in file:
      #  data = datas.replace('},', '}')

    try:
        #json_data = json.dumps(data)
        lei = data.get("lei")

        if "copy" in lei:
            lei = lei.split("copy")[0].strip()
            data["lei"] = lei

        if lei:
            print(data)

            response = requests.post(
                url=data_push_url,
                data=json.dumps([data]),
                headers=header
            )

            print(response.content)

    except Exception as e:
        print("Exception occur in lei :", e)

        with open("Unprocessed_lei_data.txt", "a+") as textfile:
            textfile.write(data)

# Define the template for the LEI payload
lei_payload_template = {
    "lei": None,
    "legalName": None,
    "leiStatus": None,
    "regStatus": None,
    "registeredAddress": None,
    "nextRenewalDate": None,
    "lastUpdateDate": None,
    "managingLou": None,
    "corroborationLevel": None,
    "validatedAs": None,
    "city": None,
    "postalCode": None,
    "parentCompanyLei": None,
    "parentCompanyName": None,
    "ultimateParentCompanyLei": None,
    "ultimateParentCompanyName": None
}


# Function to write the payload to a text file
def write_to_txt(lei_payload):
    file = f"D:\\LEI\\Lei_data\\lei_data_{today}.txt"
    with open(file, 'a') as text_file:
        formatted_payload = json.dumps(lei_payload)  # Format JSON payload with indentation
        text_file.write(formatted_payload)
        text_file.write(",\n")


# Function to extract parent information
def get_parent_info(parent_rows):
    parent_info = {}
    for parent_row in parent_rows:
        link = parent_row.find('a')
        if link:
            parent_name = link.text.strip()
            parent_lei = link['href'].split('=')[-1]
            parent_type = parent_row.text.strip()

            if 'Direct parent' in parent_type:
                parent_info['Direct Parent'] = {'name': parent_name, 'lei': parent_lei}
            elif 'Ultimate Parent' in parent_type:
                parent_info['Ultimate Parent'] = {'name': parent_name, 'lei': parent_lei}

    return parent_info


# Function to combine information into key-value pairs
def get_complete_info(Lei_reg_info, comp_info, add_info):
    key_value_pairs = []

    for index, row in Lei_reg_info.iterrows():
        key_value_pairs.append({row[0]: row[1]})
    for index, row in comp_info.iterrows():
        key_value_pairs.append({row[0]: row[1]})
    for index, row in add_info.iterrows():
        key_value_pairs.append({row[0]: row[1]})

    return key_value_pairs


# Function to scrape LEI data and populate the payload


def getLei_no(lei):
    try:
        lei_payload = lei_payload_template.copy()  # Reset payload

        # session = requests.Session()
        url = f"https://www.legalentityidentifier.in/leicert/{lei}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        # cookies = {
        #     "_ga": "GA1.1.4651009.1756896153",
        #     "__zlcmid": "1TSnt74zf0CmI3z",
        #     "_uetvid": "b27ceb7088b211f09991535d9889817c",
        #     "_clck": "1xm8gv7^2^g4l^1^2072",
        #     "_ga_23H8DVQ23S": "GS2.1.s1774259402$o8$g0$t1774259402$j60$l0$h0",
        #     "cf_clearance": "Mg3CH8XleiwFxq4_CDygLdKka5VG4WBoyqUIKnW6r0w-1781861793-1.2.1.1-GbFeLOo0szlMBZ7noxiG6SjdJHY_Li8uEwAeV26pY88RIyJL6wBRPQrEtK2EFsbFHJf6.RzG7qbaxEBNfgtJz0xufQK9uXuuAARHj9vUDtZy7YWU9gg1JmdVk9JcObGKlBqc.5bOQDcGACaLW52i5Wz9NQ63mJ6UkxZpob538n.yMpjh.9pC7NGYNYu3q8ROWOnoq2_FLaceW7jEi2uV04xSUmrtZbwwG.Ld3ct7YWhEIWn1qkycB4UuGZKcQhjtfdMySB7_0LsMVTRDyDxEWJIQETwRtT6ECcmNrCZAQjIIG9LCwLyzKF6oEeobEdzfDkPAtC_tAsIl5Vdtz0irsC0Yijq658HEDAv_p7fOlb5BSmceGN97AgflCoUFpUakGDZJW3G490u9x47doEqrv0QiYDtmSPeSRCFkQfMfRtaFmWsN3MhQDxTm8UB8jcho"
        # }

        resp = session.get(
            url,
            headers=headers,
            timeout=60
        )

        if resp.status_code != 200:
            refresh_cf_clearance(lei)
            resp = session.get(
                url,
                headers=headers,
                timeout=60
            )
        soup = bs(resp.text, "html.parser")
        # print(soup)
        tables = soup.find_all(class_="min-w-full divide-y-1 divide-gray-200")
        # print(tables)
        print(len(tables))
        if len(tables) < 7:
            raise ValueError(f"Expected ≥7 tables, found {len(tables)}")

        # ---------------- Parent info ----------------
        related_companies = tables[6]
        parent_rows = related_companies.find_all("div", class_="parent mb-1")
        parent_info = get_parent_info(parent_rows)

        # ---------------- Main tables ----------------
        company_data = tables[2]
        Lei_reg_detail = tables[3]
        Legal_add = tables[4]

        comp_info = pd.read_html(StringIO(str(company_data)))[0]
        Lei_reg_info = pd.read_html(StringIO(str(Lei_reg_detail)))[0]
        add_info = pd.read_html(StringIO(str(Legal_add)))[0]

        key_value_pairs = get_complete_info(
            Lei_reg_info,
            comp_info,
            add_info
        )

        # ---------------- Payload mapping ----------------
        if key_value_pairs:
            for pair in key_value_pairs:
                key, value = list(pair.items())[0]

                if key == 'LEI code':
                    lei_payload['lei'] = value.split("copy")[0].strip()

                elif key == 'Legal name':
                    lei_payload['legalName'] = value

                elif key == 'Entity status':
                    lei_payload['leiStatus'] = value

                elif key == 'Status':
                    lei_payload['regStatus'] = value

                elif key == 'Legal address':
                    lei_payload['registeredAddress'] = [value]

                elif key == 'Next renewal date':
                    lei_payload['nextRenewalDate'] = value

                elif key == 'Last update':
                    lei_payload['lastUpdateDate'] = value

                elif key == 'Managing LOU':
                    lei_payload['managingLou'] = value.replace('LIMITED', 'LIMITED ')

                elif key == 'Validation sources':
                    lei_payload['corroborationLevel'] = value

                elif key == 'Validated As':
                    lei_payload['validatedAs'] = value

                elif key == 'City':
                    lei_payload['city'] = value

                elif key == 'Postal code':
                    lei_payload['postalCode'] = value

            if 'Direct Parent' in parent_info:
                lei_payload['parentCompanyLei'] = parent_info['Direct Parent']['lei'].split('/')[-2]
                lei_payload['parentCompanyName'] = parent_info['Direct Parent']['name']

            if 'Ultimate Parent' in parent_info:
                lei_payload['ultimateParentCompanyLei'] = parent_info['Ultimate Parent']['lei'].split('/')[-2]
                lei_payload['ultimateParentCompanyName'] = parent_info['Ultimate Parent']['name']

        return lei_payload

    except Exception as e:
        print(f"[ERROR] LEI {lei}: {e}")

        path = r"D:\LEI\Unprocessed_lei"
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, "Unprocessed_lei1.csv"), "a+", encoding="utf-8") as f:
            f.write(lei + "\n")

        time.sleep(5)
        return None



# # Read the LEI data from the CSV file
# df_leis = pd.read_csv(r"D:\LEI\DL2_down.csv", encoding='ISO-8859-1')
df_leis = pd.read_csv(r"D:\LEI\Unprocessed_lei\Unprocessed_lei.csv", encoding='ISO-8859-1')
leis = df_leis['id'].to_list()[:]
# leis = ["335800Y7E7U6XTY6N197"]
# Iterate over the LEIs and process each one



# warning disable
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def process_lei():
    # url = "https://nexensus.co.in/client/lei"
    #
    # res = requests.get(url, verify=False)
    #
    # leis = json.loads(res.text)
    # print("leis===",len(leis))
    # df_leis = pd.read_csv(r"D:\LEI\DL2_down.csv", encoding='ISO-8859-1')
    # leis = df_leis['LEI'].to_list()
    # cins = df_leis['CIN'].to_list()
    # try:
    #     for lei in leis:
    #         print(lei)
    #         lei_payload = getLei_no(lei['lei'])
    #         print(lei_payload)
    #         if lei_payload :
    #             write_to_txt(lei_payload)
    # df_leis = pd.read_csv(r"D:\LEI\newfile.csv", encoding='ISO-8859-1')
    #
    # leis = df_leis['LEI'].to_list()[:]
    # cins = df_leis['CIN'].to_list()[:]
    # leis = ["984500ABAFD409451538"]
    try:
        # for lei, cin in zip(leis, cins):
        #     print("LEI:", lei)
        for lei in leis:
            # print("CIN:", cin)

            lei_payload = getLei_no(lei)  # direct pass karo

            if lei_payload:
                # 👉 yaha CIN update karo
                # print("old=",lei_payload)
                # lei_payload['validatedAs'] = cin

                print("Updated Payload:", lei_payload)

                write_to_txt(lei_payload)
                LeiResponseByServer(lei_payload)
                time.sleep(1)
    
    except Exception as e:
        print(f"[ERROR] LEI {lei}:")


import schedule
import time

def main():
    # ----- process lei---
    process_lei()


main()

# schedule.every().day.at("11:38").do(main)
#
# while True:
#     schedule.run_pending()
#     time.sleep(60)
