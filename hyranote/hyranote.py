import datetime
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

from hyranote.asciidoc_visitor import AsciidocVisitor
from hyranote.logging import Logging


class Generator(object):
    max_heading_level = 4
    image_suffixes = ['.png', '.jpg']
    retain_weeks = 2

    def __init__(self, data, configs):
        self.data = data
        self.current_week = configs.get('current_week')
        self.weeks = ['W%d' % (self.current_week - x) for x in range(self.retain_weeks)]
        self.quarter = f'Q{configs.get("current_quarter")}'
        self.output_dir = configs.get('output_dir')
        self.prefix = configs.get('prefix')
        self.author = configs.get('author')
        self.logger = Logging(configs.get('logging', Logging.LOG_WARN))
        self.visitor = AsciidocVisitor(self.logger)

        self.logger.info(self.weeks, self.quarter)

    def _filter_text(self, text: str) -> str:
        if not text:
            return ''

        doc = BeautifulSoup(text, features='html.parser')
        value = self.visitor.visit(doc.find())
        value = value.strip()
        return value

    def _print_child_node(self, node, fp, node_level=1):
        title = node.get('title', {}).get('text', '')
        title = self._filter_text(title)
        if title.startswith('[S]'):
            # Skip this node and its children
            return
        m = re.search(r'^W\d+', title)
        if m is not None:
            week_num = m.group(0)
            if week_num not in self.weeks:
                self.logger.info('skip', title)
                return
        m = re.search(r'^Q\d', title)
        if m is not None:
            week_num = m.group(0)
            if week_num != self.quarter:
                self.logger.info('skip quarter', title)
                return

        if node_level > 1:
            content = self._render_node_content(node, node_level, title)
            fp.write(content)

        subnodes = node.get('subnodes', [])
        for x in subnodes:
            self._print_child_node(x, fp, node_level+1)

    def _render_node_content(self, node, node_level, title):
        note = node.get('note', {}).get('text', '')
        note = self._filter_text(note)
        if len(note) > 0:
            note = note + '\n\n'
        if node_level <= self.max_heading_level:
            content = f"\n{'=' * node_level} {title}\n\n{note}"
            return content

        attachment_name = self._get_attachment_name(node)
        if attachment_name:
            content = self._render_image_block(attachment_name, title)
            return content

        task_state = node.get('task', {}).get('state', 0)
        if task_state == 1:
            title = '[ ] ' + title
        if task_state == 2:
            title = '[x] ' + title
        bullet_level = '*' * (node_level - self.max_heading_level)
        content = f"{bullet_level} {title}\n{note}"
        return content

    def _get_attachment_name(self, node):
        attachment_file_name = node.get('attachment', {}).get('fileName', '')
        default_name = ''
        if attachment_file_name:
            ext = Path(attachment_file_name).suffix
            if ext in self.image_suffixes:
                return attachment_file_name

        return default_name

    def _render_image_block(self, image_content, title):
        title = title.strip()
        if not title:
            return f'''+
image::{image_content}[pdfwidth=85%]
'''
        else:
            return f'''+
.{title.strip()}
image::{image_content}[alt={title.strip()}, pdfwidth=85%]
'''

    def generate(self):
        my_date = datetime.date.today()

        file_name = '_'.join([self.prefix, 'Notes', f'W{self.current_week}.asciidoc'])
        with open(os.path.join(self.output_dir, file_name), 'wt') as fp:
            fp.write(f'''= {self.prefix} Notes: W{self.current_week}
{self.author}
{my_date.strftime('%Y-%m-%d')}
:toc:
:toclevels: 4
:imagesdir: images
:numbered:
''')
            mn = self.data['mainNode']
            self._print_child_node(mn, fp)
