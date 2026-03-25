from News_Tagging import get_category_tag, get_type_tag

##################################### CBI News scraping Code ##############################################################
import requests 
from bs4 import BeautifulSoup
import time
import json
import datetime
import os
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

newsSite = "CBI"
today = datetime.date.today()
# def write_to_txt_resolve(newData):
#     file1 = r'D:\Nexensus_Projects\News\\data_{}.txt'.format(newsSite)
#     text_file = open(file1, 'a')
#     text_file.write(newData)
#     text_file.write(",")
#     text_file.write("\n")
#     text_file.close()

# === Load existing JSON lines to avoid duplicates ===
file_path = r'D:\\Nexensus_Projects\\News\\data_{}.txt'.format(newsSite)
new_file_path = r'D:\\Nexensus_Projects\\News\\NewsData\\NewsPayload\\PendingNews_{}.txt'.format(today)
existing_news = set()
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                # Normalize JSON to consistent string (sorted keys, no spaces)
                normalized = json.dumps(json.loads(line), sort_keys=True, separators=(",", ":"))
                existing_news.add(normalized)
            except json.JSONDecodeError:
                continue

# === Safe write function ===
def write_to_txt_resolve(newData):
    normalized = json.dumps(newData, sort_keys=True, separators=(",", ":"))
    if normalized in existing_news:
        print("⏩ Skipping duplicate news item.")
        return

    existing_news.add(normalized)
    with open(file_path, 'a', encoding='utf-8') as text_file:
        text_file.write(json.dumps(newData))
        text_file.write(",\n")

    ##### Add new news to separate file also ################
    with open(new_file_path, 'a', encoding='utf-8') as text_file:
        text_file.write(json.dumps(newData))
        text_file.write(",\n")


# Create a session to persist cookies
session = requests.Session()
# Step 1: Set language to English
lang_url = "https://cbi.gov.in/lang/en"
session.get(lang_url, headers=headers, timeout=10)
time.sleep(2)

# Step 2: Now request the target page (will come in English)
response = session.get("https://cbi.gov.in/press-releases", headers=headers, timeout=10)
time.sleep(2)
soup = BeautifulSoup(response.content, 'html.parser')

table_body = soup.find('table', {'id' : 'commonDataTable'}).find('tbody')

thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
for row in table_body.find_all('tr'):
    # print(row)
    title = row.find_all('td')[1].text.replace("News Heading:", "").replace("\u2018", "").replace("\u2019", "").replace("\u2013", "").replace(
                            "\u00a3", "").replace("\u00a0", "").strip()
    date = row.find_all('td')[2].text.replace("News Date:", "").strip()
    link = row.find_all('td')[1].find("a")['href']
    date = datetime.datetime.strptime(date, '%d/%m/%Y')
    date = date.strftime('%Y-%m-%d')
    print("DD/MM/YYYY →", date)
    # if datetime.datetime.strptime(date, "%Y-%m-%d") < thirty_days_ago:
    #     break
    
    # #################### Block to get description form the link if required ################################
    # try:
    #     # Create a session to persist cookies
    #     session = requests.Session()
    #     # Step 1: Set language to English
    #     lang_url = "https://cbi.gov.in/lang/en"
    #     session.get(lang_url, headers=headers, timeout=10)

    #     # Step 2: Now request the target page (will come in English)
    #     des_res = session.get(link, headers=headers, timeout=20)
    #     # des_res = requests.get(link,headers=headers, timeout=20)
    #     des_soup =  BeautifulSoup(des_res.content, 'html.parser')
    #     description = des_soup.find('div', 'press-txt').text.replace("\u2018", "").replace("\u2019", "").replace("\u2013", "").replace(
    #                         "\u00a3", "").replace("\u00a0", "").replace("\u021d", "").replace("\u2014", "").replace("\u200b", "").replace("\u201c", "").replace(
    #                             "\u20b9", "").replace("\u2022", "").replace("\u1e62", "").replace("\u201d","").strip()
    #     # print("description :", description)
    # except Exception as e:
    #     print('e :', e)
    #     time.sleep(20)
    #     # Create a session to persist cookies
    #     session = requests.Session()
    #     # Step 1: Set language to English
    #     lang_url = "https://cbi.gov.in/lang/en"
    #     session.get(lang_url, headers=headers, timeout=10)

    #     # Step 2: Now request the target page (will come in English)
    #     des_res = session.get(link, headers=headers, timeout=20)
    #     # des_res = requests.get(link,headers=headers, timeout=20)
    #     des_soup =  BeautifulSoup(des_res.content, 'html.parser')
    #     description = des_soup.find('div', 'press-txt').text.replace("\u2018", "").replace("\u2019", "").replace("\u2013", "").replace(
    #                         "\u00a3", "").replace("\u00a0", "").replace("\u021d", "").replace("\u2014", "").replace("\u200b", "").replace("\u201c", "").replace(
    #                             "\u20b9", "").replace("\u2022", "").replace("\u1e62", "").replace("\u201d","").strip()

    category = get_category_tag(title)
    typeTag = get_type_tag(title)
    # newsData = {"heading": title, "newsDate": date, "link" : link, "newsBody": description}
    # newsData = {"companyName": None, "cin": None, "heading": title, "newsDate": date, "newsBody": description,  "link" : link, "category": category, "typeTag" : typeTag, "sentiment": None}
    newsData = {"companyName": None, "cin": None, "heading": title, "newsDate": date, "newsBody": None,  "link" : link, "category": category, "typeTag" : typeTag, "sentiment": None}
    # write_to_txt_resolve(json.dumps(newsData))
    write_to_txt_resolve(newsData)
    # time.sleep(2)
    # print("------------")
