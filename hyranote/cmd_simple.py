import os
import plistlib

from hyranote.hyranote import SimpleGenerator
from hyranote.hutil import copy_resources


def simple_generate_contents(args):
    input_dir = os.path.expanduser(args.input)
    copy_resources(input_dir, os.path.join(args.output, 'images'))
    with open(os.path.join(input_dir, 'contents.xml'), 'rb') as fp:
        data = plistlib.load(fp)

    canvas = data['canvas']
    mind_maps = canvas['mindMaps']
    for main_node in mind_maps:
        generator = SimpleGenerator(main_node,
                              {
                                  'input': args.input,
                                  'output_dir': args.output,
                                  'author': args.author,
                                  'logging': args.verbose,
                              })
        generator.generate()
