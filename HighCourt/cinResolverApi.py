import requests
import psycopg2
import re
from urllib.parse import unquote
from flask import Flask, request, jsonify

app = Flask(__name__)

BankList = [{"CIN": "LENDER0000000000000003", "Name": "Allahabad Bank"},
            {"CIN": "LENDER0000000000000057", "Name": "Punjab National Bank"},
            {"CIN": "LENDER0000000000000069", "Name": "State Bank Of India"},
            {"CIN": "LENDER0000000000000228", "Name": "Commerce Bank"},
            {"CIN": "LENDER0000000000000033", "Name": "Indian Overseas Bank"},
            {"CIN": "LENDER0000000000000011", "Name": "Bank Of Baroda"},
            {"CIN": "LENDER000000000000624", "Name": "South Indian Bank"},
            {"CIN": "LENDER0000000000000017", "Name": "Canara Bank"},
            {"CIN": "LENDER0000000000000032", "Name": "Indian Bank"},
            {"CIN": "LENDER0000000000000099", "Name": "Uco Bank"},
            {"CIN": "LENDER0000000000000025", "Name": "Dena Bank"},
            {"CIN": "LENDER000000000000612", "Name": "Saraswat Bank"},
            {"CIN": "LENDER000000000000564", "Name": "Indusind Bank"}
            ]


def clean_company_name(company_name):
    # Add your cleaning logic here
    clean_name = company_name.replace('Private Limited', '').replace('Limited.', '').replace('Pvt Ltd', '').replace(
        'Pvt. Ltd.', '').replace('Ltd', '').replace('Limited', '').replace('Llp', '').replace('Private Li Mited', '')
    return clean_name


# def get_company_details(company_name):
#     actual_name = company_name
#     company_name = remove_company_type(company_name)
#
#     try:
#         # Establish a connection to the database
#         conn = psycopg2.connect(
#             dbname="company_uat",
#             user="postgres",
#             password="postgres",
#             host="localhost",
#             port="5432"
#         )
#
#         # Create a cursor object using the connection
#         cur = conn.cursor()
#
#         # Define the SQL query with a placeholder for the company_name variable
#
#         # [SELECT cd.cin, cd.company_name, cd.company_pan, md.description
#         # FROM company_core.t_company_detail cd
#         # JOIN company_core.t_master_data md ON cd.status_id = md.id
#         # WHERE md.id IN (51, 52, 116, 117, 55, 120)
#         #   AND replace(cd.company_name, '-', ' ') ILIKE %s
#         # ORDER BY COALESCE(cd.modified, cd.created) DESC;]
#
#         sql_query = """
#             SELECT cd.cin, cd.company_name, cd.company_pan, md.description
#             FROM company_core.t_company_detail cd
#             JOIN company_core.t_master_data md ON cd.status_id = md.id
#             WHERE md.id IN (51, 52, 116, 117, 55, 120)
#               AND replace(cd.company_name, '-', ' ') ILIKE %s
#               AND (cd.modified IS NOT NULL OR cd.created IS NOT NULL)
#             ORDER BY GREATEST(
#                 COALESCE(cd.modified, '1970-01-01'),
#                 COALESCE(cd.created, '1970-01-01')
#             ) DESC
#         """
#         # SELECT cd.cin, cd.company_name, cd.company_pan, md.description
#         # FROM company_core.t_company_detail cd
#         # JOIN company_core.t_master_data md ON cd.status_id = md.id
#         # WHERE md.id IN (51, 52, 116, 117, 55, 120) AND replace(cd.company_name, '-', ' ') ILIKE %s;
#
#         # Execute the query with the company_name variable as a parameter
#         cur.execute(sql_query, (company_name + '%',))
#
#         # Fetch the results
#         results = cur.fetchall()
#
#         # Commit the transaction
#         conn.commit()
#
#         # Close the cursor and connection
#         cur.close()
#         conn.close()
#
#         if len(results) > 1:
#             for result in results:
#                 clean_name = clean_company_name(result[1])
#                 if "Llp" in actual_name:
#                     for value in result:
#                         if isinstance(value, str) and len(value) == 8:
#                             return [result]
#                 else:
#                     if clean_name.lower().strip() == company_name.title().lower().strip():
#                         return [result]
#         else:
#             # Return an appropriate value for no results
#             return results if results else None
#
#     except psycopg2.Error as e:
#         print("Error: Unable to fetch data from the database")
#         print(e)
#         return None

