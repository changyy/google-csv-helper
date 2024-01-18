# -*- encoding: utf-8 -*-
import os
import sys
import pandas as pd
import datetime
import re
from io import StringIO
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# https://github.com/googleads/googleads-adsense-examples/tree/main/v2/python

class DateRangeType(object):
    def __init__(self):
        pass
    def __call__(self, value):
        if not value:
            raise KeyError('Cannot be empty')
        value = value.upper()
        output = { 'input': value, 'mode': 'PREDEFINED', 'startDate_year' : '', 'startDate_month': '', 'startDate_day': '', 'endDate_year': '', 'endDate_month': '', 'endDate_day': '' }
        targetDate = datetime.datetime.now()

        if value == 'TODAY':
            output['startDate_year'] = targetDate.year
            output['startDate_month'] = targetDate.month
            output['startDate_day'] = targetDate.day
            output['endDate_year'] = targetDate.year
            output['endDate_month'] = targetDate.month
            output['endDate_day'] = targetDate.day
        elif value == 'YESTERDAY':
            targetDate -= datetime.timedelta(days=1)
            output['startDate_year'] = targetDate.year
            output['startDate_month'] = targetDate.month
            output['startDate_day'] = targetDate.day
            output['endDate_year'] = targetDate.year
            output['endDate_month'] = targetDate.month
            output['endDate_day'] = targetDate.day
        elif value == 'MONTH_TO_DATE':
            output['startDate_year'] = targetDate.year
            output['startDate_month'] = targetDate.month
            output['startDate_day'] = 1
            output['endDate_year'] = targetDate.year
            output['endDate_month'] = targetDate.month
            output['endDate_day'] = targetDate.day
        elif value == 'YEAR_TO_DATE':
            output['startDate_year'] = targetDate.year
            output['startDate_month'] = 1
            output['startDate_day'] = 1
            output['endDate_year'] = targetDate.year
            output['endDate_month'] = targetDate.month
            output['endDate_day'] = targetDate.day
        elif value == 'LAST_7_DAYS':
            targetDate -= datetime.timedelta(days=1)
            output['endDate_year'] = targetDate.year
            output['endDate_month'] = targetDate.month
            output['endDate_day'] = targetDate.day
            targetDate -= datetime.timedelta(days=6)
            output['startDate_year'] = targetDate.year
            output['startDate_month'] = targetDate.month
            output['startDate_day'] = targetDate.day
        elif value == 'LAST_30_DAYS':
            targetDate -= datetime.timedelta(days=1)
            output['endDate_year'] = targetDate.year
            output['endDate_month'] = targetDate.month
            output['endDate_day'] = targetDate.day
            targetDate -= datetime.timedelta(days=29)
            output['startDate_year'] = targetDate.year
            output['startDate_month'] = targetDate.month
            output['startDate_day'] = targetDate.day
        else:
            output['mode'] = 'CUSTOM'
            pattern = re.compile(r'(\d{4})(\d{2})(\d{2})-(\d{4})(\d{2})(\d{2})')
            matches = pattern.match(value)
            if not matches:
                raise KeyError('Please use "YYYYmmdd-YYYYmmdd" format')
            startYear, startMonth, startDay, endYear, endMonth, endDay = matches.groups()
            output['startDate_year'] = int(startYear)
            output['startDate_month'] = int(startMonth)
            output['startDate_day'] = int(startDay)
            output['endDate_year'] = int(endYear)
            output['endDate_month'] = int(endMonth)
            output['endDate_day'] = int(endDay)
        return output

def googleProjectSetupCheck(configFilePath: str, tokenFilePath: str, oauthScopes: [str] = ['https://www.googleapis.com/auth/adsense.readonly', 'https://www.googleapis.com/auth/admob.readonly', 'https://www.googleapis.com/auth/admob.report']) -> (bool, Credentials, str):
    outputStatus = False
    outputCredentials = None
    outputMessasge = []
    if not os.path.exists(configFilePath):
        return (outputStatus, outputCredentials, f'configFilePath Not Found: {configFilePath}')
    if not tokenFilePath:
        return (outputStatus, outputCredentials, f'tokenFilePath is Empty: {tokenFilePath}')

    credentials = None
    if os.path.exists(tokenFilePath):
        try:
            credentials = Credentials.from_authorized_user_file(tokenFilePath)
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
        except Exception as e:
            outputMessasge.append(f'[ERROR] {e}')

    if not credentials or not credentials.valid or credentials.expired :
        flow = InstalledAppFlow.from_client_secrets_file(configFilePath, scopes=oauthScopes)
        credentials = flow.run_local_server(port=0)
        with open(tokenFilePath, "w") as token:
            token.write(credentials.to_json())

    if credentials and credentials.valid and not credentials.expired :
        outputCredentials = credentials
        outputStatus = True
    else:
        outputMessasge.append(f'[ERROR] not credentials or credentials.valid or credentials.expired ')

    return (outputStatus, outputCredentials, "\n".join(outputMessasge))


