import requests
from PIL import Image
from io import BytesIO
import easyocr
import numpy as np
import json
from datetime import datetime
import time
# import threading
# from inside_data import get_inside_data
failed = []


def write_to_txt_resolve(data, stateName, i, petres_name, rgyear):
    updated_stateName = stateName.replace(" ", "_")
    file1 = r'D:\\Nexensus_Projects\\HighCourt\\High_court_data\\Highcourt_raw\\{}\\{}\\{}_Bench_{}.txt'.format(rgyear, petres_name, updated_stateName, i, petres_name)
    text_file = open(file1, 'a', encoding='utf-8')
    text_file.write(data)
    text_file.write(",")
    text_file.write("\n")
    text_file.close()


# Retry mechanism for the CAPTCHA request
def fetch_captcha_with_retry(session, url, headers, retries=5, timeout=120):
    for attempt in range(retries):
        try:
            response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return response
            else:
                print(f"Attempt {attempt + 1} failed with status code {response.status_code}. Retrying...")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed with error: {e}. Retrying...")
        # Wait before retrying
        time.sleep(2)
    # If all retries fail, return None
    print("All attempts to fetch CAPTCHA failed.")
    return None


def fetch_and_read_captcha(image):
    # image.show()
    # Convert the PIL image to a NumPy array
    image_np = np.array(image)
    # Create an EasyOCR reader
    reader = easyocr.Reader(['en'])  # Specify the language as English
    # Use EasyOCR to extract text from the image
    result = reader.readtext(image_np, detail=0)  # detail=0 returns just the text
    if result:
        text = ' '.join(result)
        print("Extracted Text:", text)
        return text
    else:
        print("No text found in the image.")
        return None
    
def initialize_session_and_captcha(max_attempts=15):
    test_payload = {
        'court_code': '1',
        'state_code': '13',  # Known valid state (e.g., Allahabad HC)
        'court_complex_code': '1',
        'caseStatusSearchType': 'CSpartyName',
        'f': 'Both',
        'petres_name': 'LTD',
        'rgyear': '2024'
    }

    for attempt in range(1, max_attempts + 1):
        print(f"Initializing session & CAPTCHA attempt {attempt}...")

        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0...'
            # Add more headers if needed
        }

        # Load main page to set cookies
        session.get("https://hcservices.ecourts.gov.in/", headers=headers, timeout=120)

        # Get CAPTCHA image
        captcha_url = "https://hcservices.ecourts.gov.in/hcservices/securimage/securimage_show.php"
        response = fetch_captcha_with_retry(session, captcha_url, headers)
        if not response:
            print("Failed to fetch CAPTCHA image.")
            continue

        image = Image.open(BytesIO(response.content))
        captcha_text = fetch_and_read_captcha(image)

        if not captcha_text:
            print("OCR failed to read CAPTCHA. Retrying...")
            continue

        # Validate CAPTCHA by submitting test payload
        test_payload['captcha'] = captcha_text
        resp = session.post(
            'https://hcservices.ecourts.gov.in/hcservices/cases_qry/index_qry.php?action_code=showRecords',
            headers=headers,
            data=test_payload,
            timeout=120
        )

        if "Invalid Captcha" in resp.text:
            print("CAPTCHA invalid. Retrying...")
            time.sleep(2)
            continue
        else:
            print("CAPTCHA validated successfully.")
            return session, headers, captcha_text

    print("All CAPTCHA attempts failed.")
    return None, None, None



