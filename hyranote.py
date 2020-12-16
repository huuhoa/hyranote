import argparse
import datetime
import os
import plistlib
import re


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
    def __init__(self, data, configs):
        self.data = data
        self.current_week = configs.get('current_week')
        self.retain_weeks = 2
        self.weeks = ['W%d' % (self.current_week - x) for x in range(self.retain_weeks)]
        self.quarter = f'Q{configs.get("current_quarter")}'
        self.output_dir = configs.get('output_dir')
        self.prefix = configs.get('prefix')
        self.author = configs.get('author')
        self.logger = Logging(configs.get('logging', Logging.LOG_WARN))

        self.logger.info(self.weeks, self.quarter)

    def print_child_node(self, node, fp, node_level=1):
        max_heading_level = 4
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
        note = node.get('note', {}).get('text', '')
        note = re.sub('<[^>]*>', '', note)
        if len(note) > 0:
            note = note + '\n\n'
        task_state = node.get('task', {}).get('state', 0)

        if node_level <= max_heading_level:
            content = f"\n{'=' * node_level} {title}\n\n{note}"
        else:
            if task_state == 1:
                title = '[ ] ' + title
            if task_state == 2:
                title = '[x] ' + title
            content = f"{'*' * (node_level-max_heading_level)} {title}\n{note}"
        if node_level > 1:
            fp.write(content)
        subnodes = node.get('subnodes')
        if subnodes is not None:
            for x in subnodes:
                self.print_child_node(x, fp, node_level+1)

    def generate(self):
        my_date = datetime.date.today()

        file_name = '_'.join([self.prefix, f'W{self.current_week}', 'Notes.asciidoc'])
        with open(os.path.join(self.output_dir, file_name), 'wt') as fp:
            fp.write(f'''= {self.prefix} W{self.current_week} - Notes
{self.author}
{my_date.strftime('%Y-%m-%d')}
:toc:
:toclevels: 4
''')
            mn = self.data['mainNode']
            self.print_child_node(mn, fp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='Input mindnode file')
    parser.add_argument('output', nargs='?', type=str, help='Output folder', default='.')
    parser.add_argument('--prefix', type=str, help='Prefix value for output file name and title', default='')
    parser.add_argument('--author', type=str, help='Render author field', default='')
    parser.add_argument('--verbose', type=int, help='Logging level: 1-INFO, 2-WARN, 3-ERROR', default=Logging.LOG_WARN)
    args = parser.parse_args()

    input_dir = os.path.expanduser(args.input)
    with open(os.path.join(input_dir, 'contents.xml'), 'rb') as fp:
        data = plistlib.load(fp)

    # import json
    # with open('contents.json', 'wt') as fh:
    #     json.dump(data, fh, indent=2, sort_keys=True)
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


if __name__ == '__main__':
    main()
