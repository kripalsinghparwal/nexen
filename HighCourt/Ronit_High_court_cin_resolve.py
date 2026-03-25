import requests
import json
import sys, os
from datetime import datetime, date
today = date.today()


def write_resolve_textfile(data,file):
    try:
        post_data = json.dumps(data)
        #         print(post_data)
        # with open(
        #         "G:\\high_court\\high_court_resolve\\HC_" + file + "_ResolvedFile_{}.txt".format(
        #                 today), 'a') as f:
        with open(
                f"D:\\Nexensus_Projects\\HighCourt\\high_court_resolve\\{rgyear}\\{petres_name}\\" + file.replace(".txt", "") + "_ResolvedFile_{}.txt".format(
                        today), 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))


# Step:- Write final payload to text file :-
def write_erorr_textfile(data,file):
    try:
        post_data = json.dumps(data)
        #         print(post_data)
        # with open(
        #         "G:\\high_court\\high_court_error\\HC_" + file + "_NotResolvedError_{}.txt".format(
        #                 today), 'a') as f:
        with open(
                    f"D:\\Nexensus_Projects\\HighCourt\\high_court_error\\{rgyear}\\{petres_name}\\" + file.replace(".txt", "") + "_NotResolvedError_{}.txt".format(
                        today), 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))

def get_cin(company):
    company = company.replace(" ", "%20")
    try:
        response = requests.get(r"http://127.0.0.1:5011/resolve_cin?company_name={}".format(company), timeout=15)
        print("API response :", response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with get cin API: {e}")
        return None

def postcin_5000(name):
    url = 'http://localhost:5005/api/company-details'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url=url, data=json.dumps(data), headers=header)
        resp.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
        print(resp.json())
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with port 5000 API: {e}")
        return None


def postcin_5001(name):
    url = 'http://localhost:5001/api/company-details_new'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url=url, data=json.dumps(data), headers=header)
        resp.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
        print(resp.json())
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with port 5001 API: {e}")
        return None


def handle_cin_response(response):
    if isinstance(response, dict):
        return [response["cin"]] if "cin" in response else [None]
    elif isinstance(response, list):
        return [item["cin"] for item in response if "cin" in item] or [None]
    return [None]


def nclt_cinresolve(file):
    try:
        # Open the input file
        with open(f"D:\\Nexensus_Projects\\HighCourt\\scrape_file\\{rgyear}\\{petres_name}\\{file}", 'r') as input_file:
            petitioner_check = None
            respondent_check = None
            petitionerCin__check = []
            respondentCin__check = []

            for line in input_file:
                json_data = line.strip().replace('},', '}')
                try:
                    data = json.loads(json_data)
                except json.JSONDecodeError as json_error:
                    print(f"Error parsing JSON: {json_error}")
                    continue

                petitioner = data.get("petitionerName").lstrip("12345)(").lstrip(".").strip().title() if data.get(
                    "petitionerName") else None
                respondent = data.get("respondentName").lstrip("12345)(").lstrip(".").strip().title() if data.get(
                    "respondentName") else None

                # Handle petitioner CIN
                if petitioner == petitioner_check:
                    petitionerCin__check = petitionerCin__check
                elif petitioner and any(keyword in petitioner for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                    print("---api call 5000-----")
                    # petitionerCin = postcin_5000(petitioner)
                    petitionerCin = get_cin(petitioner)
                    # if not petitionerCin or "CIN" not in petitionerCin:
                    #     print("---api call 5001-----")
                    #     petitionerCin = postcin_5001(petitioner)
                    petitionerCin__check = handle_cin_response(petitionerCin)
                    petitioner_check = petitioner
                else:
                    petitionerCin__check = [None]
                    petitioner_check = petitioner

                # Handle respondent CIN
                if respondent == respondent_check:
                    respondentCin__check = respondentCin__check
                elif respondent and any(keyword in respondent.lower() for keyword in ["ltd", "limited", "llp", "bank"]):
                    print("---api call 5000-----")
                    # respondentCin = postcin_5000(respondent)
                    respondentCin = get_cin(respondent)
                    # if not respondentCin or "CIN" not in respondentCin:
                    #     print("---api call 5001-----")
                    #     respondentCin = postcin_5001(respondent)
                    respondentCin__check = handle_cin_response(respondentCin)
                    respondent_check = respondent
                else:
                    respondentCin__check = [None]
                    respondent_check = respondent

                # Safely combine petitioner and respondent CIN lists
                petitionerCin__check = petitionerCin__check if petitionerCin__check else [None]
                respondentCin__check = respondentCin__check if respondentCin__check else [None]

                data['petitionerCin'] = petitionerCin__check[0] if petitionerCin__check else None
                data['respondentCin'] = respondentCin__check[0] if respondentCin__check else None

                # Write the results
                if any(cin is not None and cin != 'null' for cin in petitionerCin__check + respondentCin__check):
                    for petitionerCin in petitionerCin__check:
                        for respondentCin in respondentCin__check:
                            data['petitionerCin'] = petitionerCin
                            data['respondentCin'] = respondentCin
                            # print(data)
                            write_resolve_textfile(data,file)
                            if any(cin is None or cin =='null' for cin in [petitionerCin, respondentCin]):
                                # print(data)
                                # print("petitionerName :",data['petitionerName'])
                                # print("respondentName :",data['respondentName'])
                                if any(keyword in data['respondentName'].lower() for keyword in ["ltd", "limited", "llp", "bank"]) and respondentCin is None:
                                    print("data from first if", data)
                                    write_erorr_textfile(data,file)
                                if any(keyword in data['petitionerName'].lower() for keyword in ["ltd", "limited", "llp", "bank"]) and petitionerCin is None:
                                    print("data from second if",data)
                                    write_erorr_textfile(data,file)
                else:
                    # print(data)
                    write_erorr_textfile(data,file)

    except Exception as e:
        print(f"An error occurred: {e}")

rgyear = "2025"
petres_name = "LLP"
print("rgyear", rgyear)
print("petes_name ", petres_name)
file_path = r"D:\\Nexensus_Projects\\HighCourt\scrape_file\\{}\\{}\\".format(rgyear,petres_name)

dir_list = os.listdir(file_path)
for file in dir_list[:2]:
    print(file)
    nclt_cinresolve(file)