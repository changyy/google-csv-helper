# -*- encoding: utf-8 -*-
import os
import sys
import argparse
import datetime
import json

from google_csv_helper import __version__
from google_csv_helper import adsense_csv_helper
from google_csv_helper import ga3_csv_helper
from google_csv_helper import ga4_csv_helper
from google_csv_helper.google_common import *

def main():
    def valid_date(data: str):
        output = datetime.date.today()
        if data != "today":
            try:
                dt = datetime.datetime.strptime(data, "%Y-%m-%d")
                return datetime.date(dt.year, dt.month, dt.day)
            except ValueError:
                raise argparse.ArgumentTypeError(f"not a valid date: {data}")
        return output
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_dir", nargs="*", type=str, help="the directory where the csv file is located")
    parser.add_argument("--output", choices=['json', 'markdown'], default='markdown', help="results format")
    parser.add_argument("--output-type", choices=['adsense', 'ga3', 'ga4'], default="adsense", help="the report")
    parser.add_argument("--output-chart-columns", type=str, default="", help="specify which CSV columns to plot, identified by field names (multiple fields separated by commas)")
    parser.add_argument("--output-chart-detailed-columns", action="store_true", default=False, help="specify which CSV columns to plot with detailed information (multiple fields separated by commas)")
    parser.add_argument("--output-chart-list-columns", action="store_true", default=False, help="lst available CSV columns that can be used for plotting")
    parser.add_argument("--output-chart-plot-config", type=str, default='{"height": 10}', help="configure additional plot settings such as colors, width, height, etc.")
    parser.add_argument("--report", choices=['date', 'week', 'month'], default='date', help="the report type")
    parser.add_argument("--debug", action="store_true", default=False, help="output the debug messages")
    parser.add_argument("--version", action="store_true", default=False, help="show the version")
    parser.add_argument("--enddate", default="today", type=valid_date, help="date for csv key field filter, date format = 'YYYY-mm-dd'")
    parser.add_argument("--adsense-filename-keyword", type=str, default="adsense", help="the keyword on csv filename of adsense")
    parser.add_argument("--admob-filename-keyword", type=str, default="admob", help="the keyword on csv filename of admob")
    parser.add_argument("--ga-filename-keyword", type=str, default="ga", help="the keyword on csv filename of gogle anayltics")
    parser.add_argument("--google-project-setup-config", type=str, default=".google_client_secret.apps.googleusercontent.com.json", help="google project info")
    parser.add_argument("--google-token-file", type=str, default=".google_account_token", help="setup the token file for google adsense/admob login")
    parser.add_argument("--google-show-report-list", action="store_true", default=False, help="Show Google Adsense Saved Report")
    parser.add_argument("--google-query-data-range", type=DateRangeType(), default='MONTH_TO_DATE', help="Specific date range for AdSense/Admob report: MONTH_TO_DATE, TODAY, YESTERDAY, MONTH_TO_DATE, YEAR_TO_DATE, LAST_7_DAYS, LAST_30_DAYS, YYYYmmdd-YYYYmmdd")
    parser.add_argument("--google-adsense-saved-report-name", type=str, default=None, help="Specific AdSense Saved Report Name to export csv content")
    parser.add_argument("--google-adsense-latest-csv", action="store_true", default=False, help="Get AdSense latest daily report csv content")
    parser.add_argument("--google-admob-latest-csv", action="store_true", default=False, help="Get AdMob latest daily Report to csv content")

    csv_filename_pattern = []
    args = parser.parse_args()

    if args.google_show_report_list:
        checkOauth, credentials, messages = googleProjectSetupCheck(args.google_project_setup_config, args.google_token_file)
        if checkOauth == False:
            print(f'[ERROR] googleProjectSetupCheck: {messages}')
            sys.exit(1)
        queryStatus, queryResult, queryMessage = getGoogleAdsenseSavedReportList(getGoogleAdsenseService(credentials))
        if queryStatus == False:
            print(f'[ERROR] getGoogleAdsenseSavedReportList: {queryMessage}')
            sys.exit(1)
        print(json.dumps(queryResult, indent = 4))
        sys.exit(0)

    if args.google_adsense_saved_report_name:
        checkOauth, credentials, messages = googleProjectSetupCheck(args.google_project_setup_config, args.google_token_file)
        if checkOauth == False:
            print(f'[ERROR] googleProjectSetupCheck: {messages}')
            sys.exit(1)
        queryStatus, queryResult, queryMessage = getGoogleAdsenseSavedReportList(getGoogleAdsenseService(credentials))
        if queryStatus == False:
            print(f'[ERROR] getGoogleAdsenseSavedReportList: {queryMessage}')
            sys.exit(1)
        savedReportList = queryResult
        
        foundSaveReportItem = None
        for item in savedReportList:
            if foundSaveReportItem:
                break
            if item['name'] == args.google_adsense_saved_report_name:
                foundSaveReportItem = item
            elif item['title'].find(args.google_adsense_saved_report_name) != -1:
                foundSaveReportItem = item
 
        if foundSaveReportItem == None:
            print(f'[ERROR] getGoogleAdsenseSavedReportList not found: {args.google_adsense_saved_report_name}')
            sys.exit(1)
        queryOption = {
            'reportId': foundSaveReportItem['name'],
            'dateRange': 'MONTH_TO_DATE',
            'currencyCode' : 'USD', 
        }
        if args.google_query_data_range['mode'] == 'PREDEFINED':
            queryOption['dateRange'] = args.google_query_data_range['input']
        else:
            queryOption['dateRange'] = 'CUSTOM'
            for field in ['startDate_year', 'startDate_month', 'startDate_day', 'endDate_year', 'endDate_month', 'endDate_day']:
                queryOption[field] = args.google_query_data_range[field]
        queryStatus, queryResult, queryMessage = getGoogleAdsenseReport(getGoogleAdsenseService(credentials), query = queryOption)
        if not queryStatus:
            print(f'[ERROR] getGoogleAdsenseReport: {queryMessage}')
            sys.exit(1)
        queryStatus, queryResult, queryMessage = listToCSVFormat(queryResult)
        if not queryStatus:
            print(f'[ERROR] listToCSVFormat: {queryMessage}')
            sys.exit(1)
        print(queryResult)
        sys.exit(0)
    elif args.google_adsense_latest_csv:
        checkOauth, credentials, messages = googleProjectSetupCheck(args.google_project_setup_config, args.google_token_file)
        if checkOauth == False:
            print(f'[ERROR] googleProjectSetupCheck: {messages}')
            sys.exit(1)
 
        queryOption = {
            'dateRange': 'MONTH_TO_DATE',
            'currencyCode' : 'USD', 
        }
        if args.google_query_data_range['mode'] == 'PREDEFINED':
            queryOption['dateRange'] = args.google_query_data_range['input']
        else:
            queryOption['dateRange'] = 'CUSTOM'
            for field in ['startDate_year', 'startDate_month', 'startDate_day', 'endDate_year', 'endDate_month', 'endDate_day']:
                queryOption[field] = args.google_query_data_range[field]

        queryStatus, queryResult, queryMessage = getGoogleAdsenseReport(getGoogleAdsenseService(credentials), query = queryOption)
        if not queryStatus:
            print(f'[ERROR] getGoogleAdsenseReport: {queryMessage}')
            sys.exit(1)
        queryStatus, queryResult, queryMessage = listToCSVFormat(queryResult)
        if not queryStatus:
            print(f'[ERROR] listToCSVFormat: {queryMessage}')
            sys.exit(1)
        print(queryResult)
        sys.exit(0)
    elif args.google_admob_latest_csv:
        checkOauth, credentials, messages = googleProjectSetupCheck(args.google_project_setup_config, args.google_token_file)
        if checkOauth == False:
            print(f'[ERROR] googleProjectSetupCheck: {messages}')
            sys.exit(1)
 
        queryOption = {
            'dateRange': 'MONTH_TO_DATE',
            'currencyCode' : 'USD', 
        }
        #if args.google_query_data_range['mode'] == 'PREDEFINED':
        #    queryOption['dateRange'] = args.google_query_data_range['input']
        #else:
        if True:
            queryOption['dateRange'] = 'CUSTOM'
            for field in ['startDate_year', 'startDate_month', 'startDate_day', 'endDate_year', 'endDate_month', 'endDate_day']:
                queryOption[field] = args.google_query_data_range[field]

        queryStatus, queryResult, queryMessage = getGoogleAdmobReport(getGoogleAdmobService(credentials), query = queryOption)
        if not queryStatus:
            print(f'[ERROR] getGoogleAdsenseReport: {queryMessage}')
            sys.exit(1)
        queryStatus, queryResult, queryMessage = listToCSVFormat(queryResult)
        if not queryStatus:
            print(f'[ERROR] listToCSVFormat: {queryMessage}')
            sys.exit(1)
        print(queryResult)
        sys.exit(0)

    if args.version:
        print(__version__)
        sys.exit(0)

    if len(args.csv_dir) == 0:
        parser.print_help()
        sys.exit(0)

    obj = None
    if args.output_type == 'adsense':
        for p in args.adsense_filename_keyword.split(','):
            csv_filename_pattern.append( str(p).strip() )
        for p in args.admob_filename_keyword.split(','):
            csv_filename_pattern.append( str(p).strip() )
        obj = adsense_csv_helper.AdsenseCSVHelper(args.csv_dir, csv_filename_pattern)
    elif args.output_type == 'ga3':
        for p in args.ga_filename_keyword.split(','):
            csv_filename_pattern.append( str(p).strip() )
        obj = ga3_csv_helper.GA3CSVHelper(args.csv_dir, csv_filename_pattern)
    elif args.output_type == 'ga4':
        for p in args.ga_filename_keyword.split(','):
            csv_filename_pattern.append( str(p).strip() )
        obj = ga4_csv_helper.GA4CSVHelper(args.csv_dir, csv_filename_pattern)

    if args.debug:
        obj.enableDebug()

    #obj.setImportCSVDuplicateRules('default', 'last')
    obj.readAllCSVRawFile()

    setup_output_chart = {
        'config' : { 
            'height': 10,
        }, 'columns': {
        }, 'debug': {
            'showCumulativeAverageChartColumnCandidates': args.output_chart_list_columns,
            'showEachCumulativeAverageColumnChart': args.output_chart_detailed_columns,
        }
    }
    if args.output_chart_columns != '':
        for fieldName in args.output_chart_columns.split(','):
            fieldName = fieldName.strip()
            if len(fieldName) == 0:
                continue
            setup_output_chart['columns'][fieldName] = fieldName
    if args.output_chart_plot_config != '' and args.output_chart_plot_config != '{}':
       try:
           test_json_value = json.loads(args.output_chart_plot_config)
           setup_output_chart['config'] = test_json_value
       except Exception as e:
           if args.debug:
               print(e)

    if args.output == 'markdown':
        if args.report == 'date':
            if args.output_type == 'adsense':
                print("## Current:")
                print(obj.getDailyMarkDownReport(args.enddate, csv_filename_pattern, setup_output_chart))
                print("## Previuos:")
                print(obj.getDailyMarkDownReport(args.enddate.replace(day=1), csv_filename_pattern, setup_output_chart))
            else:
                print("## Current:")
                print(obj.getDailyMarkDownReport(args.enddate, csv_filename_pattern))
                print("## Previuos:")
                print(obj.getDailyMarkDownReport(args.enddate - datetime.timedelta(days=7), csv_filename_pattern))
    else:
        if args.report == 'date':
            print(obj.getAllJSONResult())

if __name__ == '__main__':
    main()
