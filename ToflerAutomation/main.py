PRIVATE_LIMITED_LOOKUP = {
    # ===============================
    # Standard spaced forms
    # ===============================
    "PRIVATE LIMITED": "PRIVATE LIMITED",
    "PRIVATE LTD": "PRIVATE LIMITED",
    "PVT LIMITED": "PRIVATE LIMITED",
    "PVT LTD": "PRIVATE LIMITED",

    # ===============================
    # No-space / joined forms
    # ===============================
    "PRIVATELIMITED": "PRIVATE LIMITED",
    "PRIVATELTD": "PRIVATE LIMITED",
    "PVTLIMITED": "PRIVATE LIMITED",
    "PVTLTD": "PRIVATE LIMITED",

    # ===============================
    # Dot / comma separated
    # ===============================
    "PRIVATE.LIMITED": "PRIVATE LIMITED",
    "PRIVATE,LIMITED": "PRIVATE LIMITED",
    "PRIVATE.LTD": "PRIVATE LIMITED",
    "PRIVATE,LTD": "PRIVATE LIMITED",
    "PVT.LIMITED": "PRIVATE LIMITED",
    "PVT,LIMITED": "PRIVATE LIMITED",
    "PVT.LTD": "PRIVATE LIMITED",
    "PVT,LTD": "PRIVATE LIMITED",

    # ===============================
    # Trailing punctuation
    # ===============================
    "PVT. LTD." : "PRIVATE LIMITED",
    "PVT. LTD" : "PRIVATE LIMITED",
    "PVT LTD." : "PRIVATE LIMITED",
    "PVT.LTD.": "PRIVATE LIMITED",
    "PVT.LTD,": "PRIVATE LIMITED",
    "PVTLTD.": "PRIVATE LIMITED",
    "PVTLTD,": "PRIVATE LIMITED",

    # ===============================
    # Bracketed PRIVATE + LTD (NO space)
    # e.g. Integera Software Services(Pvt)Ltd
    # ===============================
    "(PVT)LTD": "PRIVATE LIMITED",
    "(PVT)LIMITED": "PRIVATE LIMITED",
    "(PRIVATE)LTD": "PRIVATE LIMITED",
    "(PRIVATE)LIMITED": "PRIVATE LIMITED",

    "(PVT).LTD.": "PRIVATE LIMITED",
    "(PVT).LTD": "PRIVATE LIMITED",
    "(PVT)LTD.": "PRIVATE LIMITED",
    "(PVT).LIMITED.": "PRIVATE LIMITED",
    "(PRIVATE).LTD.": "PRIVATE LIMITED",
    "(PRIVATE).LIMITED.": "PRIVATE LIMITED",

    # ===============================
    # Bracketed PRIVATE + LTD (WITH space)
    # ===============================
    "(PVT) LTD": "PRIVATE LIMITED",
    "(PRIVATE) LTD": "PRIVATE LIMITED",

    # ===============================
    # OCR / typo combinations
    # ===============================
    "PRIVATELIMTED": "PRIVATE LIMITED",
    "PRIVTELIMITED": "PRIVATE LIMITED",
    "PVTLIMTED": "PRIVATE LIMITED",
    "PVT LIMTED": "PRIVATE LIMITED",
    "P. LTD." : "PRIVATE LIMITED",
    "P. LTD" : "PRIVATE LIMITED",
    "P LTD." : "PRIVATE LIMITED",
    "P LTD" : "PRIVATE LIMITED"
}



PRIVATE_LOOKUP = {
    # Standard
    "PRIVATE,": "PRIVATE",
    "PRIVATE.": "PRIVATE",
    "PRIVATE": "PRIVATE",
    "PVT," : "PRIVATE",
    "PVT.": "PRIVATE",
    "PVT": "PRIVATE",

    # OCR / typos
    "PRIVTE": "PRIVATE",
    "PRVATE": "PRIVATE",
    "PRITVATE": "PRIVATE",

    # Joined / spacing issues
    "PRIV ATE": "PRIVATE",

    # Brackets / noise
    "(PRIVATE),": "PRIVATE",
    "(PRIVATE).": "PRIVATE",
    "(PRIVATE)": "PRIVATE",
    "(P)," : "PRIVATE",
    "(P)." : "PRIVATE",
    "(P)" : "PRIVATE",
}

LIMITED_LOOKUP = {
    # Standard
    "LIMITED," : "LIMITED",
    "LIMITED." : "LIMITED",
    "LIMITED": "LIMITED",
    "LTD.": "LIMITED",
    "LTD": "LIMITED",

    # OCR / typos
    "LIMTED,": "LIMITED",
    "LIMTED.": "LIMITED",
    "LIMTED": "LIMITED",
    "LIMTD": "LIMITED",
    "LMTD": "LIMITED",
    "L1TD": "LIMITED",
    "LT0": "LIMITED",

    # Joined / spacing issues
    "L T D": "LIMITED",
    "LTD ": "LIMITED",

    # Noise
    "(LTD),": "LIMITED",
    "(LTD).": "LIMITED",
    "(LTD)": "LIMITED",
}

