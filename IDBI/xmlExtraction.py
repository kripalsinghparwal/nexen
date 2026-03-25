##################! Final Code to get pdf link and extract attached standalone xml #######################
import requests
import os
import pandas as pd
import json
from datetime import datetime
import fitz
import xml.etree.ElementTree as ET
import time
import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST", "GET"]
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)



years = ["2023", "2024", "2025"]

cins = pd.read_excel(
    r"D:\Nexensus_Projects\IDBI\input_data\IDBI_BAnk_TrackingList.xlsx"
)['CIN'].to_list()[:]

url = "https://nexensus.club/checkfiling/file-search/"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# log_file = "error_and_not_found_logs.txt"
log_file = f"Logs\\error_and_not_found_logs_{datetime.now().strftime('%Y-%m-%d')}.txt"
no_attachment_log_file = f"Logs\\no_attachemet_logs_{datetime.now().strftime('%Y-%m-%d')}.txt"
output_dir = r"D:\Nexensus_Projects\IDBI\annual_filing_xml"
xml_log_file = f"Logs\\xml_extract_logs_{datetime.now().strftime('%Y-%m-%d')}.txt"
os.makedirs(output_dir, exist_ok=True)

def is_xml(data: bytes) -> bool:
    head = data[:200].lstrip()
    if head.startswith(b'\xef\xbb\xbf'):
        head = head[3:]
    head = head.lower()
    return (
        head.startswith(b'<?xml') or
        b'<xbrl' in head or
        b'<xbrli:xbrl' in head
    )

def get_report_type_from_xml_bytes(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
        for elem in root.iter():
            if elem.tag.split('}')[-1] == "NatureOfReportStandaloneConsolidated":
                return (elem.text or "").strip()
    except Exception:
        pass
    return "Unknown"

# def get_financial_year_from_xml_bytes(xml_bytes):
#     try:
#         root = ET.fromstring(xml_bytes)
#         for elem in root.iter():
#             if elem.tag.split('}')[-1] == "DateOfEndOfReportingPeriod":
#                 return (elem.text or "").strip().split("-")[0]
#     except Exception:
#         print("exception in getfinancial year ", e)
#         pass
#     return "Unknown"

import xml.etree.ElementTree as ET

def get_financial_year_from_xml_bytes(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
        years = []

        for elem in root.iter():
            if elem.tag.split('}')[-1] == "DateOfEndOfReportingPeriod":
                value = (elem.text or "").strip()
                
                # Expecting format like 2023-03-31
                if value:
                    year_part = value.split("-")[0]
                    if year_part.isdigit():
                        years.append(int(year_part))

        if years:
            return str(max(years))  # return latest year

    except Exception as e:
        print("Exception in get_financial_year:", e)

    return "Unknown"



for cin in cins[:]:
    print("current cin :", cin)
    time.sleep(0.2)
    for year in years:
        print("current year :", year)
        payload = {
            "cin": cin,
            "year": year
        }

        # response = requests.post(url, json=payload, headers=headers)
        try:
            response = session.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )
        except (requests.exceptions.ConnectionError, socket.gaierror) as e:
            with open(log_file, "a", encoding="utf-8") as log:
                log.write(json.dumps({
                    "cin": cin,
                    "year": year,
                    "error": "DNS / Connection error",
                    "details": str(e)
                }, indent=4))
                log.write("\n")
            continue

        resp_json = response.json()

        # ===== LOG ONLY WHEN THESE CONDITIONS OCCUR =====
        if resp_json.get('status') == 'error' or resp_json.get('file_found') is False:
            with open(log_file, "a", encoding="utf-8") as log:
                # log.write(f"\n{'='*80}\n")
                # log.write(f"CIN: {cin} | YEAR: {year}\n")
                log.write(json.dumps(resp_json, indent=4))
                log.write("\n")
            continue
        # =================================================

        # ---------------- SUCCESS CASE ----------------
        cin_resp = resp_json["cin"]
        year_resp = resp_json["year"]
        download_url = resp_json["download_link"]
        view_url = resp_json["view_link"]
        print("url :", download_url)
        try:
            # -------- Fetch PDF in memory --------
            # pdf_resp = requests.get(view_url, timeout=60)
            # pdf_resp.raise_for_status()
            try:
                pdf_resp = session.get(download_url, timeout=60)
                pdf_resp.raise_for_status()
            except (requests.exceptions.ConnectionError, socket.gaierror) as e:
                with open(log_file, "a", encoding="utf-8") as log:
                    log.write(json.dumps({
                        "cin": cin,
                        "year": year,
                        "error": "PDF download failed (DNS/Network)",
                        "details": str(e)
                    }, indent=4))
                    log.write("\n")
                continue


            # -------- Open PDF from bytes --------
            doc = fitz.open(stream=pdf_resp.content, filetype="pdf")
            if doc.embfile_count() == 0:
                # print("no attachement pdfs", download_url)
                with open(no_attachment_log_file, "a", encoding="utf-8") as log:
                    log.write(json.dumps({
                        "cin": cin,
                        "year": year,
                        "error": "No attachment found in pdf",
                        "download_url": download_url,
                        "view_url" : view_url
                    }, indent=4))
                    log.write("\n")

            for i in range(doc.embfile_count()):
                print("coming here")
                data = doc.embfile_get(i)

                if not is_xml(data):
                    continue

                if get_report_type_from_xml_bytes(data) != "Standalone":
                    continue
                year = get_financial_year_from_xml_bytes(data)

                save_name = f"{cin}_Annual_Filing_{year}.xml"
                save_path = os.path.join(output_dir, save_name)

                with open(save_path, "wb") as f:
                    f.write(data)

                with open(xml_log_file, "a", encoding="utf-8") as log:
                    log.write(f"{cin}_{year}.pdf")
                    log.write("\n")

                print("✅ XML saved:", save_path)
                break

            doc.close()

        except Exception as e:
            print(f"❌ Failed for {cin} {year}: {e}")
            with open(log_file, "a", encoding="utf-8") as log:
                # log.write(f"\n{'='*80}\n")
                # log.write(f"CIN: {cin} | YEAR: {year}\n")
                log.write(json.dumps(resp_json, indent=4))
                log.write("\n")
