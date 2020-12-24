import os
import plistlib


def dump_contents(args):
    import json

    input_dir = os.path.expanduser(args.input)
    with open(os.path.join(input_dir, 'contents.xml'), 'rb') as fp:
        data = plistlib.load(fp)

    with open('contents.json', 'wt') as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
