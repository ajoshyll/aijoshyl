import ollama

print("🤖 AI CHATBOT")
print("Ketik 'keluar' untuk berhenti.\n")

riwayat = []

while True:
    pertanyaan = input("Kamu: ")

    if pertanyaan.lower() == "keluar":
        print("AI: Sampai jumpa!")
        break

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

        print("AI:", jawaban)

        riwayat.append({
            "role": "assistant",
            "content": jawaban
        })

    except Exception as e:
        print("Error:", e)