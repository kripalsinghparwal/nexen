############## Code to split pdf to keep only pages with Rating table in it #####################
import pdfplumber
from PyPDF2 import PdfWriter, PdfReader

input_pdf_path = "TataMF Factsheet-June 2025.pdf"
output_pdf_path = "filtered_pages_with_ratings.pdf"

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
