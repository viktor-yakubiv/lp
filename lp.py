import os
import json
import pprint
import re
import requests
import sys
from bs4 import BeautifulSoup


def get_html_parser(url):
    """Makes a GET request and returns BeautifulSoup object as a result"""
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


# Parsers
# =======
# Work directly with BeautifulSoup and extract all the necessary data

def parse_select_options(soup, input_name):
    """Returns list of tuples where fisrt item is a value
    and second one is a caption"""
    selector = 'select[name={}]'.format(input_name)
    options = [
        (option['value'], ''.join(option.contents).strip())
        for option in soup.select_one(selector).children
    ]
    return options

def parse_lesson(soup):
    """Parses lesson metadata from part of HTML"""
    lesson_tag = soup.select_one('.group_content')
    lesson_details = [s.strip() for s in \
        str(lesson_tag.decode_contents(formatter="html5")).split('<br>')]

    name, teachers, rest_details = lesson_details[:3]
    teachers = filter(lambda s: s, \
        map(lambda s: s.strip(), teachers.split(',')))
    location, lesson_type = [s.strip() for s in rest_details.split('&nbsp;')]

    if len(location) > 1:  # skip ','
        room, building = [s.strip() for s in location.split(' ')][:2]
        location = {
            'room': room,
            'building': building,
        }
    else:
        location = None

    time_details = lesson_tag.parent['id'].split('_')
    week = ['full', 'chys', 'znam'].index(time_details[-1])
    subgroup = int(time_details[-2]) if len(time_details) > 2 else 0

    return {
        'name': name,
        'type': lesson_type,
        'teachers': teachers,
        'location': location,
        'week': week,
        'subgroup': subgroup,
    }

def parse_day(soup):
    """Parses lessons of a day from a part of HTML"""
    lessons = []
    for tag in soup.select('.stud_schedule'):
        number = int(tag.find_previous_sibling('h3').get_text())
        lesson = parse_lesson(tag)
        lessons.append((number, lesson))
    return lessons

def parse_timetable(soup):
    """Splits timetable to days and parses all of them"""
    days = []
    for tag in soup.select('.view-grouping'):
        name = tag.select_one('.view-grouping-header').get_text().strip()
        content = tag.select_one('.view-grouping-content')
        day = parse_day(content)
        days.append((name, day))
    return days


# Extractors
# ==========
# Get necessary impormation from timetable, such as unique teacher names,
# unique course names (themes) and lesson times

def extract_themes(timetable):
    """Extracts unique course names (themes) from a timetable"""
    added_lessons = set()
    lessons = []
    for lesson in timetable:
        key = '{} --- {}'.format(lesson['name'], lesson['format'])
        if key in added_lessons:
            continue
        added_lessons.add(key)
        lessons.append({
            'name': lesson['name'],
            'format': lesson['format'],
        })
    lessons.sort(key=lambda l: l['name'])
    return lessons

def extract_teachers(timetable):
    """Extracts unique teachers from a timetable"""
    added_teachers = set()
    teachers = []
    for lesson in timetable:
        for teacher in lesson['teachers']:
            key = teacher['full_name']
            if key in added_teachers:
                continue
            added_teachers.add(key)
            teachers.append(teacher)
    teachers.sort(key=lambda t: t['full_name'])
    return teachers

def extract_lesson_times(timetable):
    """Extracts lesson times from a timetable"""
    times = set()
    for lesson in timetable:
        times.add(lesson['lesson_time'])
    return list(times).sort()


# Transformers
# ============
# Convert parsed data to proper format

def transform_teacher(full_name):
    if not full_name:
        return None
    match = re.search(r'([\w\']+)\s*([\w\']\.?)?\s*([\w\']\.?)?', full_name)
    last, first, middle = match.groups()
    return {
        'full_name': full_name,
        'last_name': last,
        'fisrt_name': first,
        'middle_name': middle,
    }

def transform_timetable(week):
    day_map = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт']
    format_map = ['Лекція', 'Семінар', 'Практична', 'Лабораторна']

    timetable = []

    for day_name, day_lessons in week:
        day_index = day_map.index(day_name) + 1
        for lesson_time, lesson_meta in day_lessons:
            timetable.append({
                'name': lesson_meta['name'],
                'format': format_map.index(lesson_meta['type']) \
                    if lesson_meta['type'] in format_map \
                    else len(format_map),
                'teachers': list(map(transform_teacher, \
                    lesson_meta['teachers'])),
                'room_data': {
                    'housing': lesson_meta['location']['building'],
                    'room_num': lesson_meta['location']['room'],
                } if lesson_meta['location'] else lesson_meta['location'],
                'day': day_index,
                'lesson_time': lesson_time,
                'weeks': lesson_meta['week'],
                'subgroup': lesson_meta['subgroup'],
            })

    return timetable


