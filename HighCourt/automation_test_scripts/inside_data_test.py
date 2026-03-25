from bs4 import BeautifulSoup as bs
import requests
import json
import re
from datetime import datetime
from typing import Any, Dict, List
import time
import os
from bs4 import NavigableString

session = requests.Session()

case_data_template = {
    "petitionerCin": None,
    "respondentCin": None,
    "petitionerName": None,
    "respondentName": None,
    "caseDate": None,
    "nextHearing": None,
    "caseDetails": None,
    "courtName": None,
    "petitionerAdv": None,
    "respondentAdv": None,
    "caseStatus": None,
    "caseCategory": None,
    "caseSubCategory": None,
    "casePaperType": None,
    "cnrNumber": None,
    "courtEstablishment": None,
    "caseLink": None
}

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "cookie": "PHPSESSID=n8leuvl4jfmhc588ki1dmh063h; JSESSION=82533346; PHPSESSID=n8leuvl4jfmhc588ki1dmh063h",
    "origin": "https://hcservices.ecourts.gov.in",
    "referer": "https://hcservices.ecourts.gov.in/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    'Connection': 'keep-alive',
}
inside_url = r'https://hcservices.ecourts.gov.in/hcservices/cases_qry/o_civil_case_history.php'


def convert_date_format(input_date):
    # Convert the string to a datetime object
    print("input_date :", input_date)
    date_object = datetime.strptime(input_date, "%d-%m-%Y")
    # Format the datetime object to 'YYYY-MM-DD'
    return date_object.strftime("%Y-%m-%d")


def getNextDate(date_str):
    if date_str:
        print("NexDate: ", date_str)
        if ":-" != date_str.strip():
            # Remove the ordinal suffix (e.g., "rd", "th") from the day
            # date_str_cleaned = date_str.replace("rd", "").replace("th", "").replace("st", "").replace("nd", "").strip()ZZ
            date_str_cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str).strip()

            # Parse the cleaned date string into a datetime object
            date_object = datetime.strptime(date_str_cleaned, "%d %B %Y")

            # Format the datetime object into the desired format
            formatted_date = date_object.strftime("%Y-%m-%d")

            # Print the result
            return formatted_date
        return None
    return None


def extract_parties_and_unique_advocates_from_element(span_tag):
    # Replace <br> tags with line breaks for consistent splitting
    # Replace <br> and <br/> with newline
    # print("span_tag_input", span_tag)
    for br in span_tag.find_all('br'):
        br.replace_with(NavigableString('\n'))

    # Replace </br> if it's present as text
    # print("span_tag1", span_tag)
    for text in span_tag.find_all(string=True):
        if '</br>' in text:
            new_text = text.replace('</br>', '\n')
            text.replace_with(NavigableString(new_text))

    # Extract cleaned text
    # print('span_tag2', span_tag)
    text = span_tag.get_text(separator='\n')
    # print('text', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    parties = []
    all_advocates = []

    for line in lines:
        # print("line", line)
        if re.match(r'^\d+\)', line) or re.match(r'^\d+\)\s+', line):
            # Line starts with "1)" or similar => it's a party
            party_name = re.sub(r'^\d+\)\s*', '', line)
            parties.append(party_name)
        elif line.lower().startswith('advocate-'):
            # Advocate header line
            advs = re.sub(r'(?i)^advocate[-:\s]*', '', line)
            all_advocates += [a.strip() for a in advs.split(',') if a.strip()]
        else:
            # Likely additional advocate names
            all_advocates.append(line)

    # Deduplicate while preserving order
    seen = set()
    unique_advocates = []
    for name in all_advocates:
        clean_name = name.strip()
        if clean_name and clean_name not in seen:
            seen.add(clean_name)
            unique_advocates.append(clean_name)

    return parties, ', '.join(unique_advocates)


def write_to_txt_resolve(caseData, stateName, stateCode, petres_name, rgyear):
    file1 = r'D:\Nexensus_Projects\HighCourt\High_court_data\Hightcourt_payload\{}\{}\{}.txt'.format(rgyear, petres_name, stateName)
    text_file = open(file1, 'a')
    text_file.write(caseData)
    text_file.write(",")
    text_file.write("\n")
    text_file.close()


