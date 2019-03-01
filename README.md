# LP Parser

Parses Lviv Polytechnic National University's timetables from
http://www.lp.edu.ua/students_schedule

## Requirements

- Python 3
- Beautiful Soup 4 (`bs4`)
- `requests`

See more in `requirements.txt`

## How to use

To start script execute the current package like following

```sh
python .
```

and pass all the necessary options.

---

To get help execute the script like `python . --help`.
You will see the following:

```
usage: . [-h] [-f FILE_PATH] [-i] [-m] [-q] [-v] [--pretty]

Parses Lviv Polytechnic National University's timetables

optional arguments:
  -h, --help            show this help message and exit
  -f FILE_PATH, --file FILE_PATH
                        output results to passed file path; if --multi or
                        --iterative passed, creates files in format
                        '{institute}_{group}.json' in the FILE_PATH firectory
  -i, --iterative       enables iterative output; files are right after
                        parsing
  -m, --multi           multi file output; works only when FILE_PATH is passed
  -q, --quet            supress all logs
  -v, --verbose         output all values, has an effect if -q or --quet is
                        not set
  --pretty              pretty output to console and/or files
```

### Examples

### Run script to store each timetable in separate JSON file

```sh
python . -imf data --pretty
```

All results are stored in passed directory (in the example `data`).
In the each file additionaly stored group name in field `"group"` and
institute (faculty) name in field `"faculty"`.

Options:

- `--pretty` allows you to have readable JSON files _(optional)_
- `--multi` improves performance by writing all file right after parsing

### Run script to store each timetable in a single JSON file

```sh
python . -f lp.json --pretty
```

All results are stored in passed file (in the example `lp.json`).
The file is an array of parsed timetables.

## API

`lp.py` exposes class `Parser`. See short usage example in `__main__.py`.

Class `Parser` basically has following methods:

- `run()` — starts parsing entire website.
  It fetches all the groups and then one by one parses timetables.
  It's long process because there are about **1000 groups to parse**.
- `get_group_list()` – parses full groups list from the website and returns
  list of dicts in format `{ group, institute }`
- `get_parser(group_list)` – returns generator that parses timetables for the
  passed list of groups and returns the result on each iteration
