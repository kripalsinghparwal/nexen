from HighCourt.automation_test_scripts.main_test import initialize_session_and_captcha, cases_list_collection
from HighCourt.automation_test_scripts.inside_data_test import cases_details_collection
import json
import time

# Load JSON from file
with open(r'D:\Nexensus_Projects\HighCourt\mapped_court_benches.json', 'r', encoding='utf-8') as file:
    courts_data = json.load(file)

# Loop through each court/state
session, headers, captcha_text = initialize_session_and_captcha()
if not session or not captcha_text:
    print("Could not get a valid CAPTCHA. Exiting.")
    exit()

rgyear = '2023'
petres_value = int(input("enter value for getting petres \n 0 for Bank, 1 for Limited, 2 for LLP, 3 for LTD"))
petres_name = ["Bank", "Limited", "LLP", 'LTD'][petres_value]


cases_list_collection(courts_data, rgyear, petres_name, session, headers, captcha_text)
time.sleep(5)
cases_details_collection(courts_data, rgyear, petres_name)