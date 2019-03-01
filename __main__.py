#!/usr/bin/env python
from argparse import ArgumentParser
from lp import Parser

description = 'Parses Lviv Polytechnic National University\'s timetables'

arg_parser = ArgumentParser(description=description)
arg_parser.add_argument('-f', '--file',
    type=str, dest='file_path', default=False,
    help='output results to passed file path; '
         'if --multi or --iterative passed, '
         'creates files in format \'{institute}_{group}.json\' in '
         'the FILE_PATH firectory')
arg_parser.add_argument('-i', '--iterative',
    action='store_true', dest='iterative_output', default=False,
    help='enables iterative output; files are right after parsing')
arg_parser.add_argument('-m', '--multi',
    action='store_true', dest='multi_file', default=False,
    help='multi file output; works only when FILE_PATH is passed')
arg_parser.add_argument('-q', '--quet',
    action='store_true', dest='silent_mode', default=False,
    help='supress all logs')
arg_parser.add_argument('-v', '--verbose',
    action='store_true', dest='verbose_mode', default=False,
    help='output all values, has an effect if -q or --quet is not set')
arg_parser.add_argument('--pretty',
    action='store_true', dest='pretty_output', default=False,
    help='pretty output to console and/or files')
args = arg_parser.parse_args()

lp_parser = Parser(options=vars(args))
lp_parser.run()
