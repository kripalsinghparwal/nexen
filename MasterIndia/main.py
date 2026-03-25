import requests
import json
import time
import re
import pandas as pd
from datetime import datetime

start_time = datetime.now()
print("starting time : ", start_time)

output_data_template = {
    "InputBENEFICIARY_NAME" : None,
    "legalName": None,
    "gst": None,
    "pan": None,
}

def write_to_txt_resolve(output_data_template):
    file1 = r'D:\Nexensus_Projects\MasterIndia\output_folder\data4.txt'
    text_file = open(file1, 'a')
    text_file.write(output_data_template)
    text_file.write(",")
    text_file.write("\n")
    text_file.close()

def Master_India(name):
    try:
        updated_name_for_url = re.sub(r'\s+', ' ', name)
        url = "https://blog-backend.mastersindia.co/api/v1/custom/search/name_and_pan/?keyword=" + updated_name_for_url.replace(" ", "+")
        payload = {
            'keyword': updated_name_for_url
        }
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.mastersindia.co',
            'Referer': 'https://www.mastersindia.co/gst-number-search-by-name-and-pan/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

        delay = 5  # initial delay in seconds

        while True:
            response_post = requests.get(url, headers=headers, params=payload)
            
            if response_post.status_code == 429:
                retry_after = int(response_post.headers.get("Retry-After", delay))
                print(f"🔁 429 Too Many Requests for {name}. Retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                continue

            break  # exit loop if not 429

        if response_post.status_code == 206:
            print("No data available for:", name)
        else:
            result = response_post.json()
            datas = result['data']
            print(datas)

            for i in datas:
                if updated_name_for_url.strip().title() == i['lgnm'].strip().title():
                    output_data_template['InputBENEFICIARY_NAME'] = name
                    output_data_template['legalName'] = i['lgnm']
                    output_data_template['gst'] = i['gstin']
                    output_data_template['pan'] = i['gstin'][2:12]
                    write_to_txt_resolve(json.dumps(output_data_template))
                    print("✅ Data stored for company:", name)

    except Exception as e:
        print("❌ Exception for company {}:".format(name), e)
        with open(r"D:\\Nexensus_Projects\\MasterIndia\\output_folder\\failedData4.txt", "a", encoding='utf-8') as f:
            f.write(name)
            f.write("\n")


try:
    df = pd.read_excel(r'D:\\Nexensus_Projects\\MasterIndia\\input_folder\\remaining_companies.xlsx')
    if 'BENEFICIARY_NAME' not in df.columns:
        raise KeyError("'BENEFICIARY_NAME' column not found in the Excel file.")

    company_names = df['BENEFICIARY_NAME'].dropna().unique()

    # Step 2: Process Each Company Name
    for company in company_names[125:]:
        Master_India(str(company))
        time.sleep(5)
        # time.sleep(20)  # Adjust delay as needed to avoid rate limits

except Exception as e:
    print(f"❌ Error reading Excel file: {e}")

end_time = datetime.now()
print("end time : ", end_time)