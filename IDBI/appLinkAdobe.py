from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import subprocess
import os
import tempfile
import psutil
import win32gui
import win32process
import time
import winreg
import shlex
import requests
from urllib.parse import urlparse, parse_qs, unquote

# ================== DEFAULT PDF OPENER ==================

def get_default_pdf_opener():
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".pdf") as key:
            prog_id, _ = winreg.QueryValueEx(key, None)

        cmd_path = rf"{prog_id}\shell\open\command"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            command, _ = winreg.QueryValueEx(key, None)

        exe = shlex.split(command)[0]
        return exe
    except Exception:
        return None


ADOBE_PATH = get_default_pdf_opener()

app = Flask(__name__, static_folder=None)

# ================== FORCE CLOSE ADOBE ==================

def kill_acrobat_if_pdf_open(pdf_filename):
    pdf_filename = pdf_filename.lower()

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if pdf_filename in title:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    p = psutil.Process(pid)
                    if "acrobat" in p.name().lower():
                        p.kill()
                except psutil.NoSuchProcess:
                    pass

    win32gui.EnumWindows(enum_handler, None)

# ================== API ==================

@app.route("/open-section-url", methods=["POST"])
def open_pdf_section_from_url():

    pdf_url = request.form.get("pdf_url")
    section_text = request.form.get("section_text")

    if not pdf_url:
        return jsonify({"error": "pdf_url is required"}), 400

    if not section_text:
        return jsonify({"error": "section_text is required"}), 400

    # -------- Extract filename from URL --------
    parsed = urlparse(pdf_url)

    # Parse query string into dict
    query_params = parse_qs(parsed.query)

    folder_name = query_params.get("folder_name", [""])[0]
    file_name_encoded = query_params.get("file_name", [""])[0]

    # URL decode filename
    file_name = unquote(file_name_encoded)

    # Build final filename
    filename = f"{folder_name}_{file_name}"
    # filename = os.path.basename(parsed.path)
    # filename = os.path.basename(parsed.query)
    # print("filename", type(filename))
    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "URL must point to a PDF file"}), 400

    temp_pdf_path = os.path.join(tempfile.gettempdir(), filename)

    # -------- Close Adobe if same PDF open --------
    kill_acrobat_if_pdf_open(filename)
    time.sleep(0.5)

    # -------- Remove old temp file --------
    if os.path.exists(temp_pdf_path):
        try:
            os.remove(temp_pdf_path)
        except PermissionError:
            return jsonify({"error": "PDF is locked and cannot be replaced"}), 500

    # -------- Download PDF --------
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Failed to download PDF: {str(e)}"}), 400

    with open(temp_pdf_path, "wb") as f:
        f.write(response.content)

    # -------- Find section page --------
    doc = fitz.open(temp_pdf_path)
    page_number = None

    for i, page in enumerate(doc):
        if section_text.lower() in page.get_text().lower():
            page_number = i + 1
            break

    doc.close()

    if page_number is None:
        return jsonify({"error": "Section not found"}), 404

    # -------- Open PDF in Adobe --------
    subprocess.Popen([
        ADOBE_PATH,
        "/A",
        f"page={page_number}",
        temp_pdf_path
    ])

    return jsonify({
        "message": "PDF opened successfully in Adobe Acrobat",
        "page": page_number,
        "file": filename
    })


# ================== RUN ==================

if __name__ == "__main__":
    app.run(debug=True)
