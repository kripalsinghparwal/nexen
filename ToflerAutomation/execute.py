from main import process_company
import pandas as pd
import os
import time
import random
import pandas as pd
import re
from fuzzywuzzy import fuzz
from curl_cffi import requests
import hashlib
from main import normalize_company_suffix


all_data = []
input_file_path = r"D:\Nexensus_Projects\ToflerAutomation\input_folder\Nclt_30_12_2025.xlsx"
input_list = pd.read_excel(input_file_path)['c_name'].drop_duplicates().to_list()[:]
for input in input_list:
    output = process_company(input, all_data)
    all_data = output[1]
    print(output[0])

# === Final save ===
output_path = "output_" + input_file_path.split("\\")[-1]

if all_data:
    final_df = pd.DataFrame(all_data)
    # final_df = pd.read_excel(r"D:\Nexensus_Projects\ToflerAndZuba\Book7_data.xlsx")
    ratio_list = []
    
    # for row in final_df.itertuples():
    #     if isinstance(row.corrected_name, float) or row.corrected_name is None:
    #         ratio_list.append(0)
    #     else:
    #         if fuzz.ratio(row.input.lower().strip(), row.corrected_name.lower().replace("(old name)", "").strip()) != 100:
    #             ratio_list.append(fuzz.ratio(normalize_company_suffix(row.input).strip(), normalize_company_suffix(row.corrected_name.replace("(old name)", "").strip())))
    #         else:
    #             ratio_list.append(fuzz.ratio(row.input.lower().strip(), row.corrected_name.lower().replace("(old name)", "").strip()))

    # final_df['ratio'] = ratio_list

    # --- 1) Filter Active + ratio == 100 ---
    # df_100_active = final_df[(final_df['status'] == 'Active') & (final_df['ratio'] == 100)]
    df_100_active = final_df[(final_df['ratio'] == 100)]

    # --- 2) Remove rows from df_100_active based on input column ---
    df_remaining = final_df[~final_df['input'].isin(df_100_active['input'])]

    # --- 3) Filter 80Plus from remaining ---
    df_80_plus = df_remaining[df_remaining['ratio'] >= 80]

    # --- 4) Remaining after removing 80Plus ---
    df_remaining_final = df_remaining[~df_remaining['input'].isin(df_80_plus['input'])]
    # df_remaining_final = df_remaining[df_remaining['ratio'] < 80]

    # --- Save to Excel with multiple sheets ---
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        final_df.to_excel(writer, sheet_name='allData', index=False)
        df_100_active.to_excel(writer, sheet_name='100Active', index=False)
        df_80_plus.to_excel(writer, sheet_name='80Plus', index=False)
        df_remaining_final.to_excel(writer, sheet_name='remaining', index=False)

    print(f"🎉 All done! Final file saved to {output_path}")