def get_main_data(session, headers, captcha_text, stateCode, stateName, benchesNumber, petres_name, rgyear):
    # session = requests.Session()
    # headers = {
    #     'User-Agent': 'Mozilla/5.0...',
    #     # other headers
    # }

    # session.get("https://hcservices.ecourts.gov.in/", headers=headers)
    # captcha_url = "https://hcservices.ecourts.gov.in/hcservices/securimage/securimage_show.php"

    # max_attempts = 10

    # for attempt in range(max_attempts):
    #     print(f"Attempt {attempt + 1} of {max_attempts}")

    #     # Fetch and solve CAPTCHA
    #     response = fetch_captcha_with_retry(session, captcha_url, headers)
    #     if not response:
    #         print("Failed to fetch CAPTCHA.")
    #         continue

    #     image = Image.open(BytesIO(response.content))
    #     captcha_text = fetch_and_read_captcha(image)
    #     if not captcha_text:
    #         print("Failed to read CAPTCHA.")
    #         continue
    

    # Try submitting form for each court_code with solved CAPTCHA
    # for i in range(1, 7):
    for i in range(1, benchesNumber+1):
        payload = {
            'court_code': str(i),
            # 'state_code': '13',
            'state_code' : stateCode,
            'court_complex_code': '1',
            'caseStatusSearchType': 'CSpartyName',
            'captcha': captcha_text,
            'f': 'Both',
            # 'petres_name': 'LLP',
            'petres_name': petres_name,
            # 'rgyear': '2024'
            'rgyear' : rgyear
        }

        response = session.post(
            'https://hcservices.ecourts.gov.in/hcservices/cases_qry/index_qry.php?action_code=showRecords',
            headers=headers,
            data=payload,
            timeout=120
        )

        data = response.text
        print(f"Status Code for court_code {i}: {response.status_code}")

        if "Invalid Captcha" in data:
            print("Invalid CAPTCHA. Restarting attempt...")
            break  # Breaks out of court_code loop, will retry CAPTCHA
        elif '"con":["[]"]' in data:
            print("No record found for this bench {} of court {}".format(i, stateName))
        elif "con" in data:
            write_to_txt_resolve(data, stateName, i, petres_name, rgyear)
        else:
            print("Court {} not present".format(i))
            failed.append((stateCode, i))
            # Or write to file if preferred
            with open(r"D:\Nexensus_Projects\HighCourt\High_court_data\Highcourt_raw\failedData.txt", "a", encoding='utf-8') as f:
                f.write(f"{stateCode},{stateName},Bench: {i}\n")
        time.sleep(10)
    else:
        # Only reached if CAPTCHA was valid for both court_codes
        print("Success with all court codes.")
        return

    # print("Max retries exceeded. Exiting.")

# Load JSON from file
with open(r'D:\\Nexensus_Projects\\HighCourt\\mapped_court_benches.json', 'r', encoding='utf-8') as file:
    courts_data = json.load(file)

# Loop through each court/state
session, headers, captcha_text = initialize_session_and_captcha()
if not session or not captcha_text:
    print("Could not get a valid CAPTCHA. Exiting.")
    exit()

# ["Bank", "Limited", "LLP", 'LTD']
for petres_name in ["LLP"]:
    print("current petres :", petres_name)
    for court in courts_data[:]:
        stateCode = court['stateCode']
        stateName = court['stateName']
        benchesNumber = len(court['benches'])
        # petres_name = "Bank"
        # petres_name = petres_name
        rgyear = '2025'
        print("running : ", stateCode, stateName , benchesNumber, petres_name, rgyear)
        get_main_data(session, headers, captcha_text, stateCode, stateName , benchesNumber, petres_name, rgyear)
        time.sleep(5)
        print("-------------------------------------------------------------------")


# get_main_data()


# State Code: 13, State Name: Allahabad High Court
# State Code: 1, State Name: Bombay High Court
# State Code: 16, State Name: Calcutta High Court
# State Code: 6, State Name: Gauhati High Court
# State Code: 29, State Name: High Court for State of Telangana
# State Code: 2, State Name: High Court of Andhra Pradesh
# State Code: 18, State Name: High Court of Chhattisgarh
# State Code: 26, State Name: High Court of Delhi
# State Code: 17, State Name: High Court of Gujarat
# State Code: 5, State Name: High Court of Himachal Pradesh
# State Code: 12, State Name: High Court of Jammu and Kashmir
# State Code: 7, State Name: High Court of Jharkhand
# State Code: 3, State Name: High Court of Karnataka
# State Code: 4, State Name: High Court of Kerala
# State Code: 23, State Name: High Court of Madhya Pradesh
# State Code: 25, State Name: High Court of Manipur
# State Code: 21, State Name: High Court of Meghalaya
# State Code: 11, State Name: High Court of Orissa
# State Code: 22, State Name: High Court of Punjab and Haryana
# State Code: 9, State Name: High Court of Rajasthan
# State Code: 24, State Name: High Court of Sikkim
# State Code: 20, State Name: High Court of Tripura
# State Code: 15, State Name: High Court of Uttarakhand
# State Code: 10, State Name: Madras High Court
# State Code: 8, State Name: Patna High Court