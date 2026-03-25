from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import os
import tempfile
import requests
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__, static_folder=None)

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
    
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Failed to download PDF: {str(e)}"}), 400
    
    pdf_bytes = response.content
    size_mb = len(pdf_bytes) / (1024 * 1024)

    if size_mb <= 25:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")  # FAST
    else:
        temp_pdf_path = os.path.join(tempfile.gettempdir(), filename)
        # -------- Remove old temp file --------
        if os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except PermissionError:
                return jsonify({"error": "PDF is locked and cannot be replaced"}), 500

        # -------- Download PDF --------
        with open(temp_pdf_path, "wb") as f:
            f.write(response.content)    
        doc = fitz.open(temp_pdf_path)

    # # -------- Find section page --------
    # page_number = None

    # for i, page in enumerate(doc):
    #     if section_text.lower() in page.get_text().lower():
    #         page_number = i + 1
    #         break

    # -------- Find section page and coordinates --------
    page_number = None
    coords = None

    for i, page in enumerate(doc):
        matches = page.search_for(section_text)  # NO flags

        if matches:
            page_number = i + 1
            rect = matches[0]

            coords = {
                "x0": rect.x0,
                "y0": rect.y0,
                "x1": rect.x1,
                "y1": rect.y1,
                "width": rect.width,
                "height": rect.height,
            }
            break

    doc.close()

    if page_number is None:
        return jsonify({"error": "Section not found"}), 404

    return jsonify({
        "message": "Page number rendered",
        "page": page_number,
        "file": filename,
        'coords' : coords
        # 'pdf_url' : pdf_url,
        # 'temp_path' : temp_pdf_path
    })


# ================== RUN ==================

if __name__ == "__main__":
    app.run(debug=True)