LLP_LOOKUP = {
    # Standard
    "LLP" : "LLP",
    "LIMITED LIABILITY PARTNERSHIP": "LLP",
    "LIMITED LIABILITY PARTNERSHIP.": "LLP",
    "LIMITED LIABILITY PARTNERSHIP FIRM": "LLP",

    # Common abbreviations
    # "L L P": "LLP",
    # "L.L.P.": "LLP",
    # "L.L.P": "LLP",
    "LLP.": "LLP",
    "LLP," : "LLP",


    # Noise / brackets
    "(LLP).": "LLP",
    "(LLP),": "LLP",
    "(LLP)": "LLP",

}

INDIA_LOOKUP = {
    # Standard
    "INDIA": "INDIA",

    # Brackets / noise
    "(INDIA)." : "INDIA",
    "(INDIA)," : "INDIA",
    "(INDIA)": "INDIA",
    "(I)." : "INDIA",
    "(I)," : "INDIA",
    "(I)": "INDIA",
    }



def normalize_company_suffix(name: str) -> str:
    if not name:
        return name

    name_up = " ".join(name.upper().split())

    # Replace PRIVATE LIMITED first
    for key in sorted(PRIVATE_LIMITED_LOOKUP, key=len, reverse=True):
        name_up = name_up.replace(key, PRIVATE_LIMITED_LOOKUP[key])

    # Replace PRIVATE first
    for key in sorted(PRIVATE_LOOKUP, key=len, reverse=True):
        name_up = name_up.replace(key, PRIVATE_LOOKUP[key])

    # Replace LIMITED next
    for key in sorted(LIMITED_LOOKUP, key=len, reverse=True):
        name_up = name_up.replace(key, LIMITED_LOOKUP[key])

    # LLP
    for key in sorted(LLP_LOOKUP, key=len, reverse=True):
        name_up = name_up.replace(key, LLP_LOOKUP[key])

    # LLP
    for key in sorted(INDIA_LOOKUP, key=len, reverse=True):
        name_up = name_up.replace(key, INDIA_LOOKUP[key])

    return name_up


######################### Function wise processing for tofler ####################################################
import os
import time
import random
import pandas as pd
import re
from fuzzywuzzy import fuzz
from curl_cffi import requests
import hashlib


def human_delay(a=2, b=5):
    """Random sleep between a and b seconds."""
    time.sleep(random.uniform(a, b))


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
# input_list = pd.read_excel(r"D:\Nexensus_Projects\ToflerAndZuba\input_folder\Book10.xlsx")['c_name'].drop_duplicates().to_list()[:]
# output_path = 'testRequest.xlsx'
# # === Resume if partial file exists ===
# if os.path.exists(output_path):
#     existing_df = pd.read_excel(output_path)
#     processed_names = set(existing_df['input'])
#     input_list = [name for name in input_list if name not in processed_names]
#     all_data = existing_df.to_dict('records')
#     print(f"🟡 Resuming — already processed {len(processed_names)} companies.")
# else:
#     print("🟢 Starting fresh extraction.")

# === Output File ===
all_data = []
batch_size = 5

# driver = start_driver()
def find_ratio(output_dict):
    input_name = output_dict['input']
    corrected_name = output_dict['corrected_name']
    if isinstance(corrected_name, float) or corrected_name is None:
        # ratio_list.append(0)
        output_dict['ratio'] = 0
        # output_dict = {"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status, "ratio": 0}
    else:
        if fuzz.ratio(input_name.lower().strip(), corrected_name.lower().replace("(old name)", "").strip()) != 100:
            ratio = fuzz.ratio(normalize_company_suffix(input_name).strip(), normalize_company_suffix(corrected_name.replace("(old name)", "").strip()))
            # ratio_list.append(fuzz.ratio(normalize_company_suffix(row.input).strip(), normalize_company_suffix(row.corrected_name.replace("(old name)", "").strip())))
            output_dict['ratio'] = ratio
            # output_dict = {"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status, "ratio": ratio}
        else:
            ratio = fuzz.ratio(input_name.lower().strip(), corrected_name.lower().replace("(old name)", "").strip())
            # ratio_list.append(fuzz.ratio(row.input.lower().strip(), row.corrected_name.lower().replace("(old name)", "").strip()))
            output_dict['ratio'] = ratio
            # output_dict = {"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status, "ratio": ratio}
    return output_dict

def gen_nonce(cname: str) -> str:
    return hashlib.md5(("a" + cname).encode("utf-8")).hexdigest()

