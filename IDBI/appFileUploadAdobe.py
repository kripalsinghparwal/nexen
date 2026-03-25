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

def get_default_pdf_opener():
    try:
        # Step 1: Get ProgID for .pdf
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".pdf") as key:
            prog_id, _ = winreg.QueryValueEx(key, None)

        # Step 2: Get open command for that ProgID
        cmd_path = rf"{prog_id}\shell\open\command"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            command, _ = winreg.QueryValueEx(key, None)

        # Example command:
        # "C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" "%1"

        exe = shlex.split(command)[0]
        return exe
    except Exception:
        return None

ADOBE_PATH = get_default_pdf_opener()


app = Flask(__name__, static_folder=None)

# ADOBE_PATH = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"


# -------------------- Force-close Acrobat if PDF is open --------------------
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


@app.route("/open-section-upload", methods=["POST"])
def open_pdf_section_upload():
    # 1️⃣ Validate input
    if "file" not in request.files:
        return jsonify({"error": "PDF file is required"}), 400

    section_text = request.form.get("section_text")
    if not section_text:
        return jsonify({"error": "section_text is required"}), 400

    uploaded_file = request.files["file"]
    filename = uploaded_file.filename

    if not filename or not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # 2️⃣ Temp path using UPLOADED filename
    temp_pdf_path = os.path.join(tempfile.gettempdir(), filename)

    # 3️⃣ Close Acrobat if same PDF already open
    kill_acrobat_if_pdf_open(filename)
    time.sleep(0.5)  # allow Windows to release lock

    # 4️⃣ Delete existing temp file (if any)
    if os.path.exists(temp_pdf_path):
        try:
            os.remove(temp_pdf_path)
        except PermissionError:
            return jsonify({
                "error": "PDF is currently locked and cannot be replaced"
            }), 500

    # 5️⃣ Save uploaded PDF
    uploaded_file.save(temp_pdf_path)

    # 6️⃣ Find section page
    doc = fitz.open(temp_pdf_path)
    page_number = None

    for i, page in enumerate(doc):
        if section_text.lower() in page.get_text().lower():
            page_number = i + 1
            break

    doc.close()

    if page_number is None:
        return jsonify({"error": "Section not found"}), 404

    # 7️⃣ Open PDF in Adobe at detected page
    subprocess.Popen([
        ADOBE_PATH,
        "/A",
        f"page={page_number}",
        temp_pdf_path
    ])

    time.sleep(1)
    return jsonify({
        "message": "PDF opened successfully in Adobe Acrobat",
        "page": page_number,
        "file": filename
    })


if __name__ == "__main__":
    app.run(debug=True)