# New Development
def get_company_details(company_name):
    actual_name = company_name
    company_name = remove_company_type(company_name)

    try:
        # Establish a connection to the database
        conn = psycopg2.connect(
            dbname="company_uat",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )

        # Create a cursor object using the connection
        cur = conn.cursor()
        results = None
        # Define the SQL queries with placeholders for the company_name variable
        sql_queries_1 = """
                    SELECT cd.cin, cd.company_name, cd.company_pan, md.description
                    FROM company_core.t_company_detail cd
                    JOIN company_core.t_master_data md ON cd.status_id = md.id
                    WHERE md.id IN (51, 52, 116, 117, 55, 120)
                    AND replace(cd.company_name, '-', ' ') ILIKE %s
                    AND (cd.modified IS NOT NULL OR cd.created IS NOT NULL)
                    ORDER BY GREATEST(
                        COALESCE(cd.modified, '1970-01-01'),
                        COALESCE(cd.created, '1970-01-01')
                    ) DESC
                """
        cur.execute(sql_queries_1, (company_name + '%',))
        results = cur.fetchall()
        results = [result for result in results if not (result[0].startswith('FIRM') or result[0].startswith('TRUST') or result[0].startswith('LENDER'))]
        if not results:
            sql_queries_2 = """
                           SELECT cd.cin, cd.company_name, cd.company_pan, md.description
                           FROM company_core.t_company_detail cd
                           JOIN company_core.t_master_data md ON cd.status_id = md.id
                           WHERE md.id IN (51, 52, 116, 117, 55, 120)
                             AND replace(cd.company_name, '-', ' ') ILIKE %s;
                        """
            cur.execute(sql_queries_2, (company_name + '%',))
            results = cur.fetchall()

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cur.close()
        conn.close()
        # Process the results
        if results:
            results = [result for result in results if not (result[0].startswith('FIRM') or result[0].startswith('TRUST') or result[0].startswith('LENDER'))]
            if len(results) > 1:
                for result in results:
                    clean_name = clean_company_name(result[1])
                    if "Llp" in actual_name:
                        for value in result:
                            if isinstance(value, str) and len(value) == 8:
                                return [result]
                    else:
                        if clean_name.lower().strip() == company_name.title().lower().strip():
                            return [result]
            else:
                return results
        else:
            # Return None if both queries return no results
            return None

    except psycopg2.Error as e:
        print("Error: Unable to fetch data from the database")
        print(e)
        return None


def remove_company_type(text):
    # Regular expression pattern to match 'Limited', 'Ltd', or 'Llp' with word boundaries
    pattern = r'\b(?:Private Limited|Pvt Ltd|Llp|Pvt. Ltd.|Pvt. Ltd|Pvt Ltd.|Limited|Ltd)\b'
    # Replace matched patterns with an empty string
    updated_text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return updated_text.strip()


def bankCin(name):
    bankName = name.title()
    BankCin = [{"CIN": bank['CIN'], "CompanyName": bank['Name'], "CompanyPAN": None, "Description": None} for bank in
               BankList if bank['Name'] == bankName]
    return BankCin[0]


def capitalize_second_letter(text):
    pattern = r'\((\w+)\s+(\w+)\)'

    def repl(match_obj):
        first_word = match_obj.group(1)
        second_word = match_obj.group(2)
        if not second_word.isdigit():
            updated_second_word = second_word[0].capitalize() + second_word[1] + second_word[2:]
        else:
            updated_second_word = second_word
        return f"({first_word} {updated_second_word})"

    updated_text = re.sub(pattern, repl, text)
    return updated_text


