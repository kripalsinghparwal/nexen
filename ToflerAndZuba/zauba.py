######################### Batch-wise Headless Zauba Scraper with multiple results from dropdown ####################################################
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


# === List of realistic user agents (desktop + mobile mix) ===
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36 Edg/118.0.2088.61",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
]


def human_delay(a=2, b=5):
    """Random sleep between a and b seconds."""
    time.sleep(random.uniform(a, b))


def start_driver(headless=True):
    """Initialize and return a new Chrome WebDriver instance with random user-agent."""
    ua = random.choice(USER_AGENTS)
    print(f"🧠 Using User-Agent: {ua}\n")

    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"user-agent={ua}")

    # if headless:
    #     options.add_argument("--headless=new")
    #     options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=service, options=options)
    return driver

def force_kill_driver():
    # Kill chromedriver
    os.system("taskkill /f /im chromedriver.exe")
    # Kill chrome if needed
    # os.system("taskkill /f /im chrome.exe")

def safe_quit(driver):
    try:
        driver.quit()
    except:
        pass

    # If Selenium cannot quit → force kill processes
    force_kill_driver()


# === Load Input Data ===
# false_df = pd.read_excel(r"D:\Nexensus_Projects\pdfFoms\Tofler_data_2.xlsx")

# input_df = pd.read_excel(r"D:\Nexensus_Projects\ToflerAndZuba\Book4_data.xlsx")
# input_list = input_df[input_df['cin'].isna()]['input'].tolist()

input_list = pd.read_excel(r"D:\Nexensus_Projects\ToflerAndZuba\input_folder\NCLT_17-11-2025.xlsx")['c_name'].to_list()[:]

# === Output File ===
output_path = "NCLT_17-11-2025.xlsx"
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

batch_size = 25
driver = start_driver(headless=True)


# === Helper to simplify names ===
def simplify_name(name):
    return (
        name.lower()
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
        .strip()
        .rstrip(',')
    )

def clean_excel_string(s):
    if not isinstance(s, str):
        return s
    # Remove illegal characters for Excel
    return re.sub(r'[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]', '', s)

# === Core logic to fetch multiple results ===
def process_company(driver, input_name):
    """Search company, click all results, and capture data."""
    results_data = []
    clean_name = input_name.strip().rstrip(',')
    search_attempts = [clean_name, simplify_name(input_name)]

    for attempt_no, search_term in enumerate(search_attempts, start=1):
        try:
            driver.get("https://www.zaubacorp.com/")
            human_delay()

            search_box = driver.find_element(By.ID, "searchid")
            search_box.clear()
            search_box.send_keys(search_term)
            human_delay()

            result_div = driver.find_element(By.ID, "result")
            result_items = result_div.find_elements(By.TAG_NAME, "div")

            if not result_items:
                print(f"⚠️ No results found for attempt {attempt_no}: {search_term}")
                continue

            print(f"🔍 Found {len(result_items)} results for: {search_term}")

            for i in range(len(result_items)):
                try:
                    # Reopen and search again each time to avoid stale elements
                    driver.get("https://www.zaubacorp.com/")
                    human_delay()
                    search_box = driver.find_element(By.ID, "searchid")
                    search_box.clear()
                    search_box.send_keys(search_term)
                    human_delay()

                    fresh_results = driver.find_element(By.ID, "result").find_elements(By.TAG_NAME, "div")

                    if i >= len(fresh_results):
                        continue

                    print(f"➡️ Clicking result {i + 1}/{len(fresh_results)} for {input_name}")
                    fresh_results[i].click()
                    human_delay()

                    current_url = driver.current_url
                    try:
                        corrected_name = driver.find_element(By.ID, "title").text
                    except Exception:
                        corrected_name = current_url.split("/")[-1].rsplit("-", 1)[0].replace("-", " ")

                    cin = None
                    if "-" in current_url.split("/")[-1]:
                        if "llp" in input_name.lower():
                            cin = current_url.split("/")[-1].rsplit("-", 1)[0].rsplit("-", 1)[1] + " " + current_url.split("/")[-1].rsplit("-", 1)[1]
                        else:
                            cin = current_url.split("/")[-1].rsplit("-", 1)[1]

                    print(f"✅ {corrected_name} — {cin}")
                    results_data.append({
                        "input": input_name,
                        "search_term": search_term,
                        "corrected_name": corrected_name,
                        "cin": cin,
                        "url": current_url
                    })

                    # === Stop further dropdown clicks if corrected name matches cleaned input ===
                    cleaned_input = simplify_name(input_name)
                    cleaned_corrected = simplify_name(corrected_name)
                    if cleaned_input == cleaned_corrected:
                        print(f"🛑 Match found for '{input_name}' — stopping further dropdown clicks.")
                        break

                except Exception as e:
                    print(f"❌ Error on {input_name} result {i+1}: {e}")
                    continue

            if results_data:
                break  # stop after successful search
        except Exception as e:
            print(f"🚫 Search failed for attempt {attempt_no}: {search_term} — {e}")
            # driver.quit()
            safe_quit()
            time.sleep(random.randint(3, 8))
            driver = start_driver(headless=True)
            continue

    if not results_data:
        results_data.append({
            "input": input_name,
            "search_term": None,
            "corrected_name": None,
            "cin": None,
            "url": None
        })

    return results_data


# === Main Loop ===
for idx, input_name in enumerate(input_list, start=1):
    input_name = input_name.strip()
    company_results = process_company(driver, input_name)
    all_data.extend(company_results)

    # === Restart + save every batch ===
    if idx % batch_size == 0:
        print(f"\n💾 Saving progress and restarting browser after {idx} companies...\n")
        output_df = pd.DataFrame(all_data).applymap(clean_excel_string)
        output_df.to_excel(output_path, index=False)
        # pd.DataFrame(all_data).to_excel(output_path, index=False)
        print(f"✅ Progress saved to {output_path}")
        # driver.quit()
        safe_quit()
        time.sleep(random.randint(5, 10))
        driver = start_driver(headless=True)

# === Final Save ===
# driver.quit()
safe_quit()
if all_data:
    output_df = pd.DataFrame(all_data).applymap(clean_excel_string)
    output_df.to_excel(output_path, index=False)
    # pd.DataFrame(all_data).to_excel(output_path, index=False)
    print(f"🎉 All done! Final file saved to {output_path}")
