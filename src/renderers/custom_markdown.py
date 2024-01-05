"""
File: custom_markdown.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Format results as markdown in STDOUT.
"""

from rich.markdown import Markdown
from rich.console import Console

def render_code_list_as_markdown(objects):
    markdown_text = "# Object listing\n"
    for idx, obj in enumerate(objects, start=1):
        markdown_text += f"## Object {idx}\n{obj}\n"
    
    console = Console()
    console.print(Markdown(markdown_text))

