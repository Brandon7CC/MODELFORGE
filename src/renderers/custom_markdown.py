"""
File: custom_markdown.py

Author: Brandon Dalton
Organization: Swiftly Detecting

Description: Format results as markdown in STDOUT.
"""

from rich.markdown import Markdown
from rich.console import Console
from datetime import datetime


def render_and_write_code_list_as_markdown(objects, save=False):
    markdown_text = "# Object listing\n"
    for idx, obj in enumerate(objects, start=1):
        markdown_text += f"## Object {idx}\n{obj}\n"

    console = Console()
    console.print(Markdown(markdown_text))

    if save:
        with open(f'results_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.md',
                  'w') as f:
            f.write(markdown_text)


# def return_text_as_markdown(objects):
#     markdown_text = "# Object listing\n"
#     for idx, obj in enumerate(objects, start=1):
#         markdown_text += f"## Object {idx}\n{obj}\n"
#     return markdown_text
