from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from google import genai
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("PERINGATAN: GEMINI_API_KEY belum diatur.")

MODEL = "gemini-3.7-flash"

SYSTEM_PROMPT = """
Kamu adalah AI assistant bernama Jo.

Kamu ramah, sopan, dan membantu.
Jawab dalam bahasa Indonesia yang jelas dan mudah dipahami.
Jika pengguna meminta penjelasan, berikan langkah-langkah yang mudah diikuti.
Jangan mengarang informasi jika kamu tidak mengetahuinya.
"""

riwayat = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/clear", methods=["POST"])
def clear():
    global riwayat

    riwayat = []

    return jsonify({
        "success": True
    })


def tanya_gemini(prompt):

    if not client:
        return "API key Gemini belum diatur di server."

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT
        }
    )

    return response.text




@app.route("/chat", methods=["POST"])
def chat():

    global riwayat

    pertanyaan = request.form.get("message", "").strip()
    file = request.files.get("pdfFile")

    

    if not pertanyaan and not file:
        return jsonify({
            "reply": "Silakan tulis pertanyaan atau pilih file terlebih dahulu."
        })

    isi_pdf = ""
    file_path = None
    jenis_file = None

    


    if file and file.filename:

        nama_asli = os.path.basename(file.filename)
        ekstensi = os.path.splitext(nama_asli)[1].lower()

        nama_file = f"{uuid.uuid4().hex}{ekstensi}"

        file_path = os.path.join(
            UPLOAD_FOLDER,
            nama_file
        )

        file.save(file_path)

        
        if ekstensi == ".pdf":

            jenis_file = "pdf"

            try:

                reader = PdfReader(file_path)

                for page in reader.pages:
                    text = page.extract_text() or ""
                    isi_pdf += text + "\n"

                if not isi_pdf.strip():

                    isi_pdf = (
                        "PDF tidak memiliki teks yang dapat diekstrak. "
                        "Kemungkinan PDF berupa hasil scan atau gambar."
                    )

            except Exception as e:

                isi_pdf = f"PDF gagal dibaca: {e}"


        elif ekstensi in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]:

            jenis_file = "image"



    if jenis_file == "image":

        jawaban = (
            "Fitur membaca gambar belum diaktifkan pada versi online Jo. "
            "Untuk sekarang Jo dapat membaca PDF dan menjawab chat."
        )



        python
    elif jenis_file == "pdf":

        prompt = f"""
Pertanyaan pengguna:

{pertanyaan if pertanyaan else "Jelaskan isi PDF ini."}

ISI PDF:

{isi_pdf[:30000]}

INSTRUKSI:

1. Jawab berdasarkan isi PDF.
2. Jika informasi tidak ditemukan di PDF, katakan dengan jujur.
3. Jangan mengarang informasi.
4. Gunakan bahasa Indonesia yang jelas.
5. Jika pertanyaan membutuhkan perhitungan, kerjakan langkah demi langkah.
"""

        try:
            jawaban = tanya_gemini(prompt)
        except Exception as e:
            jawaban = f"Jo mengalami masalah saat membaca PDF: {e}"

    else:

        if not pertanyaan:
            return jsonify({
                "reply": "Silakan tulis pertanyaan terlebih dahulu."
            })

        riwayat.append({
            "role": "user",
            "content": pertanyaan
        })

        riwayat_terakhir = riwayat[-10:]

        percakapan = "\n\n".join(
            [
                (
                    f"Pengguna: {item['content']}"
                    if item["role"] == "user"
                    else f"Jo: {item['content']}"
                )
                for item in riwayat_terakhir
            ]
        )

        prompt = f"""
Berikut percakapan sebelumnya:

{percakapan}

Jawab pesan terakhir pengguna dengan ramah,
jelas, dan mudah dipahami.
"""

        try:
            jawaban = tanya_gemini(prompt)

            riwayat.append({
                "role": "assistant",
                "content": jawaban
            })

        except Exception as e:
            jawaban = f"Terjadi kesalahan saat menghubungi Gemini: {e}"



    if file_path and os.path.exists(file_path):

        try:
            os.remove(file_path)
        except Exception:
            pass


    return jsonify({
        "reply": jawaban
    })



if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )