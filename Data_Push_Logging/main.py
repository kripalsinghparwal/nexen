from flask import Flask, request, send_file, jsonify
import pandas as pd
import psycopg2
import io
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from waitress import serve
from zoneinfo import ZoneInfo


# Load env
load_dotenv()

app = Flask(__name__)

# DB Config
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT"),
}


def get_modified_data_BS(file_path):
    conn = None
    cursor = None

    try:
        # =========================
        # ✅ VALIDATE INPUT
        # =========================
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path")

        # =========================
        # ✅ READ FILE
        # =========================
        pushed_df = pd.read_excel(
            file_path,
            sheet_name="Sheet1",
            usecols="A,B"
        )

        # =========================
        # ✅ DATA CLEANING
        # =========================
        pushed_df = pushed_df.rename(columns={
            "CompanyCIN": "cin",
            "YearOfBalanceSheet": "financial_year"
        })

        pushed_df["cin"] = pushed_df["cin"].astype(str).str.strip().str.upper()
        pushed_df["financial_year"] = pushed_df["financial_year"].astype(str).str.strip()

        pushed_df = pushed_df.dropna(subset=["cin", "financial_year"])
        pushed_df = pushed_df.drop_duplicates(subset=["cin", "financial_year"])

        if pushed_df.empty:
            raise ValueError("No valid data found")

        # =========================
        # ✅ DB CONNECTION
        # =========================
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(readonly=True)
        cursor = conn.cursor()

        # =========================
        # ✅ BUILD VALUES STRING
        # =========================
        values = []

        for row in pushed_df.itertuples(index=False):
            cin = str(row.cin).replace("'", "''")
            fy = str(row.financial_year).replace("'", "''")

            values.append(f"('{cin}', '{fy}')")

        values_sql = ",".join(values)

        # =========================
        # ✅ QUERY (BS TABLE)
        # =========================
        query = f"""
            WITH temp_filter(cin, financial_year) AS (
                VALUES
                {values_sql}
            )

            SELECT
                f.cin,
                f.financial_year,

                t.created,
                t.modified,

                -- ✅ TRUE if record exists in DB
                CASE
                    WHEN t.company_id IS NOT NULL THEN TRUE
                    ELSE FALSE
                END AS IsDataPresent,

                -- ✅ TRUE if modified today
                COALESCE(
                    DATE(t.modified) = CURRENT_DATE,
                    FALSE
                ) AS isModified_today

            FROM temp_filter f

            LEFT JOIN company_core.t_company_detail cd
                ON cd.cin = f.cin

            LEFT JOIN company_core.t_company_balance_sheet t
                ON t.company_id = cd.id
            AND t.financial_year::TEXT = f.financial_year
        """

        database_df = pd.read_sql(query, conn)

        return database_df

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_modified_data_PnL(file_path):
    conn = None
    cursor = None

    try:
        # =========================
        # ✅ VALIDATE INPUT
        # =========================
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path")

        # =========================
        # ✅ READ FILE
        # =========================
        pushed_df = pd.read_excel(
            file_path,
            sheet_name="Sheet1",
            usecols="A,B"
        )

        # =========================
        # ✅ DATA CLEANING
        # =========================
        pushed_df = pushed_df.rename(columns={
            "CIN": "cin",
            "FinancialYear": "financial_year"  # keep same if your file uses it
        })

        pushed_df["cin"] = pushed_df["cin"].astype(str).str.strip().str.upper()
        pushed_df["financial_year"] = pushed_df["financial_year"].astype(str).str.strip()

        pushed_df = pushed_df.dropna(subset=["cin", "financial_year"])
        pushed_df = pushed_df.drop_duplicates(subset=["cin", "financial_year"])

        if pushed_df.empty:
            raise ValueError("No valid data found")

        # =========================
        # ✅ DB CONNECTION
        # =========================
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(readonly=True)
        cursor = conn.cursor()

        # =========================
        # ✅ BUILD VALUES
        # =========================
        # =========================
        # ✅ BUILD VALUES STRING
        # =========================
        values = []

        for row in pushed_df.itertuples(index=False):
            cin = str(row.cin).replace("'", "''")
            fy = str(row.financial_year).replace("'", "''")

            values.append(f"('{cin}', '{fy}')")

        values_sql = ",".join(values)

        # =========================
        # ✅ QUERY (PnL TABLE)
        # =========================
        query = f"""
            WITH temp_filter(cin, financial_year) AS (
                VALUES
                {values_sql}
            )

            SELECT
                f.cin,
                f.financial_year,

                t.created,
                t.modified,

                -- ✅ TRUE if record exists in DB
                CASE
                    WHEN t.company_id IS NOT NULL THEN TRUE
                    ELSE FALSE
                END AS IsDataPresent,

                -- ✅ TRUE if modified today
                COALESCE(
                    DATE(t.modified) = CURRENT_DATE,
                    FALSE
                ) AS isModified_today

            FROM temp_filter f

            LEFT JOIN company_core.t_company_detail cd
                ON cd.cin = f.cin

            LEFT JOIN company_core.t_company_pnl t
                ON t.company_id = cd.id
            AND t.financial_year::TEXT = f.financial_year
        """

        database_df = pd.read_sql(query, conn)

        return database_df

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


