import cv2
import numpy as np
import pandas as pd
import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
import matplotlib.pyplot as plt

pdf_path = r"D:\Nexensus_Projects\pdfEtraction\TataMF Factsheet-June 2025-60-66_red_lined.pdf"
images = convert_from_path(pdf_path, dpi=300)

def extract_red_boxes(image):
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([179, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    table_images = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 100 and h > 50:
            table_crop = cv_img[y:y+h, x:x+w]
            table_images.append(table_crop)
    return table_images

structured_tables = []
raw_text_tables = []

for page_img in images:
    tables = extract_red_boxes(page_img)
    for table_img in tables:
        ocr = pytesseract.image_to_data(table_img, config="--psm 6", output_type=Output.DATAFRAME)
        ocr = ocr[(ocr["text"].notnull()) & (ocr["conf"] > 40)].sort_values(by=["top", "left"])

        # Group words into lines
        lines, current_line, last_top = [], [], None
        for _, row in ocr.iterrows():
            if last_top is None or abs(row["top"] - last_top) <= 10:
                current_line.append((row["left"], row["text"]))
                last_top = row["top"]
            else:
                current_line.sort()
                lines.append([w[1] for w in current_line])
                current_line = [(row["left"], row["text"])]
                last_top = row["top"]
        if current_line:
            current_line.sort()
            lines.append([w[1] for w in current_line])

        # Create DataFrames
        raw_df = pd.DataFrame([" ".join(line) for line in lines], columns=["text"])
        structured_df = pd.DataFrame(
            [line[:4] + [""] * max(0, 4 - len(line)) for line in lines],
            columns=["Column 1", "Column 2", "Column 3", "Column 4"]
        )
        structured_tables.append(structured_df)
        raw_text_tables.append(raw_df)

        # Optional visual check
        plt.imshow(cv2.cvtColor(table_img, cv2.COLOR_BGR2RGB))
        plt.title("Detected Table")
        plt.axis('off')
        plt.show()

        print("Structured Table Preview:")
        print(structured_df.head())
        print("\nRaw Line Table Preview:")
        print(raw_df.head())
