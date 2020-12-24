import datetime
import os
import plistlib
import shutil

from hyranote.hyranote import Generator


def get_current_week():
    my_date = datetime.date.today()
    year, week_num, day_of_week = my_date.isocalendar()
    return week_num, int((my_date.month+2) / 3)


def copy_resources(input_dir, dst):
    resources = os.path.join(input_dir, 'resources')
    shutil.copytree(resources, dst, dirs_exist_ok=True)


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
