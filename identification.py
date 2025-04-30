import re
from bs4 import BeautifulSoup

class HTMLTranslationProcessor:
    def extract_translatable(self, html_content):
        """
        Extracts all translatable content from the HTML, including text and attributes.
        Returns a dictionary containing 'translation_data' and 'processed_html'.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        translation_data = []
        processed_html = html_content
        
        # Process all text content
        for text_element in soup.find_all(text=True):
            if text_element.strip():  # Avoid processing empty or whitespace text
                placeholder = f"<!-- TRANSLATION_ID_{hash(text_element)} -->"
                translation_data.append({
                    'id': hash(text_element),
                    'type': 'text',
                    'content': text_element,
                    'placeholder': placeholder,
                })
                text_element.replace_with(placeholder)
        
        # Process all attributes
        for tag in soup.find_all(True):  # True will match all tags
            for attr in tag.attrs:
                if isinstance(tag[attr], str) and tag[attr].strip():
                    placeholder = f"<!-- TRANSLATION_ID_{hash(tag[attr])} -->"
                    translation_data.append({
                        'id': hash(tag[attr]),
                        'type': 'attribute',
                        'content': tag[attr],
                        'placeholder': placeholder,
                        'context': {
                            'tag': tag.name,
                            'attribute': attr
                        }
                    })
                    tag[attr] = placeholder
        
        processed_html = str(soup)
        return {'translation_data': translation_data, 'processed_html': processed_html}


def sanitize_html(html_content):
    """
    Sanitizes the HTML content (if needed).
    In this case, we're assuming that we do not need special sanitation,
    but it could be expanded as necessary.
    """
    # Perform sanitization steps if needed (e.g., removing unwanted tags or attributes)
    return html_content
