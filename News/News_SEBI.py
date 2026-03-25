from News_Tagging import get_category_tag, get_type_tag

################################## SEBI news scraping code ################################################################
import requests
from bs4 import BeautifulSoup
import time
import json
import datetime
import os

newsSite = "SEBI"
endScraping = False
today = datetime.date.today()
# def write_to_txt_resolve(newData):
#     file1 = r'D:\Nexensus_Projects\News\\data_{}.txt'.format(newsSite)
#     text_file = open(file1, 'a')
#     text_file.write(json.dumps(newData))
#     text_file.write(",")
#     text_file.write("\n")
#     text_file.close()

# === Load existing JSON lines to avoid duplicates ===
file_path = r'D:\Nexensus_Projects\News\\data_{}.txt'.format(newsSite)
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


url = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=6&ssid=23&smid=0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.sebi.gov.in",
    "Connection": "keep-alive"
}

cookies = {
    "JSESSIONID": "C7F7C8E8722D1736110467AA0D643BD3"
}



# Base payload (except nextValue which we will change)
base_payload = {
    "next": "n",
    "search": "",
    "fromDate": "",
    "toDate": "",
    "fromYear": "",
    "toYear": "",
    "deptId": "-1",
    "sid": "6",
    "ssid": "23",
    "smid": "0",
    "ssidhidden": "23",
    "intmid": "-1",
    "sText": "Media & Notifications",
    "ssText": "Press Releases",
    "smText": "",
    # "doDirect": "3"
}

# Loop through pages
# for page in range(0, 250):  # scrape first 231 pages
for page in range(0, 1): # scrape first 2 page
    if endScraping == True:
        print("So ending scraping data")
        break
    time.sleep(1)
    payload = base_payload.copy()
    payload["nextValue"] = str(page)
    payload['doDirect'] = str(page)

    r = requests.post(url, headers=headers, cookies=cookies, data=payload)
    print(f"Page {page} -> {len(r.text)} characters")
    # print(r.content)
    soup = BeautifulSoup(r.content, 'html.parser')
    # print(soup.find('table', {'id' : 'sample_1'}).find_all('tr')[0])
    try:
        for row in soup.find('table', {'id' : 'sample_1'}).find_all('tr')[1:]:
            date = row.find_all('td')[0].text
            date = datetime.datetime.strptime(date, '%b %d, %Y')  # parse string to datetime

            # ✅ Check if date is within the last 5 years from today
            today = datetime.datetime.now()
            five_years_ago = datetime.datetime(today.year - 5, 1, 1)
            # five_years_ago = today.replace(year=today.year - 5)

            if date >= five_years_ago:
                date = date.strftime('%Y-%m-%d')
                print("✅ Date within last 5 years:", date)
            else:
                endScraping = True
                print(f"❌ Date {date.strftime('%Y-%m-%d')} is older than 5 years")
                break
                # print(f"❌ Date {date.strftime('%Y-%m-%d')} is older than 5 years")
            # date = date.strftime('%Y-%m-%d')  # format to desired output
            pr_no = row.find('th').text
            # title  = row.find_all('td')[1].text.replace("\u2018", "").replace("\u2019", "").replace("\u2013", "").replace(
            #                     "\u00a3", "").replace("\u00a0", "").strip()
            title = row.find_all('td')[1].text.strip()
            link = row.find_all('td')[1].find('a')['href']
            category = get_category_tag(title)
            typeTag = get_type_tag(title)
            print('date  :', date)
            print('pr_no :', pr_no)
            print('title :', title)
            print('href  :', link)
            newsData = {"companyName": None, "cin": None, "heading": title, "newsDate": date, "newsBody": None,  "link" : link, "category": category, "typeTag" : typeTag, "sentiment": None}
            # newsData = {"companyName": None, "cin": None, "heading": title, "newsDate": date, "newsBody": None,  "link" : link, "pr_no": pr_no, "category": category, "typeTag" : typeTag, "sentiment": None}
            print(newsData)
            write_to_txt_resolve(newsData)
    except Exception as e:
        print(e)
        pass
    # parse r.text with BeautifulSoup or regex if it's HTML
