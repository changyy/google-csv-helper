# -*- encoding: utf-8 -*-

from google_csv_helper import csv_common
from google_csv_helper import csv_helper

import pandas
from pandas.api.types import is_string_dtype
import datetime

class GA3CSVHelper(csv_helper.CSVHelper):
    defaultOutputField = ['User', 'NewUser', 'PageView']
    outputKeyFieldValueMergeOrder = ['User', 'NewUser', 'PageView']
    outputReportComparisonInfo = ['User', 'NewUser', 'PageView']
    intputDateFormat = "%Y/%m/%d"
    intputDataTypeChanging = { 'User': 'int', 'NewUser': 'int', 'PageView': 'int' }
    def __init__(self, input_path: str|list[str], filename_pattern: list[str]):
        self.input_field_checking = csv_common.CSV_INPUT_CHECK_MAIN_FIELD
        self.input_field_transform = csv_common.CSV_FIELD_NAME_TRANSFORM
        super().__init__(input_path, filename_pattern)

    def getDateRangeReport(self, dataframe: pandas.DataFrame, keyFieldName:str, keyFieldValueFilterBegin:str, keyFieldValueFilterEnd:str, inputDateFieldFormat:str, minmaxDateOutputFormat:str, outputFields:list[str], outputFieldsNeedToCompareMaxMin:list[str]):
        output = {}
        if len(dataframe.index) == 0:
            if self.debugMode:
                print(f"[WARNING] dataframe is empty.")
            return output

        # data type changing:
        dataframe[keyFieldName] = pandas.to_datetime(dataframe[keyFieldName], format=inputDateFieldFormat)
        pickedData = dataframe[ (dataframe[keyFieldName] >= keyFieldValueFilterBegin) & (dataframe[keyFieldName] <= keyFieldValueFilterEnd) ]
        #print("After filter:")
        #print(pickedData)
        if len(pickedData.index) == 0:
            if self.debugMode:
                print(f"[WARNING] pickedData dataframe is empty, too")
            return output

        # data type changing:
        #pickedData = pickedData.apply(lambda x: pandas.to_numeric(x.astype(str).str.replace(',','').replace('','0'), errors='coerce'))
        #pickedData[f] = pandas.to_numeric(pickedData[f])
        for f in pickedData.columns:
            if f in self.intputDataTypeChanging:
                if self.intputDataTypeChanging[f] == 'int':
                    pickedData.loc[:, f] = pickedData[f].map(lambda x: int(x.replace(',','')))
                elif self.intputDataTypeChanging[f] == 'float':
                    pickedData.loc[:, f] = pickedData[f].map(lambda x: float(x.replace(',','')))

        outFields = []
        outFieldsToCompareMaxMin = []
        for f in pickedData.columns:
            if f in outputFields:
                outFields.append(f)
            if f in outputFieldsNeedToCompareMaxMin:
                outFieldsToCompareMaxMin.append(f)

        for f in outFields:
            output[f"Average {f}"] = pickedData[f].mean()

        for f in outFieldsToCompareMaxMin:
            if f not in pickedData.columns:
                continue
            maxRow = pickedData[ pickedData[f] == pickedData[f].max() ]
            minRow = pickedData[ pickedData[f] == pickedData[f].min() ]

            if is_string_dtype(maxRow.iloc[0][keyFieldName]):
                maxRowDateInfo = datetime.datetime.strftime(datetime.datetime.strptime(maxRow.iloc[0][keyFieldName], inputDateFieldFormat), minmaxDateOutputFormat)
                minRowDateInfo = datetime.datetime.strftime(datetime.datetime.strptime(minRow.iloc[0][keyFieldName], inputDateFieldFormat), minmaxDateOutputFormat)
            else:
                maxRowDateInfo = datetime.datetime.strftime(maxRow.iloc[0][keyFieldName], minmaxDateOutputFormat)
                minRowDateInfo = datetime.datetime.strftime(minRow.iloc[0][keyFieldName], minmaxDateOutputFormat)

            output[f"Lowest {f}"] = minRow[f].sum()
            output[f"Lowest {f} info"] = minRowDateInfo
            output[f"Highest {f}"] = maxRow[f].sum()
            output[f"Highest {f} info"] = maxRowDateInfo

        return output

    def getDailySummaryReport(self, pickedDate: datetime.date, pickedReportKeyword: list[str]):
        output = {
            "input": {
                "pickedDate": pickedDate,
                "pickedReportKeyword": pickedReportKeyword,
            },
            "output": {
                "date": {
                    "duration": {
                        "begin": None,
                        "end": None,
                    },
                    "previous": {
                        "begin": None,
                        "end": None,
                    },
                },
                "csv": {
                    "header": [
                        "Item", #"Average Daily User", "Average Daily PageView", "Lowest User", "Lowest User Date", "Highest User", "Highest User Date", 
                    ],
                    "data": [],
                    "total": {
                        #"Average Daily User": 0.0,
                        #"Average Daily PageView": 0.0,
                    },
                },
            },
        }

        today = pickedDate

        DateFilterBegin = f"{today - datetime.timedelta(days=7)}"
        DateFilterEnd = f"{today - datetime.timedelta(days=1)}"
        #print(f"Filter: {DateFilterBegin} ~ {DateFilterEnd}")
    
        prevDateFilterBegin = f"{ today - datetime.timedelta(days=15)}"
        prevDateFilterEnd = f"{ today - datetime.timedelta(days=8) }"
        #print(f"Filter: {prevDateFilterBegin} ~ {prevDateFilterEnd}")

        output["output"]["date"]["duration"]["begin"] = DateFilterBegin
        output["output"]["date"]["duration"]["end"] = DateFilterEnd
        output["output"]["date"]["previous"]["begin"] = prevDateFilterBegin
        output["output"]["date"]["previous"]["end"] = prevDateFilterEnd

        tmpHeaderInfo = []
        tmpOutput = []
        for k, v in self.getAllResult().items():
            target = k

            # Check Format
            if "Date" not in v:
                if self.debugMode:
                    print(f"Skip by checking 'Date': {target}")
                continue
            if "Date" not in v["Date"].columns:
                if self.debugMode:
                    print(f"Skip by checking columns['Date']['Date']: {target}")
                continue
            if 'User' not in v["Date"].columns:
                if self.debugMode:
                    print(f"Skip by checking columns['Date']['User']: {target}")
                continue
    
            prevItemInfo = self.getDateRangeReport(v["Date"], 'Date', prevDateFilterBegin, prevDateFilterEnd, self.intputDateFormat, '%m/%d %a', self.defaultOutputField, self.outputKeyFieldValueMergeOrder)
            item = self.getDateRangeReport(v["Date"], 'Date', DateFilterBegin, DateFilterEnd, self.intputDateFormat, '%m/%d %a', self.defaultOutputField, self.outputKeyFieldValueMergeOrder)

            compareInfo = {}
            for lookup in self.outputReportComparisonInfo:
                if lookup not in item or lookup not in prevItemInfo:
                    compareInfo[lookup] = 0
                    continue
                compareInfo[lookup] = (item[lookup] - prevItemInfo[lookup]) * 100 / prevItemInfo[lookup]

            tmpOutput.append([
                f"{target}", item, compareInfo
            ])

            for h in item.keys():
                if h not in tmpHeaderInfo:
                    tmpHeaderInfo.append(h)

        output['output']['csv']['header'] = ['Item'] + tmpHeaderInfo[:]
        for item in tmpOutput: 
            outputItem = [
                item[0],
            ]

            for h in tmpHeaderInfo:
                if h in item[1].keys():
                    outputItem.append( item[1][h] )
                else:
                    outputItem.append(0)

            output["output"]["csv"]["data"].append(outputItem)

        return output

    def getDailyMarkDownReport(self, pickedDate: datetime.date, pickedReportKeyword: list[str]) -> str:
        data = self.getDailySummaryReport(pickedDate, pickedReportKeyword)

        output = [ 
            f"### Date Range: {data['output']['date']['duration']['begin']} ~ {data['output']['date']['duration']['end']}",
            f"#### Compare to previous period: {data['output']['date']['previous']['begin']} ~ {data['output']['date']['previous']['end']}",
            #f"| -- | --: | --: | --: | --: | --: ",
        ]

        output.append("| " + " | ".join(data["output"]["csv"]["header"]))
        markdownTableHead = ""
        for h in data["output"]["csv"]["header"]:
            if 'Item' in h:
                markdownTableHead += '| -- '
            elif 'info' in h:
                markdownTableHead += '| :--: '
            else:
                markdownTableHead += '| --: '
        output.append(markdownTableHead)

        for item in data["output"]["csv"]['data']:
            #output.append("| " + " | ".join(item))
            subOutput = []
            for content in item:
                if isinstance(content, int):
                    subOutput.append(f"{content:,d}")
                elif isinstance(content, float):
                    subOutput.append(f"{content:,.2f}")
                else:
                    subOutput.append(f"{content}")
            output.append("| " + " | ".join(subOutput))

        return "\n".join(output)

