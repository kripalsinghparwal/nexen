# import requests
# import base64
# import random
# import string
# from Crypto.Cipher import AES
# from Crypto.Random import get_random_bytes
# import time
# import random
# import json
# from Ngo_details import get_details
# from get_final_payload import prepare_ngo_dict
# from testNgo import get_sys_id

# # def write_to_MargeFile(newline):
# #     file_path = f"D:\\Litigation\\NGO\\trendlyne_data_AM.txt"
# #     with open(file_path, 'a', encoding='utf-8') as text_file:
# #         json_line = json.dumps(newline, ensure_ascii=False)
# #         text_file.write(json_line)
# #         text_file.write(",\n")
# import os
# import pandas as pd


# def append_ngo_to_excel(final_dict, excel_file="ngo_data_AP.xlsx"):
#     """
#     Append NGO data into Excel file.
#     If file does not exist, create new file.
#     """

#     # Convert nested list/dict columns into string
#     row_data = final_dict.copy()

#     for key, value in row_data.items():

#         # Convert list/dict to string
#         if isinstance(value, (list, dict)):
#             row_data[key] = str(value)

#     # Create DataFrame
#     new_df = pd.DataFrame([row_data])

#     # If file exists → append
#     if os.path.exists(excel_file):

#         old_df = pd.read_excel(excel_file)

#         updated_df = pd.concat(
#             [old_df, new_df],
#             ignore_index=True
#         )

#         updated_df.to_excel(excel_file, index=False)

#     else:
#         # Create new file
#         new_df.to_excel(excel_file, index=False)

#     print(f"✅ Data saved to: {excel_file}")



# # 🔑 CONSTANTS
# # SIGN_KEY = "H0k5Lz93a8t16q0gjex5m02ryjf1ToWu"
# # SYS_ID = get_sys_id()#"1780042749838"

# # 🔹 Generate requid
# def generate_requid(n=16):
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# # 🔹 Generate signature
# def get_signature(requid,SYS_ID):
#     SIGN_KEY = "H0k5Lz93a8t16q0gjex5m02ryjf1ToWu"
    
#     plaintext = f"{SYS_ID}###{requid}".encode()
#     key = SIGN_KEY.encode()
#     iv = get_random_bytes(12)

#     cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
#     ciphertext, tag = cipher.encrypt_and_digest(plaintext)

#     final = iv + ciphertext + tag
#     return base64.b64encode(final).decode()



# # # 🔹 URLs
# # urls = [
# #     "https://ngodarpan.gov.in/apis/regis/ngos-summary?stateId=28&captcha=HHaJQ1&capId=90080760a78f45278958e83d124d2129&page=1&size=10",
# #     "https://ngodarpan.gov.in/apis/regis/ngos-summary?stateId=28&captcha=HHaJQ1&capId=90080760a78f45278958e83d124d2129&page=2&size=10",
# #     "https://ngodarpan.gov.in/apis/regis/ngos-summary?stateId=28&captcha=HHaJQ1&capId=90080760a78f45278958e83d124d2129&page=3&size=10",
# # ]

# # for url in urls:
# ls = []
# for i in range(923,2054):
#     # 🔥 CREATE SESSION
#     session = requests.Session()

#     # 🔥 Step 1: Hit homepage (IMPORTANT for cookies)
#     session.get("https://ngodarpan.gov.in", verify=False)
#     i = str(i)
#     url = f"https://ngodarpan.gov.in/apis/regis/ngos-summary?stateId=28&captcha=HHaJQ1&capId=90080760a78f45278958e83d124d2129&page={i}&size=10"
#     # ✅ Generate fresh values EACH request
#     requid = generate_requid()
#     SYS_ID = get_sys_id(session)
#     signature = get_signature(requid,SYS_ID)

#     headers = {
#         "accept": "application/json, text/plain, */*",
#         "channel": "WEB",
#         "requid": requid,
#         "signature": signature,
#         "user-agent": "Mozilla/5.0",
#         "referer": "https://ngodarpan.gov.in/",
#         "origin": "https://ngodarpan.gov.in"
#     }

#     print("Fetching:", url)

#     response = session.get(url, headers=headers, timeout = 600,verify=False)

#     print("Status:", response.status_code)
#     # print(response.text[:200])  # preview
#     res = response.json()
#     ngos = res['ngos']
#     for ngo in ngos:
#         print(ngo)
#         darpan_id = ngo['darpanId']
#         print(darpan_id)
#         details = get_details(darpan_id,SYS_ID,session)
#         finalData = prepare_ngo_dict(ngo,details)
#         append_ngo_to_excel(finalData)

#     time.sleep(random.randint(1,2))


import requests
import base64
import random
import string
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import time
import json
import traceback
import os
import pandas as pd

from Ngo_details import get_details
from get_final_payload import prepare_ngo_dict
from testNgo import get_sys_id


# =====================================================
# RETRY FUNCTION
# =====================================================

def retry(func, *args, retries=5, delay=5, **kwargs):

    last_error = None

    for attempt in range(1, retries + 1):

        try:
            return func(*args, **kwargs)

        except Exception as e:

            last_error = e

            print(
                f"\n❌ {func.__name__} failed "
                f"({attempt}/{retries})"
            )

            print("Error:", str(e))

            if attempt < retries:
                print(f"🔄 Retrying after {delay} sec...")
                time.sleep(delay)

    raise last_error


