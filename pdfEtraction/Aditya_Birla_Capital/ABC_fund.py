############## Code to split pdf to keep only pages with Rating table in it #####################
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from datetime import datetime

# month_name = datetime.now().strftime("%b")
month_name = "July"

input_pdf_path = "ABSLMF_Empower_July25.pdf"
output_pdf_path = "filtered_{}.pdf".format(input_pdf_path.split(".")[0])

reader = PdfReader(input_pdf_path)
writer = PdfWriter()
fund_list = []

with pdfplumber.open(input_pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        # page_heading = page.extract_text_lines()[0]['text'].strip().replace(" ", "_")
        # tables = page.extract_tables()

        # if not tables:
        #     continue

        # for table in tables:
        #     header = table[0]
        page_lines = [obj['text'] for obj in page.extract_text_lines()]
        if any("Issuer % to Net Assets Rating" in item for item in page_lines) or any("Issuer Rating" in item for item in page_lines):
        # if "Issuer % to Net Assets Rating" in page_lines or "Issuer Rating" in page_lines:
            writer.add_page(reader.pages[page_num])
            continue  # add this page once, then move to next page



# Save the filtered PDF
with open(output_pdf_path, "wb") as f_out:
    writer.write(f_out)

print(f"✅ New PDF created: {output_pdf_path}")


fund_list = ["Large Cap Fund",
"Retirement Fund - The 30s Plan",
"Retirement Fund - The 30s Plan",
"Retirement Fund - The 40s Plan",
"Retirement Fund - The 40s Plan",
"Retirement Fund - The 50s Plan",
"Equity Hybrid '95 Fund",
"Equity Savings Fund",
"Regular Savings Fund",
"Multi Asset Allocation Fund",
"Balanced Advantage Fund",
"Overnight Fund",
"Liquid Fund",
"Liquid Fund",
"Money Manager Fund",
"Money Manager Fund",
"Low Duration Fund",
"Low Duration Fund",
"Savings Fund",
"Savings Fund",
"Floating Rate Fund",
"Floating Rate Fund",
"Floating Rate Fund",
"Corporate Bond Fund",
"Corporate Bond Fund",
"Corporate Bond Fund",
"Short Term Fund",
"Short Term Fund",
"Banking & PSU Debt Fund",
"Banking & PSU Debt Fund",
"Medium Term Plan",
"Medium Term Plan",
"Credit Risk Fund",
"Dynamic Bond Fund",
"Income Fund",
"Government Securities Fund",
"Retirement Fund 'The 50s Plus - Debt Plan'",
"Long Duration Fund",
"NIFTY SDL Plus PSU Bond Sep 2026 60colon40 Index Fund",
"NIFTY SDL Plus PSU Bond Sep 2026 60colon40 Index Fund",
"Nifty SDL Apr 2027 Index Fund",
"Nifty SDL Apr 2027 Index Fund",
"CRISIL IBX 60colon40 SDL + AAA PSU - Apr 2027 Index Fund",
"Nifty SDL Sep 2025 Index Fund",
"CRISIL IBX Gilt - April 2026 Index Fund",
"CRISIL IBX 50colon50 Gilt Plus SDL Apr 2028 Index Fund",
"CRISIL IBX Gilt Apr 2029 Index Fund",
"Nifty SDL Sep 2027 Index Fund",
"CRISIL IBX Gilt Apr 2028 Index Fund",
"CRISIL IBX SDL Jun 2032 Index Fund",
"CRISIL IBX 60colon40 SDL + AAA PSU Apr 2026 Index Fund",
"CRISIL IBX Gilt April 2033 Index Fund",
"CRISIL IBX Gilt June 2027 Index Fund",
"CRISIL-IBX AAA NBFC-HFC Index - Dec 2025 Fund",
"CRISIL-IBX AAA NBFC-HFC Index - Sep 2026 Fund",
"CRISIL-IBX AAA Financial Services Index - Sep 2027 Fund",
"CRISIL-IBX Financial Services 3 to 6 Months Debt Index Fund",
"CRISIL-IBX Financial Services 9-12 Months Debt Index Fund",
"Gold ETF",
"CRISIL Liquid Overnight ETF",
"CRISIL Broad Based Gilt ETF",
"CRISIL 10 Year Gilt ETF"
]

import os
import cv2
import numpy as np
from pdf2image import convert_from_path

# === Input PDF path ===
pdf_path = output_pdf_path
left_folder = r"D:\Nexensus_Projects\pdfEtraction\Aditya_Birla_Capital\left_half_screenshots"
right_folder = r"D:\Nexensus_Projects\pdfEtraction\Aditya_Birla_Capital\right_half_screenshots"

os.makedirs(left_folder, exist_ok=True)
os.makedirs(right_folder, exist_ok=True)

# === Optional: If you have fund names per page ===
# fund_list = ["Fund1", "Fund2", "Fund3"]  # Replace with your actual list

# === Step 1: Convert PDF pages to images ===
images = convert_from_path(pdf_path, dpi=300)  # High DPI = good clarity

# === Step 2: Process each page ===
for idx, pil_image in enumerate(images):
    # Convert PIL to OpenCV (BGR)
    image = np.array(pil_image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Get dimensions
    height, width, _ = image.shape

    # === Split vertically ===
    mid_x = width // 2

    # Left half
    left_half = image[:, :mid_x]

    # Right half
    right_half = image[:, mid_x:]

    # Use fund name if available, else fallback
    fund_name = fund_list[idx] if idx < len(fund_list) else f"page_{idx+1}"
    # fund_name = "ABC"

    # === Save images ===
    left_path = os.path.join(left_folder, f"{fund_name}_page_{idx+1}_left.png")
    right_path = os.path.join(right_folder, f"{fund_name}_page_{idx+1}_right.png")

    cv2.imwrite(left_path, left_half)
    cv2.imwrite(right_path, right_half)

    print(f"✅ Split Page {idx+1}:")
    print(f"   Left  → {left_path}")
    print(f"   Right → {right_path}")

print("\n🎯 All pages processed and saved successfully!")


####################### Working Code to fetch text from screenshot after zooom and save it in excel file with fund distributed as tabs######################
import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
import re

rating_set = set()
# Set Tesseract path (update for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pan = 'AAATB0102C'
mutual_fund = "Aditya Birla Mutual Fund"
# input_dir = "screenshots_cropped_at_rectangles\\{}".format(month_name)
input_dir_list = ["left_half_screenshots", "right_half_screenshots"]
# input_dir = "left_half_screenshots"
# input_dir = "right_half_screenshots"
pattern = re.compile(r"(AAA\(SO\)|AAA\(CE\)|AA\(CE\)|A1\+|AA\+|AA-|AAA|AA|SOVRN SOV|SOVRN|SOV|Sovereign)")
agencies = ["CARE", "IND", "CRISIL", "ICRA", "FITCH", "India Ratings", "Brickwork", "Acuite"]


agency_pattern = re.compile(rf"({'|'.join(agencies)})")


def normalize_rating_text(text):
    replacements = {
        "＋": "+",  # fullwidth plus
        "–": "-",  # en dash
        "−": "-",  # minus
        "﹣": "-",  # small hyphen
        "‒": "-",  # figure dash
        "―": "-",  # horizontal bar
        "（": "(",  # fullwidth left parenthesis
        "）": ")",  # fullwidth right parenthesis
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Remove zero-width and non-breaking spaces
    text = re.sub(r"[\u200B-\u200D\uFEFF\u00A0]", "", text)
    return text

def agency_matching(normalized_text, agency=''):
    agency_match = agency_pattern.search(normalized_text.replace("INDIA", ""))
    if agency_match:
        agency = agency_match.group(1)
        print("agency:", agency)
        normalized_text = normalized_text.replace(agency, " ")
        print("agency_replaced_normalised_text :", normalized_text)
    return [normalized_text, agency]

def rating_matching(normalized_text, rating=''):
    match = pattern.search(normalized_text)
    # print(f"Line: {normalized_text}")
    if match:
        rating = match.group(0)
        print(f"Rating: {rating}\n")
        print("rating_replaced_normalised_text :", normalized_text)
        normalized_text = normalized_text.replace(rating, " ")
    return [normalized_text, rating]

def AUM_matching(normalized_text, total_AUM=''):
    match_AUM = re.findall(r"\d+\.\d+", normalized_text)

    # If found, return the last one (but not if it's at start)
    if match_AUM:
        last = match_AUM[-1]
        # check position of last match
        m = re.finditer(r"\d+\.\d+", normalized_text)
        last_match = list(m)[-1]
        if last_match.start() == 0:
            total_AUM = None  # ignore if at start
        else:
            total_AUM = last
            # total_AUM = match_AUM[-1]
            print(f"Total AUM: {total_AUM}\n")
            print("AUM_replaced_normalised_text :", normalized_text)
            normalized_text = normalized_text.replace(total_AUM, "")
    return [normalized_text, total_AUM]

def MV_matching(normalized_text, market_value=''):
    match_MV = re.findall(r"\d+\.\d+", normalized_text)

    # If found, return the last one (but not if it's at start)
    if match_MV:
        last = match_MV[-1]
        # check position of last match
        m_mv = re.finditer(r"\d+\.\d+", normalized_text)
        last_match_mv = list(m_mv)[-1]
        if last_match_mv.start() == 0:
            market_value = None  # ignore if at start
        else:
            market_value = last
            # total_AUM = match_MV[-1]
            print(f"MV: {market_value}\n")
            print("MV_replaced_normalised_text :", normalized_text)
            normalized_text = normalized_text.replace(market_value, "")
    
    return [normalized_text, market_value]

def end_page(text):
    keywords = [
        "Total Net Assets",
        "Investment Performance",
        "mvestment rperrormance",
        "myvyestment rperrormance",
        "nvestment rerrormance",
        "investment rerrormance"  # seems like a typo version
    ]
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)




import pandas as pd
test_df = pd.DataFrame(columns=['Issuer', "% to Net Assets", "Rating"])
correct_rating_df = pd.DataFrame(columns=['Pan', 'ISIN No.', 'Mutual Fund', 'Fund Name','Fund Type', 'Portfolio', "Agency", 'Ratings', "Category", '(%) Of Total AUM', "Factsheet Date", "URL", 'Filename'])
remaining_rating_df = pd.DataFrame(columns=['Text'])
for input_dir in input_dir_list:
    for filename in os.listdir(input_dir):
        start_printing = False
        print("---------------------------------------------------------->>>>>>>>>>>>>>>>>>>>>>>>--------------------------------------------------------------")
        if filename.endswith(".png"):
            Fund_Type = filename.split("_page")[0].replace("_", " ")
            Fund_Name = "Aditya Birla Sun Life " + Fund_Type
            image_path = os.path.join(input_dir, filename)
            print(image_path)
            image = cv2.imread(image_path)

            # Scale image (e.g., 1.5x zoom)
            # scale_percent = 120  # Adjust this value as needed (e.g., 150 means 150% size)
            scale_percent = 200
            width = int(image.shape[1] * scale_percent / 100)
            height = int(image.shape[0] * scale_percent / 100)
            dim = (width, height)

            # Resize image
            image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Threshold to isolate dark lines (black separators)
            # _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

            # Adaptive threshold to handle gray lines and varying lighting
            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV,
                blockSize=15,
                C=10
            )

            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
            detected_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

            # Find contours of the lines
            contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Get y-coordinates of all horizontal lines
            line_y_coords = sorted([cv2.boundingRect(cnt)[1] for cnt in contours])

            # Add image boundaries
            line_y_coords = [0] + line_y_coords + [image.shape[0]]

            # Process and print each row
            # print("\nExtracted Table Rows:")
            for i in range(len(line_y_coords) - 1):
                y_start = line_y_coords[i]
                y_end = line_y_coords[i + 1]
                
                # Skip very small regions (likely just the line itself)
                if y_end - y_start < 10:
                    continue

                # Extract the row region
                row_img = image[y_start:y_end, :]

                # OPTIONAL: Resize the row to improve OCR accuracy
                zoom_factor = 2.0
                row_img = cv2.resize(row_img, None, fx=zoom_factor, fy=zoom_factor, interpolation=cv2.INTER_LINEAR)

                # Convert to PIL Image for Tesseract
                row_pil = Image.fromarray(cv2.cvtColor(row_img, cv2.COLOR_BGR2RGB))

                # Tesseract OCR
                custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
                text = pytesseract.image_to_string(row_pil, config=custom_config).strip()
                text = text.replace("Al1", "A1")
                normalized_text = normalize_rating_text(text)
                agency = ""
                rating = ""
                portfolio = ""
                agency_2 = ''
                rating_2 = ''
                portfolio_2 = ''
                total_AUM = ''

                if text:
                    if "issuer" in text.lower() and "ratin" in text.lower():
                        # print("Issuer text :::::::::", text)
                        start_printing = True
                        continue
                    if start_printing:
                        if "@absi" in text.lower() or "https://mutualfund.adityabirlacapital.com" in text.lower():
                            continue
                        # if text == "a |" or text == "PT" or text == "PN":
                        #     break
                        if len(text.split("\n")[0].strip()) < 6 or end_page(text) == True:
                            break
                        cleaned_text = re.sub(r'^[^A-Za-z0-9]+', '', text).replace(";", ' ').replace("~", "")
                        patterns = [
                            r'}}©—',      # first one
                            r'}Â»&Â©',       # second one
                            r'# }»&©',   # with leading '#'
                        ]
                        
                        for p in patterns:
                            cleaned_text = re.sub(p, '', cleaned_text)
                        cleaned_text = re.sub(r'[^A-Za-z0-9+%]+$', '', cleaned_text).strip()
                        cleaned_text = re.sub(r'(—_—sav@it|.istYL|. isWxSL|—s|~\-s)$', '', cleaned_text).rstrip()
                        # print(cleaned_text)
                        # print(len(re.split(r'\s{2,}', cleaned_text)),"[][]", re.split(r'\s{2,}', cleaned_text)[-1])
                        if "an" == re.split(r'\s{2,}', cleaned_text)[-1]:
                            continue
                        if len(re.split(r'\s{2,}', cleaned_text)) == 3:
                            # print(len(re.split(r'\s{2,}', cleaned_text)),"[][]", re.split(r'\s{2,}', cleaned_text)[-1])
                            print(len(re.split(r'\s{2,}', cleaned_text)), "[][]", re.split(r'\s{2,}', cleaned_text))
                            cleaned_text = re.split(r'\s{2,}', cleaned_text)
                            if cleaned_text[1].startswith("Debt"):
                                temp_df = pd.DataFrame([{
                                                        "Issuer" : cleaned_text[1],
                                                        "% to Net Assets" : cleaned_text[2],
                                                        "Agency" : None,
                                                        "Rating" : None,
                                                        "Fund Name" : Fund_Name,
                                                        "Fund Type" : Fund_Type
                                                    }])
                            else:
                                rating_and_agency = cleaned_text[2]
                                agency_matching_output = agency_matching(rating_and_agency)
                                remaining_text = agency_matching_output[0].strip()
                                agency = agency_matching_output[1].strip()
                                print("agency :", agency)


                                # rating_matching_output = rating_matching(remaining_text)
                                # remaining_text = rating_matching_output[0].strip()
                                # rating = rating_matching_output[1].strip()
                                rating = remaining_text
                                print("rating :", rating)
                                temp_df = pd.DataFrame([{
                                                "Issuer" : cleaned_text[0],
                                                "% to Net Assets" : cleaned_text[1],
                                                "Agency" : agency,
                                                "Rating" : rating,
                                                "Fund Name" : Fund_Name,
                                                "Fund Type" : Fund_Type
                                            }])
                        elif len(re.split(r'\s{2,}', cleaned_text)) == 2:
                            print(len(re.split(r'\s{2,}', cleaned_text)), "[][]", re.split(r'\s{2,}', cleaned_text))
                            cleaned_text = re.split(r'\s{2,}', cleaned_text)
                            if cleaned_text[1].startswith("Debt"):
                                temp_df = pd.DataFrame([{
                                                        "Issuer" : cleaned_text[1],
                                                        "% to Net Assets" : None,
                                                        "Agency" : None,
                                                        "Rating" : None,
                                                        "Fund Name" : Fund_Name,
                                                        "Fund Type" : Fund_Type
                                                    }])
                            else:
                                temp_df = pd.DataFrame([{
                                                        "Issuer" : cleaned_text[0],
                                                        "% to Net Assets" : cleaned_text[1],
                                                        "Agency" : None,
                                                        "Rating" : None,
                                                        "Fund Name" : Fund_Name,
                                                        "Fund Type" : Fund_Type
                                                    }])
                        elif len(re.split(r'\s{2,}', cleaned_text)) == 4:
                            print(len(re.split(r'\s{2,}', cleaned_text)), "[][]", re.split(r'\s{2,}', cleaned_text))
                            cleaned_text = [x for x in re.split(r'\s{2,}', cleaned_text) if x != ":"]
                            if cleaned_text[1].startswith("Debt"):
                                rating_and_agency = cleaned_text[3]
                                agency_matching_output = agency_matching(rating_and_agency)
                                remaining_text = agency_matching_output[0].strip()
                                agency = agency_matching_output[1].strip()
                                print("agency :", agency)


                                # rating_matching_output = rating_matching(remaining_text)
                                # remaining_text = rating_matching_output[0].strip()
                                # rating = rating_matching_output[1].strip()
                                rating = remaining_text
                                print("rating :", rating)
                                temp_df = pd.DataFrame([{
                                                        "Issuer" : cleaned_text[1],
                                                        "% to Net Assets" : cleaned_text[2],
                                                        "Agency" : agency,
                                                        "Rating" : rating,
                                                        "Fund Name" : Fund_Name,
                                                        "Fund Type" : Fund_Type
                                                    }])
                            else:
                                rating_and_agency = cleaned_text[2]
                                agency_matching_output = agency_matching(rating_and_agency)
                                remaining_text = agency_matching_output[0].strip()
                                agency = agency_matching_output[1].strip()
                                print("agency :", agency)


                                # rating_matching_output = rating_matching(remaining_text)
                                # remaining_text = rating_matching_output[0].strip()
                                # rating = rating_matching_output[1].strip()
                                rating = remaining_text
                                print("rating :", rating)
                                temp_df = pd.DataFrame([{
                                                        "Issuer" : cleaned_text[0],
                                                        "% to Net Assets" : cleaned_text[1],
                                                        "Agency" : agency,
                                                        "Rating" : rating,
                                                        "Fund Name" : Fund_Name,
                                                        "Fund Type" : Fund_Type
                                                    }])
                        else:
                            print("else block")
                            print(len(re.split(r'\s{2,}', cleaned_text)), "[][]", re.split(r'\s{2,}', cleaned_text))
                            temp_df = pd.DataFrame([{
                                                    "Issuer" : re.split(r'\s{2,}', cleaned_text)[0],
                                                    "% to Net Assets" : None,
                                                    "Agency" : None,
                                                    "Rating" : None,
                                                    "Fund Name" : Fund_Name,
                                                    "Fund Type" : Fund_Type
                                                }])

                        test_df = pd.concat([test_df, temp_df])
                        # if "Total Net Assets".lower() in text.lower() or "Investment Performance".lower() in text.lower() or "investment rerrormance" in text.lower():
                        # if end_page(text) == True:
                        #     break




