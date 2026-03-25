######################### Batch wise processing for tofler ####################################################
import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
from fuzzywuzzy import fuzz

# === List of realistic user agents (desktop + mobile mix) ===
USER_AGENTS = [
    # Chrome (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36 Edg/118.0.2088.61",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

def human_delay(a=2, b=5):
    """Random sleep between a and b seconds."""
    time.sleep(random.uniform(a, b))

def start_driver():
    """Initialize and return a new Chrome WebDriver instance with random user-agent."""
    ua = random.choice(USER_AGENTS)
    print(f"🧠 Using User-Agent: {ua}\n")

    service = Service(ChromeDriverManager().install())
    options = Options()

    # --- Headless Mode ---
    options.add_argument("--headless=new")     # Recommended for Chrome 109+
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={ua}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_after_manager(simplified: str):
    # Split on "manager" (case-insensitive), only once
    parts = re.split(r'manager', simplified, flags=re.IGNORECASE)
    
    if len(parts) < 2:
        return simplified  # or return None if you prefer
    
    result = parts[1]

    # Remove leading spaces, commas, periods
    result = result.lstrip(" ,.")

    return result.strip()
# === Load Input Data ===
import pandas as pd
input_list = pd.read_excel(r"D:\Nexensus_Projects\ToflerAndZuba\input_folder\Highcourt.xlsx")['c_name'].drop_duplicates().to_list()[:]

# === Output File ===
output_path = "HC_data.xlsx"
all_data = []

# === Resume if partial file exists ===
if os.path.exists(output_path):
    existing_df = pd.read_excel(output_path)
    processed_names = set(existing_df['input'])
    input_list = [name for name in input_list if name not in processed_names]
    all_data = existing_df.to_dict('records')
    print(f"🟡 Resuming — already processed {len(processed_names)} companies.")
else:
    print("🟢 Starting fresh extraction.")

batch_size = 50
driver = start_driver()

for idx, input_name in enumerate(input_list, start=1):
    try:
        driver.get("https://www.tofler.in/")
        time.sleep(2)

        # Clean company name for first attempt
        clean_name = input_name.strip().rstrip(',')
        driver.find_element(By.ID, "searchbox").send_keys(clean_name)
        time.sleep(4)
        # driver.find_element(By.ID, "ui-id-1").click()
        # time.sleep(2)

        # cin = driver.current_url.split("/")[-1]
        # corrected_name = driver.find_element(
        #     By.CLASS_NAME, "company_title.items-center.nowrap.gap-16"
        # ).text.strip()
        ul = driver.find_element(By.ID, "ui-id-1")
        for elment in ul.find_elements(By.TAG_NAME, "li"):
            corrected_name = elment.find_element(By.TAG_NAME, "a").get_attribute('data-company')
            corrected_name = re.sub(r"\s+", " ", corrected_name).strip()
            cin = elment.find_element(By.TAG_NAME, "a").get_attribute('data-cin')
            element_text = elment.text.strip()
            element_text = re.sub(r"\s+", " ", element_text).strip()
            status = element_text.lower().replace(corrected_name.lower(), "").strip().capitalize()

            print({"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status})
            all_data.append({"input": input_name, "corrected_name": corrected_name, "cin": cin, 'status' : status})
        # print()

    except Exception:
        print("❌ Failed — retrying with simplified name:", input_name)
        try:
            driver.get("https://www.tofler.in/")
            time.sleep(2)

            simplified = (
                input_name.lower()
                .replace("(p) limited.", "")
                .replace("(p) limited", "")  
                .replace("p limited.", "")  
                .replace("p Limited", "")  
                .replace("(p) ltd.", "")    
                .replace("(p).ltd.", "")
                .replace("p.Ltd.", "")  
                .replace("p Ltd.", "")  
                .replace("pLtd.", "")  
                .replace("(p) Ltd", "")
                .replace("(p)Ltd", "")
                .replace("pLtd", "")  
                .replace("p Ltd", "")          
                .replace("limited.", "")
                .replace("private.", "")
                .replace("limited", "")
                .replace("private", "")
                .replace("pvt.", "")
                .replace("ltd.", "")
                .replace("pvt", "")
                .replace("ltd", "")
                .replace("llp.", "")
                .replace("llp", "")
                .replace("messers", "")
                .replace("messars", "")
                .replace("m/s", "")
                .replace("()", "")
                # .replace("A.O.,", "")
                .strip()
                .rstrip(',')
                .lstrip(',')
                .lstrip(".")
            )
            if len(simplified) == 3:
                simplified = simplified + " "
            simplified = extract_after_manager(simplified)
            if "officer," in simplified:
                simplified = simplified.split("officer,")[1].strip()
            elif "officer ," in simplified:
                simplified = simplified.split("officer,")[1].strip()
            driver.find_element(By.ID, "searchbox").send_keys(simplified)
            time.sleep(4)
            # driver.find_element(By.ID, "ui-id-1").click()
            # time.sleep(2)

            # cin = driver.current_url.split("/")[-1]
            # corrected_name = driver.find_element(
            #     By.CLASS_NAME, "company_title.items-center.nowrap.gap-16"
            # ).text.strip()
            ul = driver.find_element(By.ID, "ui-id-1")
            for elment in ul.find_elements(By.TAG_NAME, "li"):
                corrected_name = elment.find_element(By.TAG_NAME, "a").get_attribute('data-company')
                corrected_name = re.sub(r"\s+", " ", corrected_name).strip()
                cin = elment.find_element(By.TAG_NAME, "a").get_attribute('data-cin')
                element_text = elment.text.strip()
                element_text = re.sub(r"\s+", " ", element_text).strip()
                status = element_text.lower().replace(corrected_name.lower(), "").strip().capitalize()

                print({"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status})
                all_data.append({"input": input_name, "corrected_name": corrected_name, "cin": cin, 'status' : status})
            # print()

        except Exception as e:
            # print("🚫 Not found:", input_name)
            print(e)
            all_data.append({"input": input_name, "corrected_name": None, "cin": None, "status": None})

    # === Restart driver + Save progress after every 50 ===
    if idx % batch_size == 0:
        print(f"\n💾 Saving progress and restarting browser after {idx} companies...\n")
        pd.DataFrame(all_data).to_excel(output_path, index=False)
        print(f"✅ Progress saved to {output_path}")

        driver.quit()
        time.sleep(20)
        driver = start_driver()
    if idx % 200 == 0:
        driver.quit()
        print("sleeping for 5 minutes for recovery")
        # time.sleep(300)
        time.sleep(random.uniform(80, 100))
        driver = start_driver()

# === Final save ===
driver.quit()
ratio_list = []
if all_data:
    final_df = pd.DataFrame(all_data)
    for row in final_df.itertuples():
        if type(row.corrected_name) == float or row.corrected_name == None:
            ratio_list.append(0)  
        else:
            ratio_list.append(fuzz.ratio(row.input.lower().strip(), row.corrected_name.lower().replace("(old name)", "").strip()))
    final_df['ratio'] = ratio_list
    final_df.to_excel(output_path, index=False)
    print(f"🎉 All done! Final file saved to {output_path}")

if all_data:
    final_df = pd.DataFrame(all_data)
    # final_df = pd.read_excel(r"D:\Nexensus_Projects\ToflerAndZuba\Book7_data.xlsx")
    ratio_list = []

    for row in final_df.itertuples():
        if isinstance(row.corrected_name, float) or row.corrected_name is None:
            ratio_list.append(0)
        else:
            ratio_list.append(fuzz.ratio(row.input.lower().strip(), row.corrected_name.lower().replace("(old name)", "").strip()))

    final_df['ratio'] = ratio_list

    # --- 1) Filter Active + ratio == 100 ---
    df_100_active = final_df[(final_df['status'] == 'Active') & (final_df['ratio'] == 100)]

    # --- 2) Remove rows from df_100_active based on input column ---
    df_remaining = final_df[~final_df['input'].isin(df_100_active['input'])]

    # --- 3) Filter 80Plus from remaining ---
    df_80_plus = df_remaining[df_remaining['ratio'] >= 80]

    # --- 4) Remaining after removing 80Plus ---
    df_remaining_final = df_remaining[~df_remaining['input'].isin(df_80_plus['input'])]

    # --- Save to Excel with multiple sheets ---
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        final_df.to_excel(writer, sheet_name='allData', index=False)
        df_100_active.to_excel(writer, sheet_name='100Active', index=False)
        df_80_plus.to_excel(writer, sheet_name='80Plus', index=False)
        df_remaining_final.to_excel(writer, sheet_name='remaining', index=False)

    print(f"🎉 All done! Final file saved to {output_path}")
