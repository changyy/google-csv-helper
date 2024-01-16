# -*- encoding: utf-8 -*-
import os
import sys
import pandas as pd
from io import StringIO
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# https://github.com/googleads/googleads-adsense-examples/tree/main/v2/python

def googleProjectSetupCheck(configFilePath: str, tokenFilePath: str, oauthScopes: [str] = ['https://www.googleapis.com/auth/adsense.readonly', 'https://www.googleapis.com/auth/admob.readonly']) -> (bool, Credentials, str):
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

def getGoogleAdsenseAccountsInfo(service: Resource):
    queryResult = service.accounts().list().execute()
    if 'accounts' not in queryResult:
        return []
    return queryResult['accounts']

def getGoogleAdsenseSavedReportList(service: Resource, googleAccountPubId: str = None, maxPageSize: int = 50) -> (bool, [], str):
    outputStatus = False
    outputReport = []
    outputMessage = []
    for accountInfo in getGoogleAdsenseAccountsInfo(service):
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
def getGoogleAdsenseReport(service: Resource, googleAccountPubId: str = None, query: dict = { 'reportId': None, 'dateRange': None, 'metrics': [], 'dimensions': [], 'orderBy': [], 'currencyCode': 'USD', 'reportingTimeZone': 'ACCOUNT_TIME_ZONE' }) -> (bool, [], []):
    outputStatus = False
    outputReport = []
    outputMessage = []

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

    for accountInfo in getGoogleAdsenseAccountsInfo(service):
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
                if 'metrics' not in query or not query['metrics']:
                    query['metrics'] = ['COST_PER_CLICK', 'AD_REQUESTS_CTR', 'CLICKS', 'AD_REQUESTS', 'PAGE_VIEWS'] 
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
