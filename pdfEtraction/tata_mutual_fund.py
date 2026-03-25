############## Code to split pdf to keep only pages with Rating table in it #####################
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader

input_pdf_path = "TataMF Factsheet-June 2025.pdf"
output_pdf_path = "filtered_{}.pdf".format(input_pdf_path.split(".")[0])

reader = PdfReader(input_pdf_path)
writer = PdfWriter()

with pdfplumber.open(input_pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        tables = page.extract_tables()

        if not tables:
            continue

        for table in tables:
            header = table[0]
            if any("Composition by Ratings" in h for h in header if h):
                break  # skip this page
            elif any("Ratings" in h for h in header if h):
                writer.add_page(reader.pages[page_num])
                break  # add this page once, then move to next page

# Save the filtered PDF
with open(output_pdf_path, "wb") as f_out:
    writer.write(f_out)

print(f"✅ New PDF created: {output_pdf_path}")



########################### Code to Screeshot tables fully and only rating tables in separate folder ###############
import pdfplumber
from pdf2image import convert_from_path
import cv2
import numpy as np
import os

# First stage: Save full screenshots below tables
def save_full_screenshots():
    pdf_path = "filtered_TataMF Factsheet-June 2025.pdf"
    output_dir_full = "screenshots_bottom_blocks"
    os.makedirs(output_dir_full, exist_ok=True)

    DPI = 300
    PDF_DPI = 72
    SCALE = DPI / PDF_DPI

    images = convert_from_path(pdf_path, dpi=DPI)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.find_tables()
            page_heading = page.extract_text_lines()[0]['text'].strip().replace(" ", "_")
            
            for i, table in enumerate(tables):
                header = table.extract()[0]

                if any("Composition by Ratings" in h for h in header if h):
                    continue

                if any("Ratings" in h for h in header if h):
                    x0, top, x1, bottom = table.bbox
                    image = np.array(images[page_num])
                    h, w, _ = image.shape

                    padding = 20
                    x0_img = max(0, int(x0 * SCALE) - padding)
                    x1_img = min(w, int(x1 * SCALE) + padding)
                    top_img = int(bottom * SCALE) - 10
                    bottom_img = int(page.height * SCALE)

                    x0_img = max(0, min(x0_img, w))
                    x1_img = max(0, min(x1_img, w))
                    top_img = max(0, min(top_img, h))
                    bottom_img = max(0, min(bottom_img, h))

                    crop = image[top_img:bottom_img, x0_img:x1_img]
                    # filename = f"{output_dir_full}/page_{page_num+1}_table_{i+1}_below.png"
                    filename = f"{output_dir_full}/{page_heading}_page_{page_num+1}_table_{i+1}_below.png"
                    cv2.imwrite(filename, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
                    print(f"✅ Full screenshot saved: {filename}")

# Second stage: Process saved screenshots to crop at rectangles
def detect_topmost_deep_blue_rectangle(image_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error loading image: {image_path}")
        return None

    # Convert to HSV color space for better color segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define deeper blue color range in HSV
    lower_blue = np.array([100, 150, 100])  # Hue, Saturation, Value
    upper_blue = np.array([140, 255, 255])
    
    # Create mask for deep blue regions
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Morphological operations to clean up the mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and collect valid rectangles
    valid_rectangles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 2000:  # Minimum area threshold
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        if h > 30:
            aspect_ratio = w / float(h)
            
            # Look for wide rectangles
            # if 3.0 < aspect_ratio < 15.0:
            if aspect_ratio:
                valid_rectangles.append({
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'area': area
                })
    
    if valid_rectangles:
        # Sort by vertical position first (y), then horizontal (x)
        valid_rectangles.sort(key=lambda r: (r['y'], r['x']))
        
        # Select the topmost rectangle
        top_rect = valid_rectangles[0]
        
        # Extract and return rectangle
        return {
            'rectangle': image[top_rect['y']:top_rect['y']+top_rect['h'], 
                         top_rect['x']:top_rect['x']+top_rect['w']],
            'coordinates': (top_rect['x'], top_rect['y'], top_rect['w'], top_rect['h']),
            'mask': mask
        }
    
    return None


def crop_at_rectangles():
    input_dir = "screenshots_bottom_blocks"
    output_dir_cropped = "screenshots_cropped_at_rectangles"
    os.makedirs(output_dir_cropped, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith(".png"):
            img_path = os.path.join(input_dir, filename)
            
            # Use your improved detection function
            result = detect_topmost_deep_blue_rectangle(img_path)
            
            if result:
                x, y, w, h = result['coordinates']
                image = cv2.imread(img_path)
                
                # Crop from top of image to top of detected rectangle
                cropped_img = image[:y, :]
                
                # Save with original filename (not prefixed with 'cropped_')
                output_path = os.path.join(output_dir_cropped, filename)
                cv2.imwrite(output_path, cropped_img)
                print(f"✅ Cropped at y={y}px: {output_path}")
                
                # Optional: Save debug images
                debug_dir = os.path.join(output_dir_cropped, "debug")
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(os.path.join(debug_dir, f"mask_{filename}"), result['mask'])
            else:
                print(f"⚠️ No rectangle found in {filename} - saving original")
                # Copy original image if no rectangle detected
                original = cv2.imread(img_path)
                output_path = os.path.join(output_dir_cropped, filename)
                cv2.imwrite(output_path, original)

# Run both stages
save_full_screenshots()
crop_at_rectangles()

print("Processing complete!")
print(f"Full screenshots saved to: screenshots_bottom_blocks")
print(f"Cropped screenshots saved to: screenshots_cropped_at_rectangles")


####################### Testing Code to fetch text from screenshot after zooom and save it in excel file with fund distributed as tabs######################
import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
import re

rating_set = set()
# Set Tesseract path (update for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pan = 'AAATT0570A'
mutual_fund = "TATA MUTUAL FUND"
input_dir = "screenshots_cropped_at_rectangles"
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




import pandas as pd
correct_rating_df = pd.DataFrame(columns=['Pan', 'ISIN No.', 'Mutual Fund', 'Fund Name','Fund Type', 'Portfolio', "Agency", 'Ratings', "Category", '(%) Of Total AUM', "Factsheet Date", "URL", 'Filename'])
remaining_rating_df = pd.DataFrame(columns=['Text'])
for filename in os.listdir(input_dir):
    print("---------------------------------------------------------->>>>>>>>>>>>>>>>>>>>>>>>--------------------------------------------------------------")
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
                # print(f"\nRow {i+1}:")
                # print(text)  # Print full text block (don't split by new lines)
                # print(len(re.split(r'\s{2,}', text)), re.split(r'\s{2,}', text))
                if len(re.split(r'\s{2,}', text)) ==4 :
                    # print(text)
                    # print(len(re.split(r'\s{2,}', text)), re.split(r'\s{2,}', text))
                    if "\n" in text:
                        first_line_text = text.split("\n")[0]
                        second_line_text = text.split("\n")[1]
                        # print(first_line_text)
                        # print(second_line_text)
                        if len(re.split(r'\s{2,}', first_line_text)) == 1:
                            agency_and_rating_text = re.split(r'\s{2,}', second_line_text)[1]
                            agency_matching_output = agency_matching(agency_and_rating_text)
                            remaining_text = agency_matching_output[0]
                            agency = agency_matching_output[1]
                            print("agency :", agency)


                            rating_matching_output = rating_matching(remaining_text)
                            remaining_text = rating_matching_output[0]
                            rating = rating_matching_output[1]
                            print("rating :", rating)

                            # print(re.split(r'\s{2,}', first_line_text)[0] + "\n" + re.split(r'\s{2,}', second_line_text)[0])
                            temp_df = pd.DataFrame([{
                            "Pan" : pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : filename.split("_page")[0].replace("_", " "),
                            "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                            "Portfolio"  : re.split(r'\s{2,}', first_line_text)[0] + "\n" + re.split(r'\s{2,}', second_line_text)[0],
                            # "Agency" : None,
                            # "Ratings" : re.split(r'\s{2,}', second_line_text)[1],
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            # "Market Value Rs Lakhs" : re.split(r'\s{2,}', second_line_text)[2],
                            "(%) Of Total AUM" : re.split(r'\s{2,}', second_line_text)[3],
                            "Factsheet Date" : None,
                            "URL" : None,
                            "Filename" : filename,
                            
                            }])
                        elif len(re.split(r'\s{2,}', second_line_text)) == 1:
                            # print(re.split(r'\s{2,}', first_line_text)[0] + "\n" + re.split(r'\s{2,}', second_line_text)[0])
                            agency_and_rating_text = re.split(r'\s{2,}', first_line_text)[1]
                            agency_matching_output = agency_matching(agency_and_rating_text)
                            remaining_text = agency_matching_output[0]
                            agency = agency_matching_output[1]
                            print("agency :", agency)


                            rating_matching_output = rating_matching(remaining_text)
                            remaining_text = rating_matching_output[0]
                            rating = rating_matching_output[1]
                            print("rating :", rating)

                            temp_df = pd.DataFrame([{
                            "Pan" : pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : filename.split("_page")[0].replace("_", " "),
                            "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                            "Portfolio"  : re.split(r'\s{2,}', first_line_text)[0] + "\n" + re.split(r'\s{2,}', second_line_text)[0],
                            # "Agency" : None,
                            # "Ratings" : re.split(r'\s{2,}', first_line_text)[1],
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            # "Market Value Rs Lakhs" : re.split(r'\s{2,}', first_line_text)[2],
                            "(%) Of Total AUM" : re.split(r'\s{2,}', first_line_text)[3],
                            "Factsheet Date" : None,
                            "URL" : None,
                            "Filename" : filename,
                            }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                    else:
                        # print(text)
                        # print(len(re.split(r'\s{2,}', text)), re.split(r'\s{2,}', text))
                        splited_column_row = re.split(r'\s{2,}', text)
                        # print(re.split(r'\s{2,}', text)[1])
                        # rating_set.add(re.split(r'\s{2,}', text)[1])
                        # print(splited_column_row[1])
                        rating_set.add(splited_column_row[1])

                        agency_and_rating_text = splited_column_row[1]
                        agency_matching_output = agency_matching(agency_and_rating_text)
                        remaining_text = agency_matching_output[0]
                        agency = agency_matching_output[1]
                        print("agency :", agency)


                        rating_matching_output = rating_matching(remaining_text)
                        remaining_text = rating_matching_output[0]
                        rating = rating_matching_output[1]
                        print("rating :", rating)
                        temp_df = pd.DataFrame([{
                            "Pan" : pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : filename.split("_page")[0].replace("_", " "),
                            "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                            "Portfolio" : splited_column_row[0],
                            # "Agency" : None,
                            # "Ratings" : splited_column_row[1],
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            # "Market Value Rs Lakhs" : splited_column_row[2],
                            "(%) Of Total AUM" : splited_column_row[3],
                            "Factsheet Date" : None,
                            "URL" : None,
                            "Filename" : filename,

                        }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                
                elif "SIP - If you had invested" in text:
                    print("SIP - If you had invested text appeared and skipped")
                elif len(normalized_text.split("\n")) ==1:
                    print("normalized_text :", normalized_text)


                    # portfolio = text.split("\n")[0]
                    agency_matching_output = agency_matching(normalized_text)
                    normalized_text = agency_matching_output[0]
                    agency = agency_matching_output[1]


                    rating_matching_output = rating_matching(normalized_text)
                    normalized_text = rating_matching_output[0]
                    rating = rating_matching_output[1]

                    AUM_matching_output = AUM_matching(normalized_text)
                    normalized_text = AUM_matching_output[0]
                    total_AUM = AUM_matching_output[1]

                    MV_matching_output = MV_matching(normalized_text)
                    normalized_text = MV_matching_output[0]
                    market_value = MV_matching_output[1]

                    portfolio = normalized_text.strip()

                    temp_df = pd.DataFrame([{
                        "Pan" : pan,
                        "ISIN No." : None,
                        "Mutual Fund" : mutual_fund,
                        "Fund Name" : filename.split("_page")[0].replace("_", " "),
                        "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                        "Portfolio" : portfolio,
                        "Agency" : agency,
                        "Ratings" : rating,
                        "Category" : None,
                        # "Market Value Rs Lakhs" : None,
                        "(%) Of Total AUM" : total_AUM,
                        "Factsheet Date" : None,
                        "URL" : None,
                        "Filename" : filename,

                    }])
                    correct_rating_df = pd.concat([correct_rating_df, temp_df])
                    print("remaining_text", normalized_text)
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                

                # else:
                    # temp_df = pd.DataFrame([{
                    #     "Pan" : pan,
                    #     "ISIN No." : None,
                    #     "Mutual Fund" : mutual_fund,
                    #     "Fund Name" : filename.split("_page")[0].replace("_", " "),
                    #     "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                    #     "Portfolio" : text,
                    #     "Agency" : None,
                    #     "Ratings" : None,
                    #     "Category" : None,
                    #     # "Market Value Rs Lakhs" : None,
                    #     "(%) Of Total AUM" : None,
                    #     "Factsheet Date" : None,
                    #     "URL" : None,
                    #     "Filename" : filename,

                    # }])
                    # correct_rating_df = pd.concat([correct_rating_df, temp_df])
                elif len(text.split("\n")) ==2:
                    if len(re.split(r'\s{2,}', text.split("\n")[0])) == 1:
                        # print("remaining_text_else")
                        # print(text)
                        portfolio = text.split("\n")[0]
                        agency_matching_output = agency_matching(text.split("\n")[1])
                        normalized_text = agency_matching_output[0]
                        agency = agency_matching_output[1]


                        agency_matching_output = rating_matching(normalized_text)
                        normalized_text = agency_matching_output[0]
                        rating = agency_matching_output[1]

                        AUM_matching_output = AUM_matching(normalized_text)
                        normalized_text = AUM_matching_output[0]
                        total_AUM = AUM_matching_output[1]

                        MV_matching_output = MV_matching(normalized_text)
                        normalized_text = MV_matching_output[0]
                        market_value = MV_matching_output[1]

                        portfolio = portfolio + "\n" + normalized_text

                        # print("agency", agency)
                        # print("rating", rating)
                        # print("total_AUM", total_AUM)
                        # print("market_value", market_value)
                        # print("portfolio :")
                        # print(portfolio)

                        temp_df = pd.DataFrame([{
                            "Pan" : pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : filename.split("_page")[0].replace("_", " "),
                            "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                            "Portfolio" : portfolio,
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            # "Market Value Rs Lakhs" : None,
                            "(%) Of Total AUM" : total_AUM,
                            "Factsheet Date" : None,
                            "URL" : None,
                            "Filename" : filename,

                        }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    else:
                        print("unresolved 2:", len(text.split("\n")),text)
                        line_1 = text.split("\n")[0]
                        agency_matching_output = agency_matching(line_1)
                        normalized_text = agency_matching_output[0]
                        agency = agency_matching_output[1]


                        agency_matching_output = rating_matching(normalized_text)
                        normalized_text = agency_matching_output[0]
                        rating = agency_matching_output[1]

                        AUM_matching_output = AUM_matching(normalized_text)
                        normalized_text = AUM_matching_output[0]
                        total_AUM = AUM_matching_output[1]

                        MV_matching_output = MV_matching(normalized_text)
                        normalized_text = MV_matching_output[0]
                        market_value = MV_matching_output[1]

                        portfolio = normalized_text.strip()

                        temp_df = pd.DataFrame([{
                            "Pan" : pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : filename.split("_page")[0].replace("_", " "),
                            "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                            "Portfolio" : portfolio,
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            # "Market Value Rs Lakhs" : None,
                            "(%) Of Total AUM" : total_AUM,
                            "Factsheet Date" : None,
                            "URL" : None,
                            "Filename" : filename,

                        }])
                        print(temp_df)
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


                        line_2 = text.split("\n")[1]
                        agency_matching_output = agency_matching(line_2)
                        normalized_text = agency_matching_output[0]
                        agency = agency_matching_output[1]


                        agency_matching_output = rating_matching(normalized_text)
                        normalized_text = agency_matching_output[0]
                        rating = agency_matching_output[1]

                        AUM_matching_output = AUM_matching(normalized_text)
                        normalized_text = AUM_matching_output[0]
                        total_AUM = AUM_matching_output[1]

                        MV_matching_output = MV_matching(normalized_text)
                        normalized_text = MV_matching_output[0]
                        market_value = MV_matching_output[1]

                        portfolio = normalized_text.strip()

                        temp_df = pd.DataFrame([{
                            "Pan" : pan,
                            "ISIN No." : None,
                            "Mutual Fund" : mutual_fund,
                            "Fund Name" : filename.split("_page")[0].replace("_", " "),
                            "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                            "Portfolio" : portfolio,
                            "Agency" : agency,
                            "Ratings" : rating,
                            "Category" : None,
                            # "Market Value Rs Lakhs" : None,
                            "(%) Of Total AUM" : total_AUM,
                            "Factsheet Date" : None,
                            "URL" : None,
                            "Filename" : filename,

                        }])
                        correct_rating_df = pd.concat([correct_rating_df, temp_df])
                        print(temp_df)
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        
                else:
                    print("unresolved :", text)
                    temp_df = pd.DataFrame([{
                        "Pan" : pan,
                        "ISIN No." : None,
                        "Mutual Fund" : mutual_fund,
                        "Fund Name" : filename.split("_page")[0].replace("_", " "),
                        "Fund Type" : filename.split("_page")[0].replace("_", " ").split(' ', 1)[-1],
                        "Portfolio" : text,
                        "Agency" : None,
                        "Ratings" : None,
                        "Category" : None,
                        # "Market Value Rs Lakhs" : None,
                        "(%) Of Total AUM" : None,
                        "Factsheet Date" : None,
                        "URL" : None,
                        "Filename" : filename,

                    }])
                    correct_rating_df = pd.concat([correct_rating_df, temp_df])        


                print("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

print("\nText extraction complete!")

def clean_decimal_values(MV):
    print("before", MV)
    try:
        if "." not in MV:
            MV = MV.replace(",", ".").replace(" ", ".")
            if "." not in MV:
                MV = MV[:-2] + "." + MV[-2:]
        elif "," in MV:
            # print("coming here")
            MV = MV.replace(",", "").replace(" ", "")
        elif " " in MV:
            MV = MV.replace(" ", "")
        print("after", MV)
        return MV
    except Exception as e:
        print(e)
        return None

# correct_rating_df['Market Value Rs Lakhs'] = correct_rating_df['Market Value Rs Lakhs'].apply(clean_decimal_values)
# correct_rating_df['% to NAV'] = correct_rating_df['% to NAV'].apply(clean_decimal_values)
# correct_rating_df.to_csv("correct_rating_df.csv", index=False)
# print("Processed Data Saved to csv")


def clean_portfolio(portfolio):
    if "GO!" in portfolio:
        portfolio = portfolio.replace("GO!", "GOI")
    if "GOI!" in portfolio:
        portfolio = portfolio.replace("GOI!", "GOI")
    if "Ses " in portfolio:
        portfolio = portfolio.replace("Ses ", "sgs ")
    return portfolio

correct_rating_df['Portfolio'] = correct_rating_df['Portfolio'].apply(clean_portfolio)

########################## Block to map isin number to fund name ##############################################
isin_df = pd.read_csv(r"D:\Nexensus_Projects\pdfEtraction\isin_Mastersheet.csv")
# Create a mapping dictionary
isin_map = dict(zip(isin_df['Fund Name'], isin_df['ISIN No.']))

# Add mapped ISIN to df2
correct_rating_df['ISIN No.'] = correct_rating_df['Fund Name'].map(isin_map)

# Save correct_rating_df to Excel file with separate sheets for each 'fund'
output_excel = "correct_rating_df_grouped_by_fund.xlsx"

with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    for fund, group_df in correct_rating_df.groupby("Fund Name"):
        # Clean sheet name: max 31 characters, remove invalid characters
        sheet_name = str(fund)[:31]
        invalid_chars = r'[:\\/?*[\]]'
        sheet_name = re.sub(invalid_chars, "_", sheet_name)

        print(f"Writing sheet: {sheet_name}")
        group_df.to_excel(writer, sheet_name=sheet_name, index=False)
        # group_df.drop(columns=["Fund Name"], errors="ignore").to_excel(writer, sheet_name=sheet_name, index=False)
        print("--------------------------------------------")

print(f"✅ Processed data saved to: {output_excel}")
    