def getGoogleAdsenseService(credentials) -> Resource:
    return build('adsense', 'v2', credentials=credentials)

def getGoogleAdmobService(credentials) -> Resource:
    return build('admob', 'v1', credentials=credentials)

def getGoogleAccountsInfo(service: Resource):
    queryResult = service.accounts().list().execute()
    if 'account' in queryResult:
        return queryResult['account']
    if 'accounts' in queryResult:
        return queryResult['accounts']
    return []

def getGoogleAdsenseSavedReportList(service: Resource, googleAccountPubId: str = None, maxPageSize: int = 50) -> (bool, [], str):
    outputStatus = False
    outputReport = []
    outputMessage = []
    for accountInfo in getGoogleAccountsInfo(service):
        if 'name' not in accountInfo:
            continue
        if googleAccountPubId is not None:
            if accountInfo['name'].find(googleAccountPubId) == -1:
                continue
        #print(accountInfo['name'])
        try:
            queryResult = service.accounts().reports().saved().list(parent=accountInfo['name'], pageSize=maxPageSize).execute()
            if 'savedReports' in queryResult:
                for savedReport in queryResult['savedReports']:
                    try:
                        #print(savedReport)
                        outputReport.append({
                            'name': savedReport['name'],
                            'title': savedReport['title'] if 'title' in savedReport else 'Untitled',
                        })
                    except Exception as e:
                        outputMessage.append(f'[ERROR] {e}')
                #sorted(outputReport, key='name')
            outputStatus = True
        except Exception as e:
            outputMessage.append(f'[ERROR] {e}')

    return (outputStatus, outputReport, "\n".join(outputMessage))

