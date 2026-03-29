import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List

class HtmlParser:
    def __init__(self, url: str):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def get_html(self) -> str:
        response = requests.get(self.url, headers=self.headers)
        return response.text

    def parse_html(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.text
        meta_tags = soup.find_all('meta')
        meta_dict = {}
        for tag in meta_tags:
            meta_dict[tag.get('name')] = tag.get('content')
        return {
            'title': title,
            'meta': meta_dict
        }

    def extract_links(self, html: str) -> List:
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a')
        link_list = []
        for link in links:
            link_list.append(link.get('href'))
        return link_list

    def extract_images(self, html: str) -> List:
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all('img')
        image_list = []
        for image in images:
            image_list.append(image.get('src'))
        return image_list

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        return text

    def extract_tables(self, html: str) -> List:
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        table_list = []
        for table in tables:
            table_list.append(table.get_text())
        return table_list

    def extract_forms(self, html: str) -> List:
        soup = BeautifulSoup(html, 'html.parser')
        forms = soup.find_all('form')
        form_list = []
        for form in forms:
            form_list.append(form.get('action'))
        return form_list

    def extract_scripts(self, html: str) -> List:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        script_list = []
        for script in scripts:
            script_list.append(script.get('src'))
        return script_list

    def extract_styles(self, html: str) -> List:
        soup = BeautifulSoup(html, 'html.parser')
        styles = soup.find_all('style')
        style_list = []
        for style in styles:
            style_list.append(style.get('href'))
        return style_list

    def extract_css(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        styles = soup.find_all('style')
        css = ''
        for style in styles:
            css += style.get_text()
        return css

    def extract_js(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        js = ''
        for script in scripts:
            js += script.get_text()
        return js

    def extract_json(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        json_dict = {}
        for script in scripts:
            if script.get('type') == 'application/json':
                json_dict = json.loads(script.get_text())
        return json_dict

    def extract_xml(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        xml = ''
        for script in scripts:
            if script.get('type') == 'application/xml':
                xml += script.get_text()
        return xml

    def extract_xslt(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        xslt = ''
        for script in scripts:
            if script.get('type') == 'application/xslt+xml':
                xslt += script.get_text()
        return xslt

    def extract_xquery(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        xquery = ''
        for script in scripts:
            if script.get('type') == 'application/xquery+xml':
                xquery += script.get_text()
        return xquery