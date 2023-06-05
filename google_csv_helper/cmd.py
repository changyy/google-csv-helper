# -*- encoding: utf-8 -*-
import sys
import argparse
import datetime

from google_csv_helper import * 

def main():
    def valid_date(data: str):
        output = datetime.date.today()
        if data != "today":
            try:
                return datetime.datetime.strptime(data, "%Y-%m-%d")
            except ValueError:
                raise argparse.ArgumentTypeError(f"not a valid date: {data}")
        return output
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_dir", nargs="*", type=str, help="the directory where the csv file is located")
    parser.add_argument("--output", choices=['json', 'markdown'], default='json', help="results format")
    parser.add_argument("--report", choices=['date', 'week', 'month'], default='date', help="the report type")
    parser.add_argument("--debug", action="store_true", default=False, help="output the debug messages")
    parser.add_argument("--version", action="store_true", default=False, help="show the version")
    parser.add_argument("--enddate", default="today", type=valid_date, help="date for csv key field filter")
    parser.add_argument("--adsense-filename-keyword", type=str, default="adsense", help="the keyword on csv filename of adsense")
    parser.add_argument("--admob-filename-keyword", type=str, default="admob", help="the keyword on csv filename of admob")
    parser.add_argument("--ga-csv-filename-keyword", type=str, default="ga", help="the keyword on csv filename of gogle anayltics")

    csv_filename_pattern = []
    args = parser.parse_args()

    for p in args.adsense_filename_keyword.split(','):
        csv_filename_pattern.append( str(p).strip() )
    for p in args.admob_filename_keyword.split(','):
        csv_filename_pattern.append( str(p).strip() )

    if args.version:
        print(version)
        sys.exit(0)

    if len(args.csv_dir) == 0:
        parser.print_help()
        sys.exit(0)

    obj = adsense_csv_helper.AdsenseCSVHelper(args.csv_dir)

    if args.debug:
        obj.enableDebug()
    obj.readAllCSVRawFile()

    if args.output == 'markdown':
        if args.report == 'date':
            print("## Current:")
            print(obj.getDailyMarkDownReport(args.enddate, csv_filename_pattern))
            print("## Previuos:")
            print(obj.getDailyMarkDownReport(args.enddate.replace(day=1), csv_filename_pattern))
    else:
        if args.report == 'date':
            print(obj.getAllJSONResult())

if __name__ == '__main__':
    main()