#
# https://developers.google.com/adsense/management/reference/rest/v2/accounts.reports/generate
#
def getGoogleAdsenseReport(service: Resource, googleAccountPubId: str = None, query: dict = { 'reportId': None, 'dateRange': None, 'metrics': [], 'dimensions': [], 'orderBy': [], 'currencyCode': 'USD', }) -> (bool, [], []):
    outputStatus = False
    outputReport = []
    outputMessage = []

    if 'reportingTimeZone' not in query or not query['reportingTimeZone']:
        query['reportingTimeZone'] = 'ACCOUNT_TIME_ZONE'

    for field in ['currencyCode', 'reportingTimeZone']:
        if  field not in query or not query[field]:
            outputMessage.append(f'[ERROR] "{field}" not found')

    if len(outputMessage) > 0:
        return (outputStatus, outputReport, outputMessage)

    # https://github.com/googleapis/google-api-python-client/blob/main/googleapiclient/discovery.py
    if 'dateRange' not in query or not query['dateRange']:
        outputMessage.append(f'[ERROR] "dateRange" not found')
        return (outputStatus, outputReport, outputMessage)

    if query['dateRange'] == 'CUSTOM':
        checkPass = True
        for field in ['startDate_year', 'startDate_month', 'startDate_day', 'endDate_year', 'endDate_month', 'endDate_day']:
            if field not in query:
                checkPass = False
                outputMessage.append(f'[ERROR] "{field}" not found')
        if not checkPass:
            return (outputStatus, outputReport, outputMessage)
    else:
        # https://github.com/googleapis/google-api-python-client/blob/main/googleapiclient/discovery.py
        # TypeError: Parameter "dateRange" value "hello" is not an allowed value in "['REPORTING_DATE_RANGE_UNSPECIFIED', 'CUSTOM', 'TODAY', 'YESTERDAY', 'MONTH_TO_DATE', 'YEAR_TO_DATE', 'LAST_7_DAYS', 'LAST_30_DAYS']"
        pass

    for accountInfo in getGoogleAccountsInfo(service):
        if 'name' not in accountInfo:
            continue
        if googleAccountPubId is not None:
            if accountInfo['name'].find(googleAccountPubId) == -1:
                continue

        result = None
        try:
            if 'reportId' in query and query['reportId']:
                if query['dateRange'] != 'CUSTOM':
                    result = service.accounts().reports().saved().generate(
                        name = query['reportId'], dateRange = query['dateRange'],
                        currencyCode = query['currencyCode'], reportingTimeZone = query['reportingTimeZone'],
                    ).execute()
                else:
                    result = service.accounts().reports().saved().generate(
                        name = query['reportId'], dateRange= query['dateRange'],
                        startDate_year = query['startDate_year'], startDate_month = query['startDate_month'], startDate_day = query['startDate_day'],
                        endDate_year = query['endDate_year'], endDate_month = query['endDate_month'], endDate_day = query['endDate_day'],
                        currencyCode = query['currencyCode'], reportingTimeZone = query['reportingTimeZone'],
                    ).execute()
            else:
                if 'orderBy' not in query or not query['orderBy']:
                    query['orderBy'] = ['+DATE']
                # https://developers.google.com/adsense/management/reference/rest/v2/Metric
                if 'metrics' not in query or not query['metrics']:
                    query['metrics'] = ['ESTIMATED_EARNINGS', 'PAGE_VIEWS', 'PAGE_VIEWS_RPM', 'IMPRESSIONS', 'IMPRESSIONS_RPM', 'ACTIVE_VIEW_MEASURABILITY', 'CLICKS', 'IMPRESSIONS_CTR', 'COST_PER_CLICK'] #'CLICKS', 'COST_PER_CLICK', 'AD_REQUESTS_CTR', 'AD_REQUESTS', 'PAGE_VIEWS'] 
                if 'dimensions' not in query or not query['dimensions']:
                    query['dimensions'] = ['DATE']
                if query['dateRange'] != 'CUSTOM':
                    result = service.accounts().reports().generate(
                        account = accountInfo['name'],
                        dateRange = query['dateRange'],
                        metrics = query['metrics'],
                        dimensions = query['dimensions'],
                        orderBy = query['orderBy'],
                        currencyCode = query['currencyCode'], reportingTimeZone = query['reportingTimeZone'],
                    ).execute()
                else:
                    result = service.accounts().reports().generate(
                        account = accountInfo['name'],
                        dateRange = query['dateRange'],
                        startDate_year = query['startDate_year'], startDate_month = query['startDate_month'], startDate_day = query['startDate_day'],
                        endDate_year = query['endDate_year'], endDate_month = query['endDate_month'], endDate_day = query['endDate_day'],
                        metrics = query['metrics'],
                        dimensions = query['dimensions'],
                        orderBy = query['orderBy'],
                        currencyCode = query['currencyCode'], reportingTimeZone = query['reportingTimeZone'],
                    ).execute()
        except Exception as e:
            outputMessage.append(f'[ERROR] {e}')
        if result != None:
            outputStatus = True
            try:
                # https://github.com/googleads/googleads-adsense-examples/blob/main/v2/python/generate_report.py
                header = []
                for field in result['headers']:
                    header.append(field['name'])
                outputReport.append(header)
                if 'rows' in result:
                    for row in result['rows']:
                        item = []
                        for cell in row['cells']:
                            item.append(cell['value'])
                        outputReport.append(item)
            except Exception as e:
                outputMessage.append(f'[ERROR] {e}')
    return (outputStatus, outputReport, "\n".join(outputMessage))
