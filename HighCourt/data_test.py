from bs4 import BeautifulSoup as bs
import requests
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# Template for case data
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

# Request headers
headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "cookie": "PHPSESSID=n8leuvl4jfmhc588ki1dmh063h; JSESSION=82533346; PHPSESSID=n8leuvl4jfmhc588ki1dmh063h",
    "origin": "https://hcservices.ecourts.gov.in",
    "referer": "https://hcservices.ecourts.gov.in/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

inside_url = 'https://hcservices.ecourts.gov.in/hcservices/cases_qry/o_civil_case_history.php'


def convert_date_format(input_date: str) -> Optional[str]:
    """Convert date from 'DD-MM-YYYY' to 'YYYY-MM-DD' format."""
    try:
        date_object = datetime.strptime(input_date, "%d-%m-%Y")
        return date_object.strftime("%Y-%m-%d")
    except ValueError as e:
        print(f"Date conversion error: {e}")
        return None


def get_next_date(date_str: Optional[str]) -> Optional[str]:
    """Extract and convert the next hearing date."""
    if date_str:
        try:
            # Remove ordinal suffixes (rd, th, st, nd) from the date string
            date_str_cleaned = re.sub(r'\b(\d+)(?:rd|th|st|nd)\b', r'\1', date_str).strip()
            # Convert the cleaned date string to a datetime object
            date_object = datetime.strptime(date_str_cleaned, "%d %B %Y")
            # Return the date in the desired format
            return date_object.strftime("%Y-%m-%d")
        except ValueError as e:
            print(f"Next date conversion error: {e}")
    return None


def get_advocate(text: str) -> Optional[str]:
    """Extract advocate names from the text."""
    advocate_pattern = r"Advocate[\s\-:]*([\w\s]+)"
    matches = re.findall(advocate_pattern, text, re.IGNORECASE)
    advocate_names = [re.sub(r"[0-9,]", "", match).strip() for match in matches if match.strip()]
    return advocate_names[0] if advocate_names else None


def get_pet_resp_names(text):
    """Extracts company names containing 'Ltd', 'Limited', 'Private Limited', 'Pvt. Ltd', or 'LLP'."""

    # Split text at digits followed by ')'
    parts = re.split(r'\d+\)', text)

    # Regex pattern to extract valid company names
    pattern = r'([A-Za-z&\s]+(?:\sPVT\.?\s+LTD|\sPRIVATE\sLIMITED|\sLTD|\sLIMITED|\sLLP)\b)'

    company_names = [re.search(pattern, part.strip(), re.IGNORECASE) for part in parts]

    # Extract matched names and filter out None values
    return [match.group(1).strip().title() for match in company_names if match]


def write_to_txt_resolve(case_data: str) -> None:
    """Append case data to a text file."""
    file_path = r'D:\High_court_data\High_Court_Bobay_new_1.txt'
    try:
        with open(file_path, 'a') as text_file:
            text_file.write(case_data + ",\n")
    except IOError as e:
        print(f"File write error: {e}")


