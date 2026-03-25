############## Code to split pdf to keep only pages with Rating table in it #####################
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from datetime import datetime

# month_name = datetime.now().strftime("%b")
month_name = "July"

input_pdf_path = "Edelweiss_MF_Factsheet_July_2025_revised_11072025_120123_PM.pdf"
output_pdf_path = "filtered_{}.pdf".format(input_pdf_path.split(".")[0])

reader = PdfReader(input_pdf_path)
writer = PdfWriter()
fund_list = []

with pdfplumber.open(input_pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        page_heading = page.extract_text_lines()[0]['text'].strip().replace(" ", "_")
        tables = page.extract_tables()

        if not tables:
            continue

        for table in tables:
            header = table[0]
            if any("Composition by Ratings" in h for h in header if h):
                break  # skip this page
            elif any("Rating" in h for h in header if h) and any("Instrument" in h for h in header if h):
                fund_list.append(page_heading)
                writer.add_page(reader.pages[page_num])
                break  # add this page once, then move to next page

# Save the filtered PDF
with open(output_pdf_path, "wb") as f_out:
    writer.write(f_out)

print(f"✅ New PDF created: {output_pdf_path}")

############ Code to save screenshot of heading of every page that contains rating table ################
import os
from pdf2image import convert_from_path
import cv2
import numpy as np

# === Configuration ===
pdf_path = output_pdf_path  # Replace with your actual PDF file path
output_dir = "heading_screenshots_Edelweiss\\{}".format(month_name)
# top_strip_dir = "top_strip_screenshots_bandhan"  # <== NEW FOLDER
os.makedirs(output_dir, exist_ok=True)
# os.makedirs(top_strip_dir, exist_ok=True)

# === Step 1: Convert PDF pages to images ===
images = convert_from_path(pdf_path, dpi=300)  # Use high DPI for better clarity

# === Step 2: Crop right half and save ===
for idx, pil_image in enumerate(images):
    # Convert PIL to OpenCV (BGR)
    image = np.array(pil_image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Get dimensions
    height, width, _ = image.shape


    # Crop left half (0% to 50%)
    x_start = 0
    x_end = int(0.255 * width)  # left half
    y_start = 0  # 8% from top (same as before)
    y_end = int(0.11 * height)
    left_half = image[y_start:y_end, x_start:x_end]

    # Save cropped image
    # fund_name = fund_list[idx]
    # print(fund_name)
    output_path = os.path.join(output_dir, f"page_{idx+1}_left_half.png")
    cv2.imwrite(output_path, left_half)

    print(f"✅ Saved: {output_path}")

print("\n✅ All screenshots of right half completed.")


####################### Code to fetch text from screenshot after zooom with top crop ######################
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
fund_list = []
import re

def numerical_sort(value):
    numbers = re.findall(r'\d+', value)
    return int(numbers[0]) if numbers else float('inf')


for filename in sorted(os.listdir(output_dir), key=numerical_sort):
    # print(filename)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(filename)
    # start_printing = False
    if filename.endswith(".png"):
        image_path = os.path.join(output_dir, filename)
        # Read the image
        image = cv2.imread(image_path)

        # Convert to grayscale (better for OCR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


        # Apply thresholding (optional, improves text detection)
        # You can tweak this or try adaptive thresholding if needed
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Use pytesseract to extract text
        text = pytesseract.image_to_string(thresh)

        print("🔎 Extracted Text:")
        print(text)
        fund_list.append(text)

####################### Working Code to fetch text from rating tale save it in excel file with fund distributed as tabs######################
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
import pandas as pd
import re

input_pdf_path = output_pdf_path

reader = PdfReader(input_pdf_path)
writer = PdfWriter()
# fund_list = []
pattern = re.compile(r"(AAA\(SO\)|AAA\(CE\)|AA\(CE\)|A1\+|AA\+|AA-|AAA|AA|SOVRN SOV|SOVRN|SOV|Sovereign)")
agencies = ["CARE", "IND", "CRISIL", "ICRA", "FITCH", "India Ratings", "Brickwork", "Acuite"]
agency_pattern = re.compile(rf"({'|'.join(agencies)})")

pan = "AAAAE2916N"
mutual_fund = "Edelweiss Mutual Fund"
correct_rating_df = pd.DataFrame(columns=['Pan', 'ISIN No.', 'Mutual Fund', 'Fund Name','Fund Type', 'Portfolio', "Agency", 'Ratings', "Category", '(%) Of Total AUM', "Factsheet Date", "URL", 'Filename'])


def agency_matching(normalized_text, agency=''):
    agency_match = agency_pattern.search(normalized_text)
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

with pdfplumber.open(input_pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        print("page_num", page_num)
        fund_name = fund_list[page_num]
        page_heading = page.extract_text_lines()[0]['text'].strip().replace(" ", "_")
        tables = page.extract_tables()

        if not tables:
            continue

        for table in tables:
            header = table[0]
            if any("Composition by Ratings" in h for h in header if h):
                break  # skip this page
            elif any("Rating" in h for h in header if h) and any("Instrument" in h for h in header if h):
                # fund_list.append(page_heading)
                # writer.add_page(reader.pages[page_num])
                # print(table)
                for row in table[1:]:
                    if len(row) == 6:
                        row = row[:3]
                        # Count total \n across all strings
                        newline_count = sum(item.count("\n") for item in row if item is not None)

                        print(f"Total '\\n' found: {newline_count}")
                        print(len(row), row)
                        agency_and_rating_text = row[1]
                        if agency_and_rating_text is not None:
                            agency_matching_output = agency_matching(agency_and_rating_text)
                            remaining_text = agency_matching_output[0]
                            agency = agency_matching_output[1]
                            print("agency :", agency)


                            rating_matching_output = rating_matching(remaining_text)
                            remaining_text = rating_matching_output[0]
                            rating = rating_matching_output[1]
                            print("rating :", rating)
                        else:
                            agency = None
                            rating = None

                        temp_df = pd.DataFrame([{
                        "Pan": pan,
                        "ISIN No." : None,
                        "Mutual Fund" : mutual_fund,
                        "Fund Name" : fund_name,
                        "Fund Type" : None,
                        "Portfolio"  : row[0],
                        "Agency" : agency,
                        "Ratings" : rating,
                        "Category" : None,
                        "(%) Of Total AUM" : row[2],
                        "Factsheet Date" : None,
                        "URL" : None,
                                                }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                    else:
                        newline_count = sum(item.count("\n") for item in row if item is not None)

                        print(f"Total '\\n' found: {newline_count}")
                        if newline_count == 3:
                            row_1 = [item.split("\n")[0] for item in row]
                            row_2 = [item.split("\n")[1] for item in row]
                            # print(len(row), row)
                            # print("row_1 ", row_1)
                            # print("row_2 ", row_2)

                            agency_and_rating_text = row_1[1]
                            if agency_and_rating_text is not None:
                                agency_matching_output = agency_matching(agency_and_rating_text)
                                remaining_text = agency_matching_output[0]
                                agency = agency_matching_output[1]
                                print("agency :", agency)


                                rating_matching_output = rating_matching(remaining_text)
                                remaining_text = rating_matching_output[0]
                                rating = rating_matching_output[1]
                                print("rating :", rating)
                            else:
                                agency = None
                                rating = None
                            temp_df = pd.DataFrame([{
                            "Pan": pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : fund_name,
                            "Fund Type" : None,
                            "Portfolio"  : row_1[0],
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            "(%) Of Total AUM" : row_1[2],
                            "Factsheet Date" : None,
                            "URL" : None,
                                                    }])
                            correct_rating_df = pd.concat([correct_rating_df, temp_df])

                            agency_and_rating_text = row_2[1]
                            if agency_and_rating_text is not None:
                                agency_matching_output = agency_matching(agency_and_rating_text)
                                remaining_text = agency_matching_output[0]
                                agency = agency_matching_output[1]
                                print("agency :", agency)


                                rating_matching_output = rating_matching(remaining_text)
                                remaining_text = rating_matching_output[0]
                                rating = rating_matching_output[1]
                                print("rating :", rating)
                            else:
                                agency = None
                                rating = None
                            temp_df = pd.DataFrame([{
                            "Pan": pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : fund_name,
                            "Fund Type" : None,
                            "Portfolio"  : row_2[0],
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            "(%) Of Total AUM" : row_2[2],
                            "Factsheet Date" : None,
                            "URL" : None,
                                                    }])
                            correct_rating_df = pd.concat([correct_rating_df, temp_df])
                        else:
                            print(len(row), row)

                            agency_and_rating_text = row[1]
                            if agency_and_rating_text is not None:
                                agency_matching_output = agency_matching(agency_and_rating_text)
                                remaining_text = agency_matching_output[0]
                                agency = agency_matching_output[1]
                                print("agency :", agency)


                                rating_matching_output = rating_matching(remaining_text)
                                remaining_text = rating_matching_output[0]
                                rating = rating_matching_output[1]
                                print("rating :", rating)
                            else:
                                agency = None
                                rating = None    
                            temp_df = pd.DataFrame([{
                            "Pan": pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : fund_name,
                            "Fund Type" : None,
                            "Portfolio"  : row[0],
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            "(%) Of Total AUM" : row[2],
                            "Factsheet Date" : None,
                            "URL" : None,
                                                    }])
                            correct_rating_df = pd.concat([correct_rating_df, temp_df])
                break  # add this page once, then move to next page
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

# Save the filtered PDF
# with open(output_pdf_path, "wb") as f_out:
#     writer.write(f_out)

# print(f"✅ New PDF created: {output_pdf_path}")

########################## Block to map isin number to fund name ##############################################
# isin_df = pd.read_csv(r"D:\Nexensus_Projects\pdfEtraction\isin_Mastersheet.csv")
# # Create a mapping dictionary
# isin_map = dict(zip(isin_df['Fund Name'], isin_df['ISIN No.']))

# # Add mapped ISIN to df2
# correct_rating_df['ISIN No.'] = correct_rating_df['Fund Name'].map(isin_map)

# Save correct_rating_df to Excel file with separate sheets for each 'fund'
output_excel = "output_data\\correct_rating_df_grouped_by_fund_Edelweiss_{}.xlsx".format(month_name)
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    for fund, group_df in correct_rating_df.groupby("Fund Name"):
        # Clean sheet name: max 31 characters, remove invalid characters
        sheet_name = str(fund).replace("Edelweiss", "").replace("CRISIL", "").replace("IBX", "")[:31]
        invalid_chars = r'[:\\/?*[\]]'
        sheet_name = re.sub(invalid_chars, "_", sheet_name)

        print(f"Writing sheet: {sheet_name}")
        group_df.to_excel(writer, sheet_name=sheet_name, index=False)
        # group_df.drop(columns=["Fund Name"], errors="ignore").to_excel(writer, sheet_name=sheet_name, index=False)
        print("--------------------------------------------")

print(f"✅ Processed data saved to: {output_excel}")
    