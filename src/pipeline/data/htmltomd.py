import re

try:
    from bs4 import BeautifulSoup, NavigableString

    SOUP = True
except ImportError:
    SOUP = False

from ..base import Pipeline

class HTMLToMarkdown(Pipeline):
    def __init__(self, paragraphs=False, sections=False):
        if not SOUP:
            raise ImportError("HTMLToMarkdown pipeline is not available - install 'beautifulsoup'")
        
        self.paragraphs = paragraphs
        self.sections = sections

    def __call__(self, html):
        soup = BeautifulSoup(html, features="html.parser")

        for script in soup.find_all(["script", "style"]):
            script.decompose()

        article = next((x for x in ["article", "main"] if soup.find(x)), None)

        nodes = []

        for node in soup.find_all(article if article else "body"):
            if not article or node.find("p"):
                nodes.append(self.process(node, article))

        return "\n".join(self.metadata(soup) + nodes) if nodes else self.default(soup)
    
    def process(self, node, article):
        if self.isheader(node):
            return self.header(node, article)
        
        if node.name in ("blockquote", "q"):
            return self.block(node)

        if node.name in ("ul", "ol"):
            return self.items(node, article)
        
        if node.name in ("code", "pre"):
            return self.code(node)
        
        if node.name == "table":
            return self.table(node, article)
        
        if node.name in ("aside", ) + (() if article else ("header", "footer")):
            return ""
        
        page = node.name and node.get("class") and "page" in node.get("class")

        children = self.children(node)

        if self.iscontainer(node, children):
            texts = [self.process(node, article) for node in children]
            text = "\n".join(text for text in texts if text or not article)

        else:
            text = self.text(node, article)

        return f"{text}\f" if page and self.sections else text
    
    def metadata(self, node):
        title = node.find("title")
        metadata = [f"**{title.text.strip()}**"] if title and title.text else []

        description = node.find("meta", attrs={"name": "description"})
        if description and description["content"]:
            metadata.append(f"\n*{description['content'].strip()}*")

        if metadata:
            metadata.append("\f" if self.sections else "\n\n")

        return metadata
    
    def default(self, soup):
        lines = []
        for line in soup.get_text().split("\n"):
            lines.append(f"\f{line}" if self.sections and re.search(r"^#+ ", line) else line)

        return "\n".join(lines)
    
    def text(self, node, article):
        items = self.children(node)
        items = items if items else [node]

        texts = []
        for x in items:
            target, text = x if x.name else node, x.text

            if text.strip():
                if target.name in ("b", "strong"):
                    text = f"**{text.strip()}** "
                elif target.name in ("i", "em"):
                    text = f"*{text.strip()}* "
                elif target.name == "a":
                    text = f"[{text.strip()}]({target.get('href')}) "
            
            texts.append(text)

        text = "".join(texts)

        text = self.articletext(node, text) if article else text

        text = text if node.name and text else text.strip()

        return text
    
    def header(self, node, article):
        level = "#" * int(node.name[1])
        text = self.text(node, article)

        level = f"\f{level}" if self.sections else f"\n{level}"

        return f"{level} {text.lstrip()}" if text.strip() else ""
    
    def block(self, node):
        text = "\n".join(f"> {x}" for x in node.text.strip().split("\n"))
        return f"{text}\n\n" if self.paragraphs else f"{text}\n"
    
    def items(self, node, article):
        elements = []
        for x, element in enumerate(node.find_all("li")):
            prefix = "-" if node.name == "ul" else f"{x + 1}."

            text = self.process(element, article)

            if text:
                elements.append(f"{prefix} {text}")

        return "\n".join(elements)
    
    def code(self, node):
        text = f"```\n{node.text.strip()}\n```"
        return f"{text}\n\n" if self.paragraphs else f"{text}\n"
    
    def table(self, node, article):
        elements, header = [], False

        rows = node.find_all("tr")
        for row in rows:
            columns = row.find_all(lambda tag: tag.name in ("th", "td"))

            elements.append(f"|{'|'.join(self.process(column, article) for column in columns)}")

            if not header and len(rows) > 1:
                elements.append(f"{'|---' * len(columns)}|")
                header = True

        return "\n".join(elements)
    
    def iscontainer(self, node, children):
        return children and (node.name in ("div", "body", "article") or not any(isinstance(x, NavigableString) for x in children))
    
    def children(self, node):
        if node.name and node.contents:
            return [node for node in node.contents if node.name or node.text.strip()]

        return None

    def articletext(self, node, text):
        valid = ("p", "th", "td", "li", "a", "b", "strong", "i", "em")

        valid = node.name in valid or (node.parent and node.parent.name in ("th", "td")) 

        text = text if (valid or self.isheader(node)) and not self.islink(node) else ""
        if text:
            text = text.replace("\xa0\n", "\n\n")

            if node.name == "p":
                text = f"{text.strip()}\n\n" if self.paragraphs else f"{text.strip()}\n"

        return text
    
    def isheader(self, node):
        return node.name in ("h1", "h2", "h3", "h4", "h5", "h6")
    
    def islink(self, node):
        link, parent = False, node
        while parent:
            if parent.name == "a":
                link = True
                break

            parent = parent.parent

        return link and node.parent.name not in ("th", "td")