def get_json(html_content: str, court_name: str) -> None:
    """Extract case data from HTML content and print it as JSON."""
    try:
        case_data = {}
        soup = bs(html_content, 'html.parser')

        # Extract case link
        link = next((a_tag['href'] for a_tag in soup.find_all('a', href=True) if len(a_tag['href']) > 20), None)
        mainLink = 'https://hcservices.ecourts.gov.in/hcservices/' + link if link else None

        # Extract IA details
        ia_details_header = soup.find('h2', class_='h2class', string='IA Details')
        status_detail = []

        if ia_details_header:
            ia_table = ia_details_header.find_next('table')
            if ia_table:
                for row in ia_table.find_all('tr')[1:]:  # Skip header row
                    columns = row.find_all('td')
                    if len(columns) >= 5:
                        current_detail = {
                            'ia_number': columns[0].get_text(strip=True),
                            'party': columns[1].get_text(strip=True),
                            'ia_status': columns[4].get_text(strip=True)
                        }
                        status_detail.append(current_detail)

        case_data['status_detail'] = status_detail
        # print("case_data['status_detail']: ", case_data['status_detail'])
        # Extract case details
        case_details = soup.find(class_='table case_details_table')
        if case_details:
            data = {}
            for row in case_details.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) == 4:
                    data[cells[0].get_text(strip=True)] = cells[1].get_text(strip=True)
                    data[cells[2].get_text(strip=True)] = cells[3].get_text(strip=True)
                elif len(cells) == 2:
                    data[cells[0].get_text(strip=True)] = cells[1].get_text(strip=True)

        case_data['case_details'] = data
        # print("case_data['case_details'] :", case_data['case_details'])
        # Extract case status
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

        case_data['case_status'] = case_status
        # print("case_data['case_status']: ", case_data['case_status'])
        # Extract petitioner and advocate
        petitioner_advocate_header = soup.find('h2', string='Petitioner and Advocate')
        if petitioner_advocate_header:
            case_data['petitioner_and_advocate'] = petitioner_advocate_header.find_next('span').text.strip().replace(
                '\u00a0', '')
            print("case_data['petitioner_and_advocate']:", case_data['petitioner_and_advocate'])

        # Extract respondent and advocate
        respondent_advocate_header = soup.find('h2', string='Respondent and Advocate')
        if respondent_advocate_header:
            case_data['respondent_and_advocate'] = respondent_advocate_header.find_next('span').text.strip().replace(
                '\u00a0', '')

        # Extract category and subcategory
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

        case_data['category_details'] = category_details
        # print("case_data['category_details']:", case_data['category_details'])
        # Populate case data template
        petitioner_names = get_pet_resp_names(case_data['petitioner_and_advocate'])
        # print("petitioner_names ", petitioner_names)
        if petitioner_names:
            case_data_template['petitionerName'] = petitioner_names[0]
            case_data_template['petitionerAdv'] = get_advocate(case_data['petitioner_and_advocate'])
            case_data_template['respondentName'] = (case_data['respondent_and_advocate'].split('Advocate'))[0].title()
            case_data_template['respondentAdv'] = get_advocate(case_data['respondent_and_advocate'])
            case_data_template['caseDate'] = convert_date_format(
                case_data['case_details'].get('Filing Date', '').strip())
            case_data_template['caseDetails'] = case_data['case_details'].get('Registration Number', '').strip()
            case_data_template['cnrNumber'] = case_data['case_details'].get('CNR Number', '').strip()
            case_data_template['nextHearing'] = get_next_date(
                case_data['case_status'].get('Next Hearing Date', '').strip())
            case_data_template['courtName'] = court_name.title()
            case_data_template['caseStatus'] = case_data['status_detail'][0]['ia_status'].title().strip() if case_data[
                'status_detail'] else None
            case_data_template['caseCategory'] = case_data['category_details'].get('Category', '').title().strip()
            case_data_template['caseSubCategory'] = case_data['category_details'].get('Sub Category',
                                                                                      '').title().strip()
            case_data_template['caseLink'] = mainLink

            print(case_data_template)
            write_to_txt_resolve(json.dumps(case_data_template))

        respondent_names = get_pet_resp_names(case_data['respondent_and_advocate'])
        # print("respondent_names:", respondent_names)
        if respondent_names:
            case_data_template['petitionerName'] = case_data['petitioner_and_advocate'].split('Advocate')[0].replace(
                '1)', '').title().strip()
            case_data_template['petitionerAdv'] = get_advocate(case_data['petitioner_and_advocate'])
            case_data_template['respondentName'] = respondent_names[0]
            case_data_template['respondentAdv'] = get_advocate(case_data['respondent_and_advocate'])
            case_data_template['caseDate'] = convert_date_format(
                case_data['case_details'].get('Filing Date', '').strip())
            case_data_template['caseDetails'] = case_data['case_details'].get('Registration Number', '').strip()
            case_data_template['cnrNumber'] = case_data['case_details'].get('CNR Number', '').strip()
            case_data_template['nextHearing'] = get_next_date(
                case_data['case_status'].get('Next Hearing Date', '').strip())
            case_data_template['courtName'] = court_name.title()
            case_data_template['caseStatus'] = case_data['status_detail'][0]['ia_status'].title().strip() if case_data[
                'status_detail'] else None
            case_data_template['caseCategory'] = case_data['category_details'].get('Category', '').title().strip()
            case_data_template['caseSubCategory'] = case_data['category_details'].get('Sub Category',
                                                                                      '').title().strip()
            case_data_template['caseLink'] = mainLink

            print(case_data_template)
            write_to_txt_resolve(json.dumps(case_data_template))

    except Exception as e:
        print(f"Exception in get_json: {e}")


def get_inside_data(case_no: str, cino: str, court_code: str, court_name: str) -> None:
    """Fetch inside data for a specific case."""
    session = requests.Session()
    data = {
        "court_code": court_code,
        "state_code": 1,
        "court_complex_code": 1,
        "case_no": case_no,
        "cino": cino,
        "appFlag": ""
    }

    try:
        response = session.post(url=inside_url, headers=headers, data=data, timeout=1000)
        if response.status_code == 200:
            html_content = response.text
            get_json(html_content, court_name)
        else:
            print(f"Error: Received status code {response.status_code}")
    except requests.RequestException as e:
        print(f"Request error: {e}")


def read_file_without_bom(file_path: str) -> List[Any]:
    """Read a UTF-8 encoded file, remove BOM if present, and return parsed JSON content."""
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]  # Remove BOM
            decoded_text = content.decode('utf-8')
            cleaned_text = decoded_text.replace('["[', '[').replace(']"]', ']').replace('\\', '').strip()
            parsed_json = json.loads(cleaned_text)
            court_code = parsed_json.get('court_code')[0]
            court_name = parsed_json.get('courtNameArr')[0]
            connections = parsed_json.get('con', [])
            for connection in connections:
                cino = connection['cino']
                case_no = connection['case_no']
                print(cino)
                get_inside_data(case_no, cino, court_code, court_name)
    except (IOError, json.JSONDecodeError) as e:
        print(f"File read error: {e}")


file_path = r'D:\High_court_data\bobay.txt'  # Replace with your file path

read_file_without_bom(file_path)