#
# https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate?hl=zh-tw
# https://github.com/googleads/googleads-admob-api-samples/blob/main/python/v1/generate_network_report.py
# https://github.com/changyy/helper-study/blob/master/python3/admob-api/main.py
#
def getGoogleAdmobReport(service: Resource, googleAccountPubId: str = None, query: dict = { 'dateRange': None, 'metrics': [], 'dimensions': [], 'orderBy': [], 'currencyCode': 'USD', }) -> (bool, [], []):
    outputStatus = False
    outputReport = []
    outputMessage = []

    for field in ['currencyCode']: #, 'reportingTimeZone']:
        if  field not in query or not query[field]:
            outputMessage.append(f'[ERROR] "{field}" not found')
    if len(outputMessage) > 0:
        return (outputStatus, outputReport, outputMessage)

    # https://github.com/googleapis/google-api-python-client/blob/main/googleapiclient/discovery.py
    if 'dateRange' not in query or not query['dateRange']:
        outputMessage.append(f'[ERROR] "dateRange" not found')
        return (outputStatus, outputReport, outputMessage)

    #if query['dateRange'] != 'CUSTOM':
        # https://github.com/googleapis/google-api-python-client/blob/main/googleapiclient/discovery.py
        # TypeError: Parameter "dateRange" value "hello" is not an allowed value in "['REPORTING_DATE_RANGE_UNSPECIFIED', 'CUSTOM', 'TODAY', 'YESTERDAY', 'MONTH_TO_DATE', 'YEAR_TO_DATE', 'LAST_7_DAYS', 'LAST_30_DAYS']"

    checkPass = True
    for field in ['startDate_year', 'startDate_month', 'startDate_day', 'endDate_year', 'endDate_month', 'endDate_day']:
        if field not in query:
            checkPass = False
            outputMessage.append(f'[ERROR] "{field}" not found')
    if not checkPass:
        return (outputStatus, outputReport, outputMessage)

    for accountInfo in getGoogleAccountsInfo(service):
        if 'name' not in accountInfo:
            continue
        if googleAccountPubId is not None:
            if accountInfo['name'].find(googleAccountPubId) == -1:
                continue

        result = None
        try:
            if 'orderBy' not in query or not query['orderBy']:
                query['orderBy'] = ['+DATE']
            # https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate?hl=zh-tw#Metric
            if 'metrics' not in query or not query['metrics']:
                query['metrics'] = ['ESTIMATED_EARNINGS', 'CLICKS', 'AD_REQUESTS', 'IMPRESSIONS', 'IMPRESSION_CTR', 'IMPRESSION_RPM', 'SHOW_RATE'] 
            if 'dimensions' not in query or not query['dimensions']:
                query['dimensions'] = ['DATE']

            reportSpec = {
                'date_range': {
                    'start_date': { 'year': query['startDate_year'], 'month': query['startDate_month'], 'day': query['startDate_day']},
                    'end_date': {'year': query['endDate_year'], 'month': query['endDate_month'], 'day': query['endDate_day']},
                },
                'dimensions': query['dimensions'],
                'metrics': query['metrics'],
                'sort_conditions': {'dimension': query['orderBy'][0].replace('+', '').replace('-', ''), 'order': 'DESCENDING' if query['orderBy'][0].find('+') != -1 else 'ASCENDING' },
                'localizationSettings': {
                    'currencyCode': query['currencyCode'],
                    'languageCode': query['languageCode'] if 'languageCode' in query else 'en-US',
                },
                #'timeZone': query['reportingTimeZone'],
            }
            result = service.accounts().networkReport().generate(parent = accountInfo['name'], body={'report_spec': reportSpec}).execute()
        except Exception as e:
            outputMessage.append(f'[ERROR] {e}')
        if result != None:
            outputStatus = True
            try:
                # https://developers.google.com/admob/api/reference/rest/v1/accounts.networkReport/generate?hl=zh-tw
                header = []
                for field in query['dimensions']:
                    header.append(field)
                for field in query['metrics']:
                    header.append(field)
                outputReport.append(header)
                for row in result[1:]:
                    item = [] # [''] * (len(query['dimensions']) + len(query['metrics']))
                    if 'row' not in row:
                        continue
                    if 'dimensionValues' in row['row']:
                        for field in query['dimensions']:
                            value = row['row']['dimensionValues'][field]['value']
                            if field == 'DATE':
                                value = value[0:4]+'-'+value[4:6]+'-'+value[6:]
                            item.append( value )
                    if 'metricValues' in row['row']:
                        for field in query['metrics']:
                            value = row['row']['metricValues'][field]
                            if 'integerValue' in value:
                                item.append(value['integerValue'])
                            if 'doubleValue' in value:
                                item.append(value['doubleValue'])
                            if 'microsValue' in value:
                                item.append( int(value['microsValue']) / 1000000.0)
                    outputReport.append(item)
            except Exception as e:
                outputMessage.append(f'[ERROR] {e}')
    return (outputStatus, outputReport, "\n".join(outputMessage))

def listToCSVFormat(report: []) -> (bool, str, str):
    outputStatus = False
    outputMessage = []
    outputData = ''
    if len(report) >= 1:
        df = pd.DataFrame(report[1:], columns=report[0])
        outputStatus = True
        csvBuffer = StringIO()
        df.to_csv(csvBuffer, index=False)
        outputData = csvBuffer.getvalue()
    return (outputStatus, outputData, "\n".join(outputMessage))
