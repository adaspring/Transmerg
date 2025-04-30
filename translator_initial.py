import os
import json
import re
import requests
from identification import HTMLTranslationProcessor, sanitize_html
from bs4 import BeautifulSoup

# Configuration
TRANSLATION_MEMORY = "translation_db.json"
TARGET_LANG = "fr"
INJECT_HEAD_FILE = "inject_head.html"
INJECT_BODY_FILE = "inject_body.html"

PATTERNS = {
    r"(\d+) BCE": r"\1 av. J.-C.",
    r"(\d+) CE": r"\1 ap. J.-C.",
    r"Back to Top": "Retour en haut",
    r"Nok Terracottas": "Terres cuites Nok"
}

SERVERS = [
    "https://translate.argosopentech.com",
    "https://libretranslate.de",
    "https://libretranslate.com",
    "https://translate.astian.org",
]

def load_memory():
    if os.path.exists(TRANSLATION_MEMORY):
        with open(TRANSLATION_MEMORY, 'r', encoding='utf-8') as f:
            return json.load(f)
    print("No memory found. Creating new translation memory...")
    return {}

def save_memory(memory):
    with open(TRANSLATION_MEMORY, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def local_translate(text, memory):
    for pattern, replacement in PATTERNS.items():
        text = re.sub(pattern, replacement, text)
    return memory.get(text.strip(), None)

def api_translate(text):
    payload = {
        "q": text,
        "source": "en",
        "target": TARGET_LANG,
        "format": "text"
    }
    headers = {"Content-Type": "application/json"}

    for server in SERVERS:
        try:
            response = requests.post(f"{server}/translate", json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("translatedText", text)
        except Exception as e:
            print(f"Server {server} failed: {e}")
            continue

    print("All LibreTranslate servers failed. Returning original text.")
    return text

def inject_html(html_content):
    head_injection = ""
    body_injection = ""

    if os.path.exists(INJECT_HEAD_FILE):
        with open(INJECT_HEAD_FILE, 'r', encoding='utf-8') as f:
            head_injection = f.read()

    if os.path.exists(INJECT_BODY_FILE):
        with open(INJECT_BODY_FILE, 'r', encoding='utf-8') as f:
            body_injection = f.read()

    if head_injection:
        html_content = html_content.replace("</head>", f"{head_injection}\n</head>")

    if body_injection:
        html_content = html_content.replace("</body>", f"{body_injection}\n</body>")

    return html_content

def restore_translations(processed_html, translation_data, translated_texts):
    soup = BeautifulSoup(processed_html, 'html.parser')

    for entry, new_text in zip(translation_data, translated_texts):
        placeholder = f"<!-- TRANSLATION_ID_{entry['id']} -->"

        if entry["type"] == "text":
            for element in soup.find_all(string=placeholder):
                element.replace_with(new_text)
        elif entry["type"] == "attribute":
            for element in soup.find_all(entry["context"]["tag"]):
                attr = entry["attribute"]
                if element.has_attr(attr) and element[attr] == placeholder:
                    element[attr] = new_text
                    break

    return str(soup)

def translate_html(input_file):
    memory = load_memory()
    output_file = input_file.replace('.html', f'-{TARGET_LANG}.html')

    if os.path.exists(output_file):
        print(f"File already exists, skipping: {output_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        raw_html = f.read()

    processor = HTMLTranslationProcessor()
    sanitized_html = sanitize_html(raw_html)
    extracted = processor.extract_translatable(sanitized_html)

    translation_data = extracted['translation_data']
    translated_texts = []

    for entry in translation_data:
        original = entry['content']
        translated = local_translate(original, memory)
        if not translated:
            translated = api_translate(original)
            memory[original] = translated
        translated_texts.append(translated)

    translated_html = restore_translations(extracted['processed_html'], translation_data, translated_texts)

    soup = BeautifulSoup(translated_html, 'html.parser')

    if soup.html:
        soup.html['lang'] = TARGET_LANG

    for a in soup.find_all('a', href=True):
        if a['href'].endswith('.html') and f"-{TARGET_LANG}" not in a['href']:
            a['href'] = a['href'].replace('.html', f'-{TARGET_LANG}.html')

    final_html = str(soup)
    final_html = inject_html(final_html)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"Translated and saved: {output_file}")
    save_memory(memory)

def main():
    for file in os.listdir('.'):
        if file.endswith('.html') and f'-{TARGET_LANG}' not in file:
            translate_html(file)

    print("✅ All files processed successfully.")

if __name__ == "__main__":
    main()