# =====================================================
# EXCEL SAVE
# =====================================================

def write_data_to_textfile(payload):
    """Append JSON payload to a local text file."""
    try:
        post_data = json.dumps(payload, ensure_ascii=False)

        with open(r'D:\\Litigation\\NGO\\NGOrajasthan11Txt.txt', 'a', encoding='utf-8') as f:
            f.write(post_data)
            f.write(',\n')

    except Exception as e:
        print(f"Exception in write_data_to_textfile: {e}")


def append_ngo_to_excel(
    final_dict,
    excel_file="ngo_data_delhi.xlsx"
):

    try:

        row_data = final_dict.copy()

        for key, value in row_data.items():

            if isinstance(value, (list, dict)):
                row_data[key] = json.dumps(
                    value,
                    ensure_ascii=False
                )

        new_df = pd.DataFrame([row_data])

        if os.path.exists(excel_file):

            old_df = pd.read_excel(excel_file)

            updated_df = pd.concat(
                [old_df, new_df],
                ignore_index=True
            )

            updated_df.to_excel(
                excel_file,
                index=False
            )

        else:

            new_df.to_excel(
                excel_file,
                index=False
            )

        print("✅ Saved")

    except Exception:
        traceback.print_exc()
        raise


# =====================================================
# REQID
# =====================================================

def generate_requid(n=16):

    try:

        return ''.join(
            random.choices(
                string.ascii_letters +
                string.digits,
                k=n
            )
        )

    except Exception:
        traceback.print_exc()
        raise


# =====================================================
# SIGNATURE
# =====================================================

def get_signature(requid, SYS_ID):

    try:

        SIGN_KEY = (
            "H0k5Lz93a8t16q0gjex5m02ryjf1ToWu"
        )

        plaintext = (
            f"{SYS_ID}###{requid}"
        ).encode()

        key = SIGN_KEY.encode()

        iv = get_random_bytes(12)

        cipher = AES.new(
            key,
            AES.MODE_GCM,
            nonce=iv
        )

        ciphertext, tag = (
            cipher.encrypt_and_digest(
                plaintext
            )
        )

        final = iv + ciphertext + tag

        return base64.b64encode(
            final
        ).decode()

    except Exception:
        traceback.print_exc()
        raise


# =====================================================
# MAIN
# =====================================================

TOTAL_PAGES = 3161

page = 1722

while page < TOTAL_PAGES:

    try:

        print(
            f"\n{'='*60}"
        )
        print(
            f"Processing Page: {page}"
        )
        print(
            f"{'='*60}\n"
        )

        session = requests.Session()

        retry(
            session.get,
            "https://ngodarpan.gov.in",
            timeout=60,
            verify=False,
            retries=5
        )

        url = (
            "https://ngodarpan.gov.in/"
            "apis/regis/ngos-summary"
            "?stateId=8"
            "&captcha=HHaJQ1"
            "&capId=90080760a78f45278958e83d124d2129"
            f"&page={page}"
            "&size=10"
        )

        requid = retry(
            generate_requid,
            retries=3
        )

        SYS_ID = retry(
            get_sys_id,
             session,
            retries=5
        )

        signature = retry(
            get_signature,
            requid,
            SYS_ID,
            retries=3
        )

        headers = {
            "accept":
            "application/json, text/plain, */*",

            "channel":
            "WEB",

            "requid":
            requid,

            "signature":
            signature,

            "user-agent":
            "Mozilla/5.0",

            "referer":
            "https://ngodarpan.gov.in/",

            "origin":
            "https://ngodarpan.gov.in"
        }

        response = retry(
            session.get,
            url,
            headers=headers,
            timeout=60,
            verify=False,
            retries=5
        )

        print(
            "Status Code:",
            response.status_code
        )

        res = retry(
            response.json,
            retries=3
        )

        ngos = res.get(
            "ngos",
            []
        )

        print(
            f"NGOs Found: "
            f"{len(ngos)}"
        )

        for ngo in ngos:

            darpan_id = ngo.get(
                "darpanId"
            )

            try:

                print(
                    f"\nFetching NGO:"
                    f" {darpan_id}"
                )

                details = retry(
                    get_details,
                    darpan_id,
                    SYS_ID,
                    session,
                    retries=5,
                    delay=5
                )

                finalData = retry(
                    prepare_ngo_dict,
                    ngo,
                    details,
                    retries=3
                )

                write_data_to_textfile(finalData)

                # retry(
                #     append_ngo_to_excel,
                #     finalData,
                #     retries=5
                # )

                print(
                    f"✅ Done: "
                    f"{darpan_id}"
                )

            except Exception as e:

                print(
                    f"❌ NGO Failed: "
                    f"{darpan_id}"
                )

                print(e)

                with open(
                    "failed_ngos.txt",
                    "a",
                    encoding="utf-8"
                ) as f:

                    f.write(
                        str(darpan_id)
                        + "\n"
                    )

        print(
            f"\n✅ Page "
            f"{page} Completed"
        )

        page += 1

        time.sleep(
            random.randint(1, 2)
        )

    except Exception as e:

        print(
            f"\n🚨 Page "
            f"{page} Failed"
        )

        print(e)

        traceback.print_exc()

        print(
            "Retrying same page "
            "after 10 sec..."
        )

        time.sleep(10)

        # page increment nahi hoga
        # same page fir chalega