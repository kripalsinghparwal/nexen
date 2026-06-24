import requests
import base64
import random
import string
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import time
import random
import json
import urllib3
# from testNgo import get_sys_id

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 🔑 CONSTANTS
SIGN_KEY = "H0k5Lz93a8t16q0gjex5m02ryjf1ToWu"
# SYS_ID = "1780042749838"

# 🔹 Generate requid
def generate_requid(n=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# # 🔹 Generate signature
def get_signature(requid, sys_id, sign_key):
    # SYS_ID = get_sys_id()
    plaintext = f"{sys_id}###{requid}".encode()
    key = sign_key.encode()
    iv = get_random_bytes(12)

    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    final = iv + ciphertext + tag
    return base64.b64encode(final).decode()

# # 🔥 CREATE SESSION
# session = requests.Session()

# # 🔥 Step 1: Hit homepage (IMPORTANT for cookies)
# session.get("https://ngodarpan.gov.in", verify=False)

def get_details(darpanId,SYS_ID,session):
    """
    Fetch NGO details API response
    """
    requid = generate_requid()
    signature = get_signature(requid, SYS_ID, SIGN_KEY)

    headers = {
        "accept": "application/json, text/plain, */*",
        "channel": "WEB",
        "requid": requid,
        "signature": signature,
        "user-agent": "Mozilla/5.0",
        "referer": "https://ngodarpan.gov.in/",
        "origin": "https://ngodarpan.gov.in"
    }
    try:
        url = f"https://ngodarpan.gov.in/apis/regis/summary/ngo-view?darpanId={darpanId}"

        response = session.get(
            url,
            headers=headers,
            verify=False,
            timeout=600
        )

        print(f"Status Code : {response.status_code}")

        if response.status_code == 200:

            data = response.json()

            print("✅ Detail API Success")

            return data

        else:
            print("❌ Failed Response")
            print(response.text)

            return None

    except Exception as e:

        print(f"❌ Error : {e}")

        return None