class Parser:
    """Entry point of exwcutable.
    Object that stores global cnfiguration and a few options"""
    base_url = 'http://www.lp.edu.ua/students_schedule'
    input_name_institute = 'institutecode_selective'
    input_name_group = 'edugrupabr_selective'

    def __init__(self, base_url = None, options = {}):
        self.base_url = base_url or Parser.base_url
        self.options = {
            'silent_mode': False,
            'verbose_mode': False,
            'pretty_output': False,
            'multi_file': False,
            'iterative_output': False,
            'file_path': None,
        }
        self.options.update(options)

    def log_data(self, data, **kwargs):
        output = ''
        if self.options['pretty_output']:
            pp = pprint.PrettyPrinter(indent=2)
            output = pp.pformat(data)
        else:
            output = str(data)
        print(output, **kwargs)

    def log(self, message = '', output = None, **kwargs):
        if not self.options['silent_mode']:
            if not output:
                print(message)
                return
            if self.options['verbose_mode']:
                print(message)
                self.log_data(output, **kwargs)

    def format_url(self, institute = 'All', group = 'All'):
        query = {
            Parser.input_name_institute: institute,
            Parser.input_name_group: group,
        }
        query_str = '&'.join(['{}={}'.format(key, value) \
            for key, value in query.items()])

        return '{}?{}'.format(self.base_url, query_str)

    def get_group_list(self):
        self.log('Fetching institutes list from\n  {}'.format(self.base_url))
        soup = get_html_parser(self.base_url)
        institutes = parse_select_options(soup, Parser.input_name_institute)[1:]
        self.log('Fetched institutes list:', institutes)

        groups = []
        for institute_key, institute_name in institutes:
            url = self.format_url(institute_key)
            self.log('Fetching groups for {} from\n  {}' \
                .format(institute_key, url))
            soup = get_html_parser(url)
            institute_groups = parse_select_options(soup, \
                Parser.input_name_group)[1:]
            self.log('Fetched group list for {}' \
                .format(institute_key), institute_groups)
            groups.extend({
                'group': group_key,
                'institute': institute_key,
            } for group_key, _ in institute_groups)
        return groups

    def get_timetable(self, institute, group):
        url = self.format_url(institute, group)
        self.log('Fetching timetable for group {} at {} from\n  {}' \
            .format(group, institute, url))
        soup = get_html_parser(url)
        week = parse_timetable(soup)
        timetable = transform_timetable(week)
        result = {
            'teachers': extract_teachers(timetable),
            'themes': extract_themes(timetable),
            'lessons_times': extract_lesson_times(timetable),
            'lessons': timetable,
        }
        self.log('Fetched timetable group {} at {}' \
            .format(group, institute), result)
        return result

    def get_parser(self, group_list):
        for group in group_list:
            timetable = self.get_timetable(group['institute'], group['group'])
            result = {
                'faculty': group['institute'],
                'group': group['group'],
            }
            result.update(timetable)
            yield result

    def write(self, filepath, results = None):
        if not results:
            results = self.results

        def write_result(filename, result):
            with open(filename, 'w', encoding='utf8') as file:
                json.dump(result, file,
                    indent=2 if self.options['pretty_output'] else None,
                    ensure_ascii=False)
            self.log('Written {}'.format(filename))

        if self.options['multi_file']:
            if type(results) != list:
                results = [results]
            for result in results:
                if not os.path.exists(filepath):
                    os.mkdir(filepath)
                filename = os.path.join(filepath, \
                    '{}_{}.json'.format(result['institute'], result['group']))
                write_result(filename, result)
        else:
            write_result(filepath, results)

    def output(self, file=sys.stdout):
        self.log_data(self.results, file=file)

    def run(self):
        self.log('Fetching group list from\n  {}'.format(self.base_url))
        group_list = self.get_group_list()
        self.log('Fetched groups:', group_list)
        self.log()
        self.log('Found {} groups. Starting accumulation of data...' \
            .format(len(group_list)))

        results = []
        parser = self.get_parser(group_list)
        for result in parser:
            results.append(result)
            if self.options['iterative_output'] and self.options['file_path']:
                self.write(self.options['file_path'], result)
        self.results = results
