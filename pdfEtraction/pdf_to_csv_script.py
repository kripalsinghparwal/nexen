import pdfplumber
import pandas as pd

pdf_path = r"D:\\Nexensus_Projects\\pdfEtraction\\List of Delhi Tax Payers Having turnover above 1.5 half crore assigned to Centre and State.pdf"
output_file = pdf_path.split("\\\\")[-1].replace('.pdf', "")
print(output_file)
all_rows = []
header = ["SN", "Trade Name", "GSTIN", "TIN", "PAN", "Ward Range", "Tax Office to which to be assigned"]

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        table = page.extract_table()
        if table:
            print("page_num", page_num)
            if page_num == 0:
                # Skip first row if it's header on first page
                rows = table[1:]
            else:
                rows = table
            all_rows.extend(rows)

# Convert to DataFrame
df = pd.DataFrame(all_rows, columns=header)

# Save to CSV or Excel
df.to_csv("{}.csv".format(output_file), index=False)
# df.to_csv("output_table.csv", index=False)
# or df.to_excel("output_table.xlsx", index=False)

print("Table extracted and saved successfully.")
