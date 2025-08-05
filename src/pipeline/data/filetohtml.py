import os
import re

from subprocess import Popen

try:
    from tika import detector, parser

    TIKA = True
except ImportError:
    TIKA = False

try:
    from docling.document_converter import DocumentConverter

    DOCLING = True
except ImportError:
    DOCLING = False

from ..base import Pipeline

class FileToHTML(Pipeline):
    def __init__(self, backend="available"):
        backend = backend.lower() if backend else None

        if backend == "available":
            backend = "tika" if Tika.available() else "docling" if Docling.available() else None

        self.backend = Tika() if backend == "tika" else Docling() if backend == "docling" else None

    def __call__(self, path):
        return self.backend(path) if self.backend else None
    
class Tika:
    @staticmethod
    def available():
        path = os.environ.get("TIKA_JAVA", "java")

        try:
            _ = Popen(path, stdout=open(os.devnull, "w"), stderr=open(os.devnull, "w"))
        except:
            return False
        
    def __init__(self):
        if not Tika.available():
            raise ImportError("tika is not available install 'Tika'")
        
    def __call__(self, path):
        mimetype = detector.from_file(path)
        if mimetype in ("text/plain", "text/html", "text/xhtml"):
            return None
        
        parsed = parser.from_file(path, xmlContent=True)
        return parsed["content"]
    
class Docling:
    @staticmethod
    def available():
        return DOCLING
    
    def __init__(self):
        if not Docling.available():
            raise ImportError("Docling is not available - install 'Docling' ")
        
        self.converter = DocumentConverter()

    def __call__(self, path):
        if self.ishtml(path):
            return None
        
        html = self.converter.convert(path).document.export_to_html(html_head="<head/>")

        return self.normalize(html)
    
    def ishtml(self, path):
        with open(path, "rb") as f:
            content = f.read(1024)
            content = content.decode("ascii", errors="ignore").lower().strip()

            return re.search(r"<!doctype\s+html|<html|<head|<body", content)
        
    def normalize(self, html):
        html = html.replace("<head/>", "<head/><body>").replace("</html>", "</body></html>") if "<body>" not in html else html

        html = re.sub(r"<li>\xb7 ", r"<li>", html)

        return html.replace("</p>", "</p><p/>")