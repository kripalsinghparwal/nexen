import requests
import json
import sys, os
from datetime import datetime, date
today = date.today()
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time

start_time = time.time()

cin_cache = {}
cin_lock = Lock()

def cached_postcin(name, port_selector):
    with cin_lock:
        if name in cin_cache:
            return cin_cache[name]
    
    result = port_selector(name)
    
    with cin_lock:
        cin_cache[name] = result
    
    return result


def write_resolve_textfile(data,file):
    try:
        post_data = json.dumps(data)
        #         print(post_data)
        # with open(
        #         "G:\\high_court\\high_court_resolve\\HC_" + file + "_ResolvedFile_{}.txt".format(
        #                 today), 'a') as f:
        with open(
                f"D:\\Nexensus_Projects\\HighCourt\\High_court_data\\Highcourt_resolved\\{rgyear}\\{petres_name}\\" + file.replace(".txt", "") + "_ResolvedFile_{}.txt".format(
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
                    f"D:\\Nexensus_Projects\\HighCourt\\High_court_data\\Highcourt_unresolved\\{rgyear}\\{petres_name}\\" + file.replace(".txt", "") + "_NotResolvedError_{}.txt".format(
                        today), 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))


def postcin_5000(name):
    url = 'http://localhost:5000/api/company-details'
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
        return [response["CIN"]] if "CIN" in response else [None]
    elif isinstance(response, list):
        return [item["CIN"] for item in response if "CIN" in item] or [None]
    return [None]


