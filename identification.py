import re
from bs4 import BeautifulSoup, Comment

def sanitize_html(html):
    """Sanitize HTML by removing problematic declarations and normalizing whitespace."""
    html = re.sub(r'<!DOCTYPE[^>]+>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<\?xml[^>]+\?>', '', html)
    html = re.sub(r'\s+', ' ', html)
    return html.strip()

class HTMLTranslationProcessor:
    def __init__(self):
        self.counter = 0

    def _generate_id(self):
        self.counter += 1
        return self.counter

    def extract_translatable(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        translation_data = []

        for element in soup.find_all(text=True):
            text = element.strip()
            if text and not isinstance(element, Comment):
                parent = element.parent
                if parent.name not in ['script', 'style', 'noscript']:
                    entry_id = self._generate_id()
                    placeholder = f"<!-- TRANSLATION_ID_{entry_id} -->"
                    translation_data.append({
                        "id": entry_id,
                        "type": "text",
                        "content": text
                    })
                    element.replace_with(placeholder)

        for tag in soup.find_all(True):
            for attr in ['title', 'alt', 'placeholder']:
                if tag.has_attr(attr):
                    content = tag[attr].strip()
                    if content:
                        entry_id = self._generate_id()
                        placeholder = f"<!-- TRANSLATION_ID_{entry_id} -->"
                        translation_data.append({
                            "id": entry_id,
                            "type": "attribute",
                            "attribute": attr,
                            "content": content,
                            "context": {"tag": tag.name}
                        })
                        tag[attr] = placeholder

        return {
            "processed_html": str(soup),
            "translation_data": translation_data
        }
