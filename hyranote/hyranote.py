import datetime
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

from hyranote.asciidoc_visitor import AsciidocVisitor
from hyranote.logging import Logging


class BaseGenerator(object):
    max_heading_level = 4
    image_suffixes = ['.png', '.jpg']

    def __init__(self, data, configs):
        self.data = data
        self.output_dir = configs.get('output_dir')
        self.author = configs.get('author')
        self.logger = Logging(configs.get('logging', Logging.LOG_WARN))
        self.visitor = AsciidocVisitor(self.logger)

    def _filter_text(self, text: str) -> str:
        if not text:
            return ''

        doc = BeautifulSoup(f'<div>{text}</div>', features='html.parser')
        value = self.visitor.visit(doc.find())
        value = value.strip()
        return value

    def _visit_node(self, node, fp, node_level=1):
        pass

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

    def _generate_metadata(self, title, metadata, fp):
        fp.write(f'''= {title}
{self.author}
{metadata}
''')

    def _get_output_file_path(self) -> str:
        pass

    def _get_output_title(self) -> str:
        pass

    def _get_output_metadata(self) -> str:
        return f''':toc:
:toclevels: {self.max_heading_level}
:imagesdir: images
:numbered:'''

    def generate(self):
        output_file_path = self._get_output_file_path()
        with open(output_file_path, 'wt') as fp:
            self._generate_metadata(self._get_output_title(), self._get_output_metadata(), fp)
            mn = self.data['mainNode']
            self._visit_node(mn, fp)


class Generator(BaseGenerator):
    max_heading_level = 4
    image_suffixes = ['.png', '.jpg']

    def __init__(self, data, configs):
        super(Generator, self).__init__(data, configs)
        self.current_week = configs.get('current_week')
        prev_week = configs.get('previous_week')
        self.weeks = [f'W{prev_week}', f'W{self.current_week}']
        self.quarter = f'Q{configs.get("current_quarter")}'
        self.prefix = configs.get('prefix')
        self.visitor = AsciidocVisitor(self.logger)

        self.logger.info(self.weeks, self.quarter)

    def _visit_node(self, node, fp, node_level=1):
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
            quarter = m.group(0)
            if quarter != self.quarter:
                self.logger.info('skip quarter', title)
                return

        if node_level > 1:
            content = self._render_node_content(node, node_level, title)
            fp.write(content)

        subnodes = node.get('subnodes', [])
        for x in subnodes:
            self._visit_node(x, fp, node_level + 1)

    def _get_output_file_path(self):
        file_name = '_'.join([self.prefix, 'Notes', f'W{self.current_week}.asciidoc'])
        file_path = os.path.join(self.output_dir, file_name)
        return file_path

    def _get_output_title(self) -> str:
        return f'{self.prefix} Notes: W{self.current_week}'

    def _get_output_metadata(self) -> str:
        my_date = datetime.date.today()
        return f'''{my_date.strftime('%Y-%m-%d')}
{super(Generator, self)._get_output_metadata()}
'''


class SimpleGenerator(BaseGenerator):
    max_heading_level = 3
    image_suffixes = ['.png', '.jpg']

    def __init__(self, data, configs):
        super(SimpleGenerator, self).__init__(data, configs)
        self.output_basename = os.path.splitext(os.path.basename(configs.get('input')))[0]

    def _visit_node(self, node, fp, node_level=1):
        title = node.get('title', {}).get('text', '')
        title = self._filter_text(title)
        if title.startswith('[S]'):
            # Skip this node and its children
            return

        if node_level > 1:
            content = self._render_node_content(node, node_level, title)
            fp.write(content)

        subnodes = node.get('subnodes', [])
        for x in subnodes:
            self._visit_node(x, fp, node_level + 1)

    def _get_output_file_path(self):
        file_name = f'{self.output_basename}.asciidoc'
        file_path = os.path.join(self.output_dir, file_name)
        return file_path

    def _get_output_title(self) -> str:
        mn = self.data['mainNode']
        title = mn.get('title', {}).get('text', '')
        title = self._filter_text(title)
        return title

