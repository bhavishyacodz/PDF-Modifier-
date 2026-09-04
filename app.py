import os, json, base64, requests, telebot

# PASTE YOUR API KEYS HERE
TELEGRAM_BOT_TOKEN = "8945870305:AAEYyQB0jsQ7UC1KgDM8fyX14DyVfTlhfzA"
GEMINI_API_KEY = "AQ.Ab8RN6LG2n8Wo-G_Xp76vEmW-rXc36XLICcLpEzsSFhqv9IVmw"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

HTML_START = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>JEE Practice</title><script>MathJax = {tex: {inlineMath: [['$', '$']]}};</script><script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script><script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:sans-serif;background:#f0f2f5;padding:20px}.page{max-width:800px;margin:0 auto;background:#fff;padding:30px;border-radius:12px}.header{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:25px;border-radius:10px;margin-bottom:30px;text-align:center}.question-block{margin-bottom:25px;border-bottom:1px solid #f1f5f9;padding-bottom:20px}.question-text{font-size:15px;margin-bottom:15px;display:flex;gap:10px}.q-num{font-weight:700;color:#7c3aed}.options-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.option{display:flex;align-items:center;background:#f8fafc;padding:10px;border-radius:8px;border-left:4px solid #cbd5e1}.option:nth-child(1){border-color:#ef4444}.option:nth-child(2){border-color:#3b82f6}.option:nth-child(3){border-color:#10b981}.option:nth-child(4){border-color:#f59e0b}.opt-letter{font-weight:700;background:#e2e8f0;padding:2px 8px;border-radius:4px;margin-right:10px}.ans-key{margin-top:40px;text-align:center}</style></head><body><div class="page"><div class="header"><h1>JEE Mains Paper</h1></div>"""


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send a JEE PDF to get started!")

@bot.message_handler(content_types=['document'])
def handle_pdf(message):
    if not message.document.file_name.lower().endswith('.pdf'):
        bot.reply_to(message, "Please send a .pdf file.")
        return
    msg = bot.reply_to(message, "Processing PDF with AI... Please wait 15-30s.")
    in_pdf = f"/tmp/{message.document.file_name}"
    out_html = f"/tmp/{message.document.file_name}.html"
    try:
        f_info = bot.get_file(message.document.file_id)
        d_file = bot.download_file(f_info.file_path)
        with open(in_pdf, 'wb') as f:
            f.write(d_file)
        with open(in_pdf, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = "Extract multiple-choice questions. Return strictly as a JSON array of objects with keys: 'q' (question with LaTeX), 'a', 'b', 'c', 'd' (options), and 'ans' (correct letter). Do not wrap with markdown."
        payload = {"contents":[{"parts":[{"text":prompt},{"inline_data":{"mime_type":"application/pdf","data":pdf_data}}]}],"generationConfig":{"responseMimeType":"application/json"}}
        resp = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        if resp.status_code != 200:
            raise Exception(resp.text)
        data = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"].replace('```json', '').replace('```', '').strip())
        q_html, a_html = "", ""
        for i, item in enumerate(data):
            q_html += f"<div class='question-block'><div class='question-text'><span class='q-num'>Q{i+1}.</span><span>{item.get('q','')}</span></div><div class='options-grid'><div class='option'><span class='opt-letter'>A</span> {item.get('a','')}</div><div class='option'><span class='opt-letter'>B</span> {item.get('b','')}</div><div class='option'><span class='opt-letter'>C</span> {item.get('c','')}</div><div class='option'><span class='opt-letter'>D</span> {item.get('d','')}</div></div></div>"
            if item.get('ans'): a_html += f"<b>{i+1}.</b> {item['ans']} &nbsp;&nbsp;|&nbsp;&nbsp; "
        full = HTML_START + q_html + f"<div class='ans-key'><h2>Answer Key</h2><br><p>{a_html}</p></div></div></body></html>"
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(full)
        with open(out_html, "rb") as f:
            bot.send_document(message.chat.id, f, caption="✅ Ready! Tap to open, then Share > Print > Save as PDF.")
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(in_pdf): os.remove(in_pdf)
        if os.path.exists(out_html): os.remove(out_html)

print("Bot is running...")
bot.infinity_polling()