def getjson(html_content, courtName, stateName, stateCode, petres_name, rgyear):
    try:
        """Extracts case data from the provided HTML content and prints it as JSON."""
        # Initialize a dictionary to store the extracted data
        case_data = {}

        # Parse the HTML content
        soup = bs(html_content, 'html.parser')
        html_content_for_petitioner_and_repondent = html_content.replace("<br>", '\n').replace("</br>", '\n').replace("<br/>", '\n').replace("<br />", '\n')
        soup_for_petitioner_and_repondent = bs(html_content_for_petitioner_and_repondent, 'html.parser')
        # print(soup)
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            if len(link) > 20:
                case_data['link'] = 'https://hcservices.ecourts.gov.in/hcservices/'+link
            else:
                case_data['link'] = None
        # Extract IA details
        ia_details_header = soup.find('h2', class_='h2class', string='IA Details')
        status_detail = []  # Initialize as a list to store multiple entries

        if ia_details_header:
            # Extract the IA details table
            ia_table = ia_details_header.find_next('table')
            if ia_table:
                rows = ia_table.find_all('tr')
                for row in rows[1:]:  # Skip the header row
                    columns = row.find_all('td')
                    if len(columns) >= 5:  # Ensure there are enough columns
                        ia_number = columns[0].get_text(strip=True)
                        party = columns[1].get_text(strip=True)
                        ia_status = columns[4].get_text(strip=True)

                        # Create a dictionary for the current row
                        current_detail = {
                            'ia_number': ia_number,
                            'party': party,
                            'ia_status': ia_status
                        }

                        # Instead of appending, directly assign to the list using the index
                        status_detail.append(current_detail)  # This line can remain as is

        case_data['status_detail'] = status_detail  # Corrected key name

        # Extract Case Details
        case_details = soup.find(class_='table case_details_table')
        if case_details:
            rows = case_details.find_all('tr')
            data = {}

            # Loop through rows and extract key-value pairs
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 4:  # Two key-value pairs in this row
                    key1 = cells[0].get_text(strip=True)
                    value1 = cells[1].get_text(strip=True)
                    key2 = cells[2].get_text(strip=True)
                    value2 = cells[3].get_text(strip=True)
                    data[key1] = value1
                    data[key2] = value2
                elif len(cells) == 2:  # Single key-value pair in this row
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    data[key] = value

            case_data['case_details'] = data  # Corrected key name

        # Extract Case Status
        case_status = {}
        case_status_header = soup.find('h2', string='Case Status')
        if case_status_header:
            status_table = case_status_header.find_next('table')
            if status_table:
                for row in status_table.find_all('tr'):
                    key = row.find('td').text.strip().replace('\u00a0', '')
                    value = row.find_all('td')[1].text.strip().replace('\u00a0', '') if len(
                        row.find_all('td')) > 1 else None
                    case_status[key] = value

        case_data['case_status'] = case_status  # Corrected key name
        # print("case_data :", case_data)
        try:
            # Extract Petitioner and Advocate
            petitioner_advocate_header = soup.find('h2', string='Petitioner and Advocate')
            if petitioner_advocate_header:
                # petitioner_names, pet_adv = extract_parties_and_unique_advocates_from_element(petitioner_advocate_header.find_next('span'))
                petitioner_names, pet_adv = extract_parties_and_unique_advocates_from_element(soup_for_petitioner_and_repondent.find('span', class_='Petitioner_Advocate_table'))
                petitioner_advocate = petitioner_advocate_header.find_next('span').text.strip().replace('\u00a0', '')
                case_data['petitioner_and_advocate'] = petitioner_advocate  # Corrected key name

            # Extract Respondent and Advocate
            respondent_advocate_header = soup.find('h2', string='Respondent and Advocate')
            if respondent_advocate_header:
                # respondent_names, resp_adv = extract_parties_and_unique_advocates_from_element(respondent_advocate_header.find_next('span'))
                respondent_names, resp_adv = extract_parties_and_unique_advocates_from_element(soup_for_petitioner_and_repondent.find('span', class_='Respondent_Advocate_table'))
                respondent_advocate = respondent_advocate_header.find_next('span').text.strip().replace('\u00a0', '')
                case_data['respondent_and_advocate'] = respondent_advocate  # Corrected key name

            # Extract Category and Subcategory
            category_details = {}
            category_header = soup.find('h2', string='Category Details')
            if category_header:
                category_table = category_header.find_next('table')
                if category_table:
                    for row in category_table.find_all('tr'):
                        header = row.find('td').text.strip().replace('\u00a0', '')
                        value = row.find_all('td')[1].text.strip().replace('\u00a0', '')
                        if len(row.find_all('td')) > 1:
                            category_details[header] = value

            case_data['category_details'] = category_details  # Corrected key name
            # print(json.dumps(case_data, indent=4))

            print("petitioner_names     :", petitioner_names)
            print("respondent_names     :", respondent_names)
            print("petitioner_advocates :", pet_adv)
            print("respondent_advocates :", resp_adv)

            # Generate all petitioner/respondent combinations
            for petitioner_name in petitioner_names:
                for respondent_name in respondent_names:
                    try:
                        case_data_template['petitionerName'] = petitioner_name.title().strip()
                        case_data_template['petitionerAdv'] = pet_adv
                        case_data_template['respondentName'] = respondent_name.title().strip()
                        case_data_template['respondentAdv'] = resp_adv
                        case_data_template['caseDate'] = convert_date_format(case_data['case_details']['Filing Date'].strip())
                        case_data_template['caseDetails'] = case_data['case_details']['Registration Number'].strip()
                        case_data_template['cnrNumber'] = case_data['case_details']['CNR Number'].strip()

                        # Handle next hearing date if available
                        if 'Next Hearing Date' in case_data.get('case_status', {}):
                            date_str = case_data['case_status']['Next Hearing Date'].strip()
                            case_data_template['nextHearing'] = getNextDate(date_str)
                        else:
                            case_data_template['nextHearing'] = None

                        case_data_template['courtName'] = courtName.title()

                        # Case status
                        if case_data.get('status_detail'):
                            case_data_template['caseStatus'] = case_data['status_detail'][0].get('ia_status', '').title().strip()
                        else:
                            case_data_template['caseStatus'] = None

                        # Categories
                        try:
                            case_data_template['caseCategory'] = case_data['category_details'].get('Category', '').title().strip()
                        except Exception as e:
                            case_data_template['caseCategory'] = None
                            print('Exception in Case Category:', e)

                        try:
                            case_data_template['caseSubCategory'] = case_data['category_details'].get('Sub Category', '').title().strip()
                        except Exception as e:
                            case_data_template['caseSubCategory'] = None
                            print('Exception in Case Sub Category:', e)

                        case_data_template['caseLink'] = case_data['link']

                        # Output or save the data
                        print(case_data_template)
                        write_to_txt_resolve(json.dumps(case_data_template), stateName, stateCode, petres_name, rgyear)
                        print("data stored in text file")
                    except Exception as e:
                        print("Exception while processing a petitioner/respondent pair:", e)
        except Exception as e:
            print("Exception as :", e)
    except Exception as e:
        print("Exception :", e)


