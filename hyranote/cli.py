import argparse
from hyranote.cmd_simple import simple_generate_contents
from hyranote.cmd_dump import dump_contents
from hyranote.cmd_generate import generate_contents
from hyranote.logging import Logging


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

    g_parser = dump_command.add_parser('simple', aliases=['s', 'sim'], help='Generate weekly notes from MindNode file in simplify format')
    g_parser.add_argument('input', type=str, help='Input MindNode file')
    g_parser.add_argument('output', nargs='?', type=str, help='Output folder', default='.')
    g_parser.add_argument('--author', type=str, help='Render author field', default='')
    g_parser.add_argument('--verbose', type=int, help='Logging level: 1-INFO, 2-WARN, 3-ERROR', default=Logging.LOG_WARN)
    g_parser.set_defaults(func=simple_generate_contents)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