INPUT_DIR = os.getenv("INPUT_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/process-data", methods=["POST"])
def process_data():
    timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d_%H-%M-%S")
    data = request.json
    report_type = data.get("type")

    if report_type not in ["BS", "PnL"]:
        return jsonify({"error": "type must be 'BS' or 'PnL'"}), 400

    # ✅ REPLACED url_map → function_map
    function_map = {
        "BS": get_modified_data_BS,
        "PnL": get_modified_data_PnL
    }

    target_function = function_map[report_type]

    keyword = report_type.lower()

    df_list = []
    processed_files = []

    for filename in os.listdir(INPUT_DIR):

        # ✅ Filter files based on BS / PnL in name
        if (
            filename.endswith((".xlsx", ".xls")) and
            keyword in filename.lower()
        ):
            file_path = os.path.join(INPUT_DIR, filename)
            processed_files.append(filename)

            print(f"Processing: {filename}, {file_path}")

            try:
                # ✅ DIRECT FUNCTION CALL (NO API)
                temp_df = target_function(file_path)

                if temp_df is not None and not temp_df.empty:
                    temp_df["source_file"] = filename
                    df_list.append(temp_df)

                print(f"✅ Processed: {filename}")

            except Exception as e:
                print(f"🚨 Error processing {filename}: {str(e)}")

    # =========================
    # ✅ COMBINE DATA
    # =========================
    if df_list:
        combined_df = pd.concat(df_list, ignore_index=True)
    else:
        return jsonify({
            "message": "No matching files found",
            "type": report_type
        })

    # =========================
    # ✅ SAFE FILTER
    # =========================
    if "isdatapresent" not in combined_df.columns:
        return jsonify({
            "error": "'isdatapresent' column missing in response"
        }), 500

    combined_df["isdatapresent"] = combined_df["isdatapresent"].astype(str).str.lower()

    filtered_df = combined_df[
        combined_df["isdatapresent"].isin(["false", "0"])
    ]

    # =========================
    # ✅ SAVE
    # =========================
    if len(filtered_df) > 0:
        output_file = f"combined_filtered_output_{report_type}_{timestamp}.csv"
        final_output_path = os.path.join(OUTPUT_DIR, output_file)
        filtered_df.to_csv(final_output_path, index=False)

        return jsonify({
            "message": "Processing completed",
            "type": report_type,
            "files_processed": processed_files,
            "total_files": len(processed_files),
            "output_file": final_output_path,
            "rows_before": len(combined_df),
            "rows_after": len(filtered_df)
        })
    else:
        return jsonify({
            "message": "Processing completed",
            "type": report_type,
            "files_processed": processed_files,
            "total_files": len(processed_files),
            "output_file": None,
            "rows_before": len(combined_df),
            "rows_after": len(filtered_df)
        })

@app.route("/")
def home():
    return "Server is running"

print("Starting server on http://0.0.0.0:5000")

if __name__ == "__main__":
    # app.run(debug=False)
    serve(app, host="0.0.0.0", port=5000)
    # app.run(host="0.0.0.0", port=5000)