def resolve_line(data, petitioner_check, respondent_check, petitionerCin__check, respondentCin__check, file):
    try:
        petitioner = data.get("petitionerName", "").lstrip("12345)(").lstrip(".").strip().title()
        respondent = data.get("respondentName", "").lstrip("12345)(").lstrip(".").strip().title()

        # Handle petitioner CIN with cache
        if petitioner == petitioner_check:
            pass
        elif petitioner and any(keyword in petitioner for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
            print("---cached api call 5000 (petitioner)-----")
            petitionerCin = cached_postcin(petitioner, postcin_5000)
            if not petitionerCin or "CIN" not in petitionerCin:
                print("---cached api call 5001 (petitioner)-----")
                petitionerCin = cached_postcin(petitioner, postcin_5001)
            petitionerCin__check = handle_cin_response(petitionerCin)
            petitioner_check = petitioner
        else:
            petitionerCin__check = [None]
            petitioner_check = petitioner

        # Handle respondent CIN with cache
        if respondent == respondent_check:
            pass
        elif respondent and any(keyword in respondent for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
            print("---cached api call 5000 (respondent)-----")
            respondentCin = cached_postcin(respondent, postcin_5000)
            if not respondentCin or "CIN" not in respondentCin:
                print("---cached api call 5001 (respondent)-----")
                respondentCin = cached_postcin(respondent, postcin_5001)
            respondentCin__check = handle_cin_response(respondentCin)
            respondent_check = respondent
        else:
            respondentCin__check = [None]
            respondent_check = respondent

        petitionerCin__check = petitionerCin__check or [None]
        respondentCin__check = respondentCin__check or [None]

        results = []
        if any(cin is not None and cin != 'null' for cin in petitionerCin__check + respondentCin__check):
            for pCin in petitionerCin__check:
                for rCin in respondentCin__check:
                    data_copy = data.copy()
                    data_copy['petitionerCin'] = pCin
                    data_copy['respondentCin'] = rCin
                    results.append(('resolved', data_copy))
        else:
            data['petitionerCin'] = None
            data['respondentCin'] = None
            results.append(('error', data))

        return results
    except Exception as e:
        print(f"Error resolving line: {e}")
        return [('error', data)]



def nclt_cinresolve(file):
    try:
        file_path_full = f"D:\\Nexensus_Projects\\HighCourt\\High_court_data\\Hightcourt_payload\\{rgyear}\\{petres_name}\\{file}"
        with open(file_path_full, 'r') as input_file:
            lines = [line.strip().replace('},', '}') for line in input_file if line.strip()]
        
        tasks = []
        for line in lines:
            try:
                data = json.loads(line)
                tasks.append((data, None, None, [], [], file))
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")

        print("total_tasks", len(tasks))
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_results = executor.map(lambda args: resolve_line(*args), tasks)

        for result_set in future_results:
            for result_type, result_data in result_set:
                if result_type == 'resolved':
                    write_resolve_textfile(result_data, file)
                else:
                    write_erorr_textfile(result_data, file)

    except Exception as e:
        print(f"An error occurred: {e}")


# def nclt_cinresolve(file):
#     try:
#         # Open the input file
#         with open(f"D:\\Nexensus_Projects\\HighCourt\\High_court_data\\Hightcourt_payload\\{rgyear}\\{petres_name}\\{file}", 'r') as input_file:
#             petitioner_check = None
#             respondent_check = None
#             petitionerCin__check = []
#             respondentCin__check = []

#             for line in input_file:
#                 json_data = line.strip().replace('},', '}')
#                 try:
#                     data = json.loads(json_data)
#                 except json.JSONDecodeError as json_error:
#                     print(f"Error parsing JSON: {json_error}")
#                     continue

#                 petitioner = data.get("petitionerName").lstrip("12345)(").lstrip(".").strip().title() if data.get(
#                     "petitionerName") else None
#                 respondent = data.get("respondentName").lstrip("12345)(").lstrip(".").strip().title() if data.get(
#                     "respondentName") else None

#                 # Handle petitioner CIN
#                 if petitioner == petitioner_check:
#                     petitionerCin__check = petitionerCin__check
#                 elif petitioner and any(keyword in petitioner for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
#                     print("---api call 5000-----")
#                     petitionerCin = postcin_5000(petitioner)
#                     if not petitionerCin or "CIN" not in petitionerCin:
#                         print("---api call 5001-----")
#                         petitionerCin = postcin_5001(petitioner)
#                     petitionerCin__check = handle_cin_response(petitionerCin)
#                     petitioner_check = petitioner
#                 else:
#                     petitionerCin__check = [None]
#                     petitioner_check = petitioner

#                 # Handle respondent CIN
#                 if respondent == respondent_check:
#                     respondentCin__check = respondentCin__check
#                 elif respondent and any(keyword in respondent for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
#                     print("---api call 5000-----")
#                     respondentCin = postcin_5000(respondent)
#                     if not respondentCin or "CIN" not in respondentCin:
#                         print("---api call 5001-----")
#                         respondentCin = postcin_5001(respondent)
#                     respondentCin__check = handle_cin_response(respondentCin)
#                     respondent_check = respondent
#                 else:
#                     respondentCin__check = [None]
#                     respondent_check = respondent

#                 # Safely combine petitioner and respondent CIN lists
#                 petitionerCin__check = petitionerCin__check if petitionerCin__check else [None]
#                 respondentCin__check = respondentCin__check if respondentCin__check else [None]

#                 data['petitionerCin'] = petitionerCin__check[0] if petitionerCin__check else None
#                 data['respondentCin'] = respondentCin__check[0] if respondentCin__check else None

#                 # Write the results
#                 if any(cin is not None and cin != 'null' for cin in petitionerCin__check + respondentCin__check):
#                     for petitionerCin in petitionerCin__check:
#                         for respondentCin in respondentCin__check:
#                             data['petitionerCin'] = petitionerCin
#                             data['respondentCin'] = respondentCin
#                             print(data)
#                             write_resolve_textfile(data,file)
#                 else:
#                     print(data)
#                     write_erorr_textfile(data,file)

#     except Exception as e:
#         print(f"An error occurred: {e}")

rgyear = "2025"
petres_name = "LLP"
file_path = r"D:\Nexensus_Projects\HighCourt\High_court_data\Hightcourt_payload\\{}\\{}\\".format(rgyear,petres_name)

dir_list = os.listdir(file_path)
for file in dir_list[2:4]:
    print(file)
    nclt_cinresolve(file)

print("Total time taken: {:.2f} seconds".format(time.time() - start_time))