def get_inside_data(case_no, cino, court_code, courtName, stateName, stateCode, petres_name, rgyear, seen_data_set):
    global session  # Access and modify the global session

    data = {
        "court_code": f'{court_code}',
        "state_code": stateCode,
        "court_complex_code": 1,
        "case_no": f'{case_no}',
        "cino": f"{cino}",
        "appFlag": ""
    }

    print("data", data)

    data_key = json.dumps(data, sort_keys=True)
    if data_key in seen_data_set:
        print("Duplicate data found. Skipping POST request:", data)
        return
    else:
        seen_data_set.add(data_key)

    print("Posting data:", data)

    try:
        response = session.post(url=inside_url, headers=headers, data=data, timeout=10)
        response.encoding = response.apparent_encoding

        if response.status_code == 200:
            html_content = response.text
            getjson(html_content, courtName, stateName, stateCode, petres_name, rgyear)
        else:
            print(f"Error: Received status code {response.status_code}")

    # except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
    except Exception as e:
        print(f"[ERROR] Exception during POST: {e}")
        print("Resetting session and retrying...")

        # Re-initialize the global session
        session = requests.Session()

        try:
            response = session.post(url=inside_url, headers=headers, data=data, timeout=10)
            response.encoding = response.apparent_encoding

            if response.status_code == 200:
                html_content = response.text
                getjson(html_content, courtName, stateName, stateCode, petres_name, rgyear)
            else:
                print(f"[RETRY] Error: Received status code {response.status_code}")
        except Exception as e:
            print(f"[RETRY ERROR] Failed again after resetting session: {e}")