def company_search(search_keyword):
    result_payload = {"CIN": None, "CompanyName": None, "CompanyPAN": None, "Description": None}
    url = 'https://www.thecompanycheck.com/api/CompanySearch/Search'
    headers = {
        "Origin": "https://www.thecompanycheck.com",
        "Referer": "https://www.thecompanycheck.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }

    # Check if the search keyword contains specific keywords indicating Limited, Ltd, or LLP
    if any(keyword in search_keyword.title() for keyword in ['Limited', 'Ltd', 'Llp']):
        searchkeyword = remove_company_type(search_keyword)
        payload = {"SearchKeyword": searchkeyword}
        try:
            # Send the POST request to the API
            resp = requests.post(url, json=payload, headers=headers)
            # Check if the response is empty
            if not resp.text:
                return "Error: Empty response from the API."
            # Check if the request was successful (status code 200)
            if resp.status_code == 200:
                datas = resp.json()
                # Check if the response contains any data
                if datas:
                    # Extract the required information from the response
                    for data in datas:
                        clean_name = data['CompanyName'].title().replace('Private Limited', '').replace('Limited',
                                                                                                        '').replace(
                            'Pvt Ltd', '').replace(
                            'Pvt. Ltd.', '').replace('Ltd', '')
                        if clean_name.strip() == searchkeyword.title().strip():
                            cin = data['CIN']
                            company_name = data['CompanyName']
                            result_payload['CIN'] = cin
                            result_payload['CompanyName'] = company_name
                            return result_payload
                else:
                    return f"Error: No data found for company: {search_keyword}"
            else:
                return f"Error: Unable to fetch data. Status code: {resp.status_code}"
        except requests.RequestException as e:
            return f"Error: {e}"
    else:
        return f"Error: Company is not Limited, Private Limited, or LLP: {search_keyword}"
    return "No data found for the specified company name"


# ... (same as the given code)

def process_text(company_name):
    processed_text = company_name.title().replace('Pvt. Ltd.', 'Private Limited').replace('Pvt Ltd', 'Private Limited') \
        .replace('Ltd', 'Limited').replace('M/s', '').replace('M/ S', '').replace('M/S', '').replace('(P)', 'Private') \
        .replace('Co.', 'Company').replace('Pvt.Ltd', 'Private Limited').replace('Privatelimited', 'Private Limited') \
        .replace('Pvt .Ltd', 'Pvt. Ltd.').replace('Pvt .ltd', 'Pvt. Ltd.').strip()

    # Regular expression pattern to match text inside parentheses
    pattern = r'\((.*?)\)'

    # Find and replace text inside parentheses with lowercase version
    processed_text = re.sub(pattern, lambda x: '(' + x.group(1).lower() + ')', processed_text)

    # Regular expression pattern to match 'ltd', 'limited', or 'llp' followed by a space or period
    pattern = r'(.*?\b(?:ltd|limited|llp))'

    # Find the first match and extract the text up to the match
    match = re.search(pattern, processed_text, flags=re.IGNORECASE)
    if match:
        processed_text = match.group(1).strip()
        if '(' in processed_text:
            compname = capitalize_second_letter(processed_text)
        else:
            compname = processed_text
        company_details = get_company_details(compname)
        if not company_details:
            company_details = get_company_details(
                compname.replace('And', '&').replace('and', '&').replace('india', '(india)').replace('India',
                                                                                                     '(india)'))
        if company_details:
            payload = {
                'CIN': company_details[0][0],
                'CompanyName': company_details[0][1],
                'CompanyPAN': company_details[0][2],
                'Description': company_details[0][3]
            }
            return payload

        else:
            return company_search(processed_text)
    # print("processed_text_1: ", company_name.title())
    if any(keyword in company_name.title() for keyword in ['Limited', 'Ltd', 'Llp']):
        return company_search(company_name)
    return {"error": "No results found for the given company name."}


# ... (same as the given code)

@app.route('/api/company-details', methods=['POST'])
def company_details():
    try:
        data = request.get_json()
        company_name_param = data.get('company_name', '')
        company_name = unquote(
            company_name_param.replace('&', 'and').replace('-', ' ').replace('.', ' ').replace('  ', ' ').strip())
        filtered_banks = [bank['Name'] for bank in BankList if bank['Name'] == company_name.title()]
        if company_name.title() in filtered_banks:
            return jsonify(bankCin(company_name.title()))
        if "Bank" in company_name and company_name not in filtered_banks:
            company_name = company_name + " Limited"

        processed_text = process_text(company_name)

        if 'error' in processed_text:
            return jsonify({"error": "No results found for the given company name."}), 200

        return jsonify(processed_text)
    except Exception as e:
        return jsonify({"error": "No results found for the given company name."}), 200


if __name__ == '__main__':
    # app.run(host='192.168.1.100', port=5000, debug=True)
    app.run(debug=True)

# pyinstaller --onefile .\cinResolverApi.py