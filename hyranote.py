import argparse
import datetime
import os
import plistlib
import re
from pathlib import Path
import shutil


def get_current_week():
    my_date = datetime.date.today()
    year, week_num, day_of_week = my_date.isocalendar()
    return week_num, int((my_date.month+2) / 3)


def _wrap_with_color_code(code: str):
    def inner(self, text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)

    return inner


class Logging(object):
    def __init__(self, level: int):
        self.log_level = level

    LOG_INFO = 1
    LOG_WARN = 2
    LOG_ERROR = 3

    red = _wrap_with_color_code('31')
    green = _wrap_with_color_code('32')
    yellow = _wrap_with_color_code('33')
    blue = _wrap_with_color_code('34')
    magenta = _wrap_with_color_code('35')
    cyan = _wrap_with_color_code('36')
    white = _wrap_with_color_code('37')

    def error(self, msg, *args, **kwargs):
        if self.log_level <= self.LOG_ERROR:
            print(self.red("[ERROR]"), msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        if self.log_level <= self.LOG_WARN:
            print(self.yellow("[WARN]"), msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        if self.log_level <= self.LOG_INFO:
            print(self.green("[INFO]"), msg, *args, **kwargs)


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

        self.logger.info(self.weeks, self.quarter)

    def _print_child_node(self, node, fp, node_level=1):
        title = node.get('title', {}).get('text', '')
        title = re.sub('<[^>]*>', '', title)
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
        note = re.sub('<[^>]*>', '', note)
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


def copy_resources(input_dir, dst):
    resources = os.path.join(input_dir, 'resources')
    shutil.copytree(resources, dst, dirs_exist_ok=True)


def dump_contents(args):
    import json

    input_dir = os.path.expanduser(args.input)
    with open(os.path.join(input_dir, 'contents.xml'), 'rb') as fp:
        data = plistlib.load(fp)

    with open('contents.json', 'wt') as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def generate_contents(args):
    input_dir = os.path.expanduser(args.input)
    copy_resources(input_dir, os.path.join(args.output, 'images'))
    with open(os.path.join(input_dir, 'contents.xml'), 'rb') as fp:
        data = plistlib.load(fp)

    canvas = data['canvas']
    mind_maps = canvas['mindMaps']
    for main_node in mind_maps:
        week_num, quarter = get_current_week()
        generator = Generator(main_node,
                              {
                                  'current_week': week_num,
                                  'current_quarter': quarter,
                                  'output_dir': args.output,
                                  'prefix': args.prefix,
                                  'author': args.author,
                                  'logging': args.verbose,
                              })
        generator.generate()


def main():
    parser = argparse.ArgumentParser(description='Hyranote to generate weekly notes for you')
    dump_command = parser.add_subparsers(title="Dump contents")
    d_parser = dump_command.add_parser("dump", help='Dump content of MindNode file to json and exit')
    d_parser.add_argument('input', type=str, help='Input MindNode file')
    d_parser.set_defaults(func=dump_contents)

    g_parser = dump_command.add_parser('generate', aliases=['g', 'gen'], help='Generate weekly notes from MindNode file')
    g_parser.add_argument('input', type=str, help='Input MindNode file')
    g_parser.add_argument('output', nargs='?', type=str, help='Output folder', default='.')
    g_parser.add_argument('--prefix', type=str, help='Prefix value for output file name and title', default='')
    g_parser.add_argument('--author', type=str, help='Render author field', default='')
    g_parser.add_argument('--verbose', type=int, help='Logging level: 1-INFO, 2-WARN, 3-ERROR', default=Logging.LOG_WARN)
    g_parser.set_defaults(func=generate_contents)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
