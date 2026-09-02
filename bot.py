import os
import json
import telebot
import google.generativeai as genai

# Read secrets from environment variables (safe and secure)
TELEGRAM_BOT_TOKEN = "8945870305:AAEYyQB0jsQ7UC1KgDM8fyX14DyVfTlhfzA"
GEMINI_API_KEY = "AQ.Ab8RN6KseNJ8w72MQHkjHYNSCeoioau4z5bwj-4W_-56uW33Vg"

genai.configure(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

HTML_TEMPLATE_START = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JEE Mains Practice Test</title>
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; color: #1f2937; padding: 20px; }
    .page { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    .header { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; padding: 25px; border-radius: 10px; margin-bottom: 30px; text-align: center; }
    .header h1 { font-size: 24px; margin-bottom: 8px; }
    .question-block { margin-bottom: 25px; page-break-inside: avoid; border-bottom: 1px solid #f1f5f9; padding-bottom: 20px; }
    .question-text { font-size: 15px; line-height: 1.6; margin-bottom: 15px; display: flex; gap: 10px; }
    .q-num { font-weight: 700; color: #7c3aed; font-size: 16px; }
    .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .option { display: flex; align-items: center; background: #f8fafc; padding: 10px 14px; border-radius: 8px; border-left: 4px solid #cbd5e1; font-size: 14px; }
    .option:nth-child(1) { border-left-color: #ef4444; }
    .option:nth-child(2) { border-left-color: #3b82f6; }
    .option:nth-child(3) { border-left-color: #10b981; }
    .option:nth-child(4) { border-left-color: #f59e0b; }
    .opt-letter { font-weight: 700; background: #e2e8f0; color: #475569; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; border-radius: 4px; margin-right: 10px; font-size: 12px; }
    .answer-key-section { margin-top: 40px; padding-top: 20px; border-top: 2px dashed #cbd5e1; }
    .answer-key-title { font-size: 18px; color: #4f46e5; margin-bottom: 15px; text-align: center; font-weight: bold; }
    .answer-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
    .ans-item { background: #1e293b; color: white; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; }
    @media print { body { background: white; padding: 0; } .page { box-shadow: none; max-width: 100%; } }
</style>
</head>
<body>
<div class="page">
    <div class="header">
        <h1>JEE Mains Grand Practice Paper</h1>
        <p>Subject: Physics / Math | Full Syllabus</p>
    </div>
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me any JEE PDF, and I will instantly return it restyled in your custom vibrant theme!")

@bot.message_handler(content_types=['document'])
def handle_pdf(message):
    if not message.document.file_name.endswith('.pdf'):
        bot.reply_to(message, "Please upload a valid .pdf file.")
        return

    status_msg = bot.reply_to(message, "Processing your PDF with AI... Please wait 15-30 seconds.")
    temp_input_pdf = f"/tmp/{message.document.file_name}"
    output_html_name = f"styled_{message.document.file_name.replace('.pdf', '.html')}"
    temp_output_html = f"/tmp/{output_html_name}"

    try:
        # Download the file from Telegram
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(temp_input_pdf, 'wb') as f:
            f.write(downloaded_file)

        # Upload and extract via Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        uploaded_doc = genai.upload_file(path=temp_input_pdf)
        
        prompt = """
        Extract all multiple-choice questions from this document.
        Return strictly as a JSON array of objects with keys:
        "q" (question text with LaTeX for formulas), "a", "b", "c", "d" (options text/math), and "ans" (correct option letter).
        Do not wrap with markdown other than json.
        """
        response = model.generate_content([uploaded_doc, prompt])
        
        # Clean JSON
        clean_json_str = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json_str)

        # Assemble HTML
        questions_html = ""
        answers_html = ""
        for i, item in enumerate(data):
            q_num = i + 1
            questions_html += f"""
            <div class="question-block">
                <div class="question-text">
                    <span class="q-num">Q{q_num}.</span>
                    <span>{item.get('q', '')}</span>
                </div>
                <div class="options-grid">
                    <div class="option"><span class="opt-letter">A</span> {item.get('a', '-')}</div>
                    <div class="option"><span class="opt-letter">B</span> {item.get('b', '-')}</div>
                    <div class="option"><span class="opt-letter">C</span> {item.get('c', '-')}</div>
                    <div class="option"><span class="opt-letter">D</span> {item.get('d', '-')}</div>
                </div>
            </div>
            """
            if 'ans' in item and item['ans']:
                answers_html += f'<div class="ans-item">{q_num}. {item["ans"]}</div>'

        full_html = HTML_TEMPLATE_START + questions_html
        if answers_html:
            full_html += f"""
            <div class="answer-key-section">
                <div class="answer-key-title">ANSWER KEY</div>
                <div class="answer-grid">{answers_html}</div>
            </div>
            """
        full_html += "</div></body></html>"

        with open(temp_output_html, "w", encoding="utf-8") as f:
            f.write(full_html)

        # Send back the styled file
        with open(temp_output_html, "rb") as f:
            bot.send_document(
                message.chat.id, 
                f, 
                caption="Here is your restyled test paper! Tap to open, then select 'Share > Print > Save as PDF'."
            )
        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_input_pdf): os.remove(temp_input_pdf)
        if os.path.exists(temp_output_html): os.remove(temp_output_html)

bot.infinity_polling()
