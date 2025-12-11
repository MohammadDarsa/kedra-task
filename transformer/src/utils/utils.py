import hashlib
from bs4 import BeautifulSoup

def process_html_content(content):
    soup = BeautifulSoup(content, 'html.parser')
    
    # remove navigation, headers, footers (just in case)
    for tag in soup(['nav', 'header', 'footer', 'script', 'style']):
        tag.decompose()

    # the main content based on observations are inside this div
    content_div = soup.find('div', class_='col-sm-9')
    if content_div:
        return str(content_div).encode('utf-8')
        
    if soup.body:
        return str(soup.body).encode('utf-8')
    return str(soup).encode('utf-8')

def calculate_hash(content):
    # uses sha256 to calculate hash
    return hashlib.sha256(content).hexdigest()
