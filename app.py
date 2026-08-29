from flask import Flask, render_template, request, jsonify
import ollama
from pypdf import PdfReader
from ddgs import DDGS
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

riwayat = [
    {
        "role": "system",
        "content": """
        Kamu adalah AI assistant bernama Jo.
        Kamu ramah, sopan, dan membantu.
        Jawab dalam bahasa Indonesia yang jelas dan mudah dipahami.
        """
    }
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/clear", methods=["POST"])
def clear():
    global riwayat

    riwayat = [
        {
            "role": "system",
            "content": """
            Kamu adalah AI assistant bernama Jo.
            Kamu ramah, sopan, dan membantu.
            Jawab dalam bahasa Indonesia yang jelas dan mudah dipahami.
            """
        }
    ]

    return jsonify({"success": True})


@app.route("/chat", methods=["POST"])
def chat():

    pertanyaan = request.form.get("message", "")
    file = request.files.get("pdfFile")

    isi_pdf = ""
    file_path = None
    jenis_file = None

    # =========================
    # MEMBACA FILE
    # =========================

    if file and file.filename:

        nama_file = file.filename
        ekstensi = os.path.splitext(nama_file)[1].lower()

        file_path = os.path.join(
            UPLOAD_FOLDER,
            nama_file
        )

        file.save(file_path)

        # PDF
        if ekstensi == ".pdf":
            jenis_file = "pdf"

            try:
                reader = PdfReader(file_path)

                for page in reader.pages:
                    text = page.extract_text() or ""
                    isi_pdf += text + "\n"

                if not isi_pdf.strip():
                    isi_pdf = "PDF tidak memiliki teks yang dapat diekstrak. Kemungkinan PDF berupa hasil scan/gambar."

            except Exception as e:
                isi_pdf = f"PDF gagal dibaca: {e}"

        # GAMBAR
        elif ekstensi in [".jpg", ".jpeg", ".png", ".webp"]:
            jenis_file = "image"


    # =========================
    # JIKA ADA GAMBAR
    # =========================

    if jenis_file == "image":

        try:
            response = ollama.chat(
                model="llama3.2-vision",
                messages=[
                    {
                        "role": "user",
                        "content": pertanyaan if pertanyaan else "Jelaskan gambar ini.",
                        "images": [file_path]
                    }
                ]
            )

            jawaban = response["message"]["content"]

        except Exception as e:
            jawaban = f"Jo mengalami masalah saat membaca gambar: {e}"


    # =========================
    # JIKA ADA PDF
    # =========================

    elif jenis_file == "pdf":

        prompt = f"""
Pertanyaan pengguna:
{pertanyaan}

Berikut adalah isi PDF yang diberikan pengguna:

{isi_pdf[:15000]}

Jawablah pertanyaan berdasarkan isi PDF tersebut.
Jika informasi yang ditanyakan tidak terdapat dalam PDF,
katakan dengan jujur bahwa informasinya tidak ditemukan.
"""

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=[
                    *riwayat,
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            jawaban = response["message"]["content"]

        except Exception as e:
            jawaban = f"Jo mengalami masalah saat membaca PDF: {e}"


    # =========================
    # CHAT BIASA
    # =========================

    else:

        riwayat.append({
            "role": "user",
            "content": pertanyaan
        })

        try:
            response = ollama.chat(
                model="llama3.2",
                messages=riwayat
            )

            jawaban = response["message"]["content"]

            riwayat.append({
                "role": "assistant",
                "content": jawaban
            })

        except Exception as e:
            jawaban = f"Terjadi kesalahan: {e}"


    # Hapus file sementara
    #if file_path and os.path.exists(file_path):
        #os.remove(file_path)

    return jsonify({
        "reply": jawaban
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)