def read_file_without_bom(file_path: str, stateName, stateCode, petres_name, rgyear) -> List[Any]:
    """Reads a UTF-8 encoded file, removes BOM if present, and returns the parsed JSON content."""
    seen_data_set = set()
    try:
        with open(file_path, 'rb') as file:  # Open in binary mode to read BOM
            content = file.read()

            # Check for BOM and remove it if present
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]  # Remove BOM (3 bytes)

            # Decode the content to a string
            decoded_text = content.decode('utf-8')

            # Clean up the string for JSON parsing
            cleaned_text = decoded_text.replace('["[', '[').replace(']"]', ']').replace('\\', '').strip()

            # Parse the cleaned JSON string
            cleaned_text = cleaned_text.rsplit(",", 1)[0]
            parsed_json = json.loads(cleaned_text)

            # Extract the 'con' key from the parsed JSON
            court_code = parsed_json.get('court_code')[0]
            courtName = parsed_json.get('courtNameArr')[0]
            connections = parsed_json.get('con', [])
            for connection in connections:
                cino = connection['cino']
                case_no = connection['case_no']
                get_inside_data(case_no, cino, court_code, courtName, stateName, stateCode, petres_name, rgyear, seen_data_set)
                print("---------------------------------------------------------")
    except Exception as e:
        print("Exception in reading raw file try second method", e)
        # Step 1: Read the raw text (if from file)
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            raw_text = f.read()
        # Step 2: Load the outer JSON
        try:
            outer_data = json.loads(raw_text)
        except Exception as e:
            print("Exception occured again reading file retryin third method", e)
            outer_data = json.loads(raw_text.rsplit(",", 1)[0])

        # Step 3: Extract court info
        court_code = outer_data.get('court_code', [None])[0]
        courtName = outer_data.get('courtNameArr', [None])[0]

        # Step 3: Extract and parse the stringified JSON list inside 'con'
        # `con` is a list with one string element that contains the actual list
        inner_list_str = outer_data['con'][0]
        inner_list = json.loads(inner_list_str)

        # Step 4: Extract 'cino' and 'case_no'
        for item in inner_list:
            case_no = item['case_no']
            cino = item['cino']
            # print(f"CINO: {item['cino']}, CASE NO: {item['case_no']}")
            get_inside_data(case_no, cino, court_code, courtName, stateName, stateCode, petres_name, rgyear, seen_data_set)
            print("---------------------------------------------------------")

    # return connections
# with open(r'D:\Nexensus_Projects\HighCourt\mapped_court_benches.json', 'r', encoding='utf-8') as file:
#     courts_data = json.load(file)


# for petres_name in ["Bank", "Limited", "LLP", 'LTD'][3:4]:
#     print("current petres :", petres_name)

def cases_details_collection(courts_data, rgyear, petres_name):
    for court in courts_data[:]:
        stateCode = court['stateCode']
        stateName = court['stateName'].strip().replace(" ", "_")
        benchesNumber = len(court['benches'])
        benches = court['benches']

        print("running one :", rgyear, petres_name, stateCode, stateName, benchesNumber, benches)

        for i in range(1, benchesNumber + 1):
            bench = i
            file_path = r'D:\Nexensus_Projects\HighCourt\High_court_data\Highcourt_raw\{}\{}\{}_Bench_{}.txt'.format(rgyear, petres_name, stateName, bench)
            print("current_file :", file_path)
            # ✅ Check if file exists before reading
            if os.path.isfile(file_path):
                file_content = read_file_without_bom(file_path, stateName, stateCode, petres_name, rgyear)
            else:
                print(f"File not found: {file_path}")

        


