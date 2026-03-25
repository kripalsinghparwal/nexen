############## Code to split pdf to keep only pages with Rating table in it #####################
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader
from datetime import datetime

# month_name = datetime.now().strftime("%b")
month_name = "Sep"

input_pdf_path = "6e735b17-bandhan-passive-factsheet-sept-2025.pdf"
output_pdf_path = "filtered_{}.pdf".format(input_pdf_path.split(".")[0])

reader = PdfReader(input_pdf_path)
writer = PdfWriter()
fund_list = [
    "Gilt April 2026 Index Fund",
    "Gilt June 2027 Index Fund",
    "Gilt April 2028 Index Fund",
    "Gilt April 2032 Index Fund",
    "90colon10 SDL Plus Gilt- November 2026 Index Fund",
    "90colon10 SDL Plus Gilt- September 2027 Index Fund",
    "90colon10 SDL Plus Gilt-April 2032 Index Fund",
    "10colon90 Gilt + SDL Index - Dec 2029 Fund",
    "Financial Services 3-6 Months Debt Index Fund",
]

with pdfplumber.open(input_pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        words = page.extract_words()
        page_heading = page.extract_text_lines()[0]['text'].strip().replace(" ", "_")
        capital_words = [word['text'] for word in words if word['text'].isupper()]
        if "PORTFOLIO" in capital_words:
            for word in words:
                if 'Rating' in word['text']:
                    print(f"\n=== Page {page_num + 1} ===")
                    # print(page_num,capital_words)
                    print("page heading :", page_heading.split("Fund")[0] + "Fund")
                    # fund_list.append(page_heading.split("Fund")[0].replace(":", "double_colon") + "Fund")
                    print([word['text'] for word in words])
                    writer.add_page(reader.pages[page_num])
                    break  # add this page once, then move to next page

# Save the filtered PDF
with open(output_pdf_path, "wb") as f_out:
    writer.write(f_out)

############ Code to save screenshot of right_half of every page that contains rating table ################
import os
from pdf2image import convert_from_path
import cv2
import numpy as np

# === Configuration ===
pdf_path = output_pdf_path  # Replace with your actual PDF file path
output_dir = "right_half_screenshots_Bandhan\\{}".format(month_name)
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


    # Crop right half (60% to 100%)
    x_start = int(0.33 * width)
    y_start = int(0.08 * height)  # 15% from top
    right_half = image[y_start:, x_start:]
    # right_half = image[:, x_start:]

    # Save cropped image
    fund_name = fund_list[idx]
    print(fund_name)
    output_path = os.path.join(output_dir, f"{fund_name}_page_{idx+1}_right_half.png")
    cv2.imwrite(output_path, right_half)

    print(f"✅ Saved: {output_path}")

print("\n✅ All screenshots of right half completed.")


####################### Code to fetch text from screenshot after zooom with top crop ######################
import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
import re

rating_set = set()
# Set Tesseract path (update for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

input_dir = "right_half_screenshots_Bandhan\\{}".format(month_name)
pan = "AAETS9556K"
mutual_fund = "Bandhan Mutual Fund"
import pandas as pd
correct_rating_df = pd.DataFrame(columns=['Pan', 'ISIN No.', 'Mutual Fund', 'Fund Name','Fund Type', 'Portfolio', "Agency", 'Ratings', "Category", '(%) Of Total AUM', "Factsheet Date", "URL", 'Filename'])
remaining_rating_df = pd.DataFrame(columns=['Text'])
for filename in os.listdir(input_dir)[:]:
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # start_printing = False
    if filename.endswith(".png"):
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
        print("\nExtracted Table Rows:")
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

            if text:
                if "ASSET OUALITY" in text :
                        break
                if "PORTFOLIO" in text or "% of NAV" in text or "|" in text:
                     continue
                # print(text.split("\n"))
                # print(len(re.split(r'\s{2,}', text)), re.split(r'\s{2,}', text))
                for t in text.split("\n"):
                    print(re.split(r'\s{2,}', t))
                    print(len(re.split(r'\s{2,}', t)))
                    print("--------------------------------------")
                    splited_row = re.split(r'\s{2,}', t)

                    if len(re.split(r'\s{2,}', t)) ==3:
                        temp_df = pd.DataFrame([{
                        "Pan": pan,
                        "ISIN No." : None,
                        "Mutual Fund" : mutual_fund,
                        "Fund Name" : "Bandhan " + filename.split("_page")[0].replace("colon", ":").replace("_", " "),
                        "Fund Type" : filename.split("_page")[0].replace("colon", ":").replace("_", " "),
                        "Portfolio"  : splited_row[0],
                        "Agency" : None,
                        "Ratings" : splited_row[1].replace("Ai+", "A1+"),
                        "Category" : None,
                        "(%) Of Total AUM" : splited_row[2],
                        "Factsheet Date" : None,
                        "URL" : None,
                        "Filename" : filename,                        }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                    elif len(re.split(r'\s{2,}', t)) ==2:
                        temp_df = pd.DataFrame([{
                        "Pan": pan,
                        "ISIN No." : None,
                        "Mutual Fund" : mutual_fund,
                        "Fund Name" : "Bandhan " + filename.split("_page")[0].replace("colon", ":").replace("_", " "),
                        "Fund Type" : filename.split("_page")[0].replace("colon", ":").replace("_", " "),
                        "Portfolio"  : splited_row[0],
                        "Agency" : None,
                        "Ratings" : None,
                        "Category" : None,
                        "(%) Of Total AUM" : splited_row[1],
                        "Factsheet Date" : None,
                        "URL" : None,
                        "Filename" : filename, 
                        }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                    else:
                         print("remaining ones :", t)

########################## Block to map isin number to fund name ##############################################
# isin_df = pd.read_csv(r"D:\Nexensus_Projects\pdfEtraction\isin_Mastersheet.csv")
# # Create a mapping dictionary
# isin_map = dict(zip(isin_df['Fund Name'], isin_df['ISIN No.']))

# # Add mapped ISIN to df2
# correct_rating_df['ISIN No.'] = correct_rating_df['Fund Name'].map(isin_map)

# Save correct_rating_df to Excel file with separate sheets for each 'fund'
output_excel = "output_data\\correct_rating_df_grouped_by_fund_Bandhan_{}.xlsx".format(month_name)

with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    for fund, group_df in correct_rating_df.groupby("Fund Name"):
        # Clean sheet name: max 31 characters, remove invalid characters
        sheet_name = str(fund).replace("Bandhan ", "").replace("CRISIL IBX", "").replace("CRISIL-IBX", "")[:31]
        invalid_chars = r'[:\\/?*[\]]'
        sheet_name = re.sub(invalid_chars, "_", sheet_name)

        print(f"Writing sheet: {sheet_name}")
        group_df.to_excel(writer, sheet_name=sheet_name, index=False)
        # group_df.drop(columns=["Fund Name"], errors="ignore").to_excel(writer, sheet_name=sheet_name, index=False)
        print("--------------------------------------------")

print(f"✅ Processed data saved to: {output_excel}")
    