def process_company(input_name, all_data):
# for idx, input_name in enumerate(input_list, start=1):
    try:
        # driver = start_driver()
        nonce = gen_nonce(input_name)
    
        url = "https://www.tofler.in/cnamesearch"  # <-- real endpoint

        payload = {
            "cname": input_name,   # space → tata+
            "nonce": nonce
        }

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-requested-with": "XMLHttpRequest",
            "origin": "https://www.tofler.in",
            "referer": "https://www.tofler.in/",
        }

        # cookies = {
        #     "ToflerSession": "ba9450cf69395a5c9ac47593abde13fd",
        #     # add other cookies if present
        # }

        resp = requests.post(
            url,
            impersonate="chrome",
            headers=headers,
            # cookies=cookies,
            data=payload,
        )
        # print(input_name)
        # print(resp.status_code)
        resp_list = resp.json()
        # print()
        time.sleep(0.5)
        # print(resp_list)
        # [{'label': 'COMPUAGE INFOCOM LIMITED', 'status': 'Active', 'value': 'L99999MH1999PLC135914', 'subtype': 'companyinfo', 'url': '/compuage-infocom-limited/company/L99999MH1999PLC135914'}, {'label': 'COMPUAGE INFOCOM LIMITED', 'status': 'Not available for efiling', 'value': 'U30007TN1999PLC042926', 'subtype': 'companyinfo', 'url': '/compuage-infocom-limited/company/U30007TN1999PLC042926'}]
        if resp_list[0]['subtype'].strip() != 'nomatch':
            for elment in resp_list:
                try:
                    corrected_name = elment['label']
                    corrected_name = re.sub(r"\s+", " ", corrected_name).strip()
                except:
                    corrected_name = None
                try:
                    cin = elment['value']
                except:
                    cin = None
                # element_text = elment.text.strip()
                # element_text = re.sub(r"\s+", " ", element_text).strip()
                try:
                    status = elment['status']
                except:
                    status = None
                output_dict = {"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status}
                output_dict = find_ratio(output_dict)
                # if output_dict['ratio'] == 100 and output_dict['status'] == 'Active':
                if output_dict['ratio'] == 100:
                    all_data.append(output_dict)
                    # return output_dict
                    return [output_dict, all_data]
                else:
                    if output_dict not in all_data:
                        all_data.append(output_dict)
            # return all_data
            # return output_dict
            output_dict = {"input": input_name, "corrected_name": None, "cin": None, "status": None, 'ratio': None}
            # return output_dict
            return [output_dict, all_data]
        else:
            print("❌ Failed — retrying with simplified name:", input_name)
            try:
                time.sleep(0.1)

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

                nonce = gen_nonce(simplified)
            
                url = "https://www.tofler.in/cnamesearch"  # <-- real endpoint

                payload = {
                    "cname": simplified,   # space → tata+
                    "nonce": nonce
                }

                headers = {
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-requested-with": "XMLHttpRequest",
                    "origin": "https://www.tofler.in",
                    "referer": "https://www.tofler.in/",
                }

                # cookies = {
                #     "ToflerSession": "ba9450cf69395a5c9ac47593abde13fd",
                #     # add other cookies if present
                # }

                resp = requests.post(
                    url,
                    impersonate="chrome",
                    headers=headers,
                    # cookies=cookies,
                    data=payload,
                )
                # print(input_name)
                # print(resp.status_code)
                resp_list = resp.json()
                # print()
                time.sleep(0.5)
                print(len(resp_list))
                if resp_list[0]['subtype'].strip() != 'nomatch':
                    for elment in resp_list:
                        try:
                            corrected_name = elment['label']
                            corrected_name = re.sub(r"\s+", " ", corrected_name).strip()
                        except:
                            corrected_name = None
                        try:
                            cin = elment['value']
                        except:
                            cin = None
                        # element_text = elment.text.strip()
                        # element_text = re.sub(r"\s+", " ", element_text).strip()
                        try:
                            status = elment['status']
                        except:
                            status = None

                        output_dict = {"input": input_name, "cin": cin, "corrected_name": corrected_name, "status" : status}
                        output_dict = find_ratio(output_dict)
                        # if output_dict['ratio'] == 100 and output_dict['status'] == 'Active':
                        if output_dict['ratio'] == 100:
                            all_data.append(output_dict)
                            # return output_dict
                            return [output_dict, all_data]
                        else:
                            if output_dict not in all_data:
                                all_data.append(output_dict)
                    # return all_data
                    # return output_dict
                    output_dict = {"input": input_name, "corrected_name": None, "cin": None, "status": None, 'ratio': None}
                    # return output_dict
                    return [output_dict, all_data]
                else:
                    output_dict = {"input": input_name, "corrected_name": None, "cin": None, "status": None, 'ratio': None}
                    all_data.append(output_dict)
                    # return output_dict
                    return [output_dict, all_data]
            except Exception as e:
                # print("🚫 Not found:", input_name)
                print("exception 1: ", e)
                output_dict = {"input": input_name, "corrected_name": None, "cin": None, "status": None, 'ratio': None}
                if output_dict not in all_data:
                    all_data.append(output_dict)
                # return all_data
                # return output_dict
                return [output_dict, all_data]
    except Exception as e:
        # print("🚫 Not found:", input_name)
        print("exception 2: ", e)
        output_dict = {"input": input_name, "corrected_name": None, "cin": None, "status": None, 'ratio': None}
        if output_dict not in all_data:
            all_data.append(output_dict)
        # return all_data
        # return output_dict
        return [output_dict, all_data]
