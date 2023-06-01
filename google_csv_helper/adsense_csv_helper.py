# -*- encoding: utf-8 -*-

import csv_common as csvCommonInfo
import csv_helper as csvHelper

import pandas
import datetime

class AdsenseCSVHelper(csvHelper.CSVHelper):
    def getDateRangeReport(self, dataframe: pandas.DataFrame, keyFieldName:str, valueFilterBegin:str, valueFilterEnd:str, minmaxDateInputFormat:str, minmaxDateOutputFormat:str ):
        output = {}

        pickedData = dataframe[ (dataframe[keyFieldName] >= valueFilterBegin) & (dataframe[keyFieldName] <= valueFilterEnd) ]

        maxRow = pickedData[ pickedData['Estimated earnings (USD)'] == pickedData['Estimated earnings (USD)'].max() ]
        minRow = pickedData[ pickedData['Estimated earnings (USD)'] == pickedData['Estimated earnings (USD)'].min() ]

        maxRowDateInfo = datetime.datetime.strftime(datetime.datetime.strptime(maxRow.iloc[0][keyFieldName], minmaxDateInputFormat), minmaxDateOutputFormat)
        minRowDateInfo = datetime.datetime.strftime(datetime.datetime.strptime(minRow.iloc[0][keyFieldName], minmaxDateInputFormat), minmaxDateOutputFormat)

        output['Estimated earnings (USD)'] = pickedData['Estimated earnings (USD)'].sum()
        output['Average earnings (USD)'] = pickedData['Estimated earnings (USD)'].mean()
        output['Average CPC'] = pickedData['Estimated earnings (USD)'].sum() / pickedData['Clicks'].sum()
        output['Average Impressions'] = pickedData['Impressions'].mean()
        output['Lowest earnings'] = minRow['Estimated earnings (USD)'].sum()
        output['Lowest earnings info'] = minRowDateInfo
        output['Highest earnings'] = maxRow['Estimated earnings (USD)'].sum()
        output['Highest earnings info'] = maxRowDateInfo
        
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
                        "Item", "Cumulative Revenue", "Cumulative Revenue%", "Average Daily Revenue", "Average Daily Revenue%", "Average CPC", "Average CPC%", "Lowest Revenue", "Lowest Revenue Date", "Highest Revenue", "Highest Revenue Date",
                    ],
                    "data": [],
                    "total": {
                        "Cumulative Revenue": 0.0,
                        "Average Daily Revenue": 0.0,
                    },
                },
            },
        }

        today = pickedDate
        if today.day == 1:
            today = today - datetime.timedelta(days=1)
            DateFilterBegin = f"{today.replace(day=1)}"
            DateFilterEnd = f"{today}"
        else:
            DateFilterBegin = f"{today.replace(day=1)}"
            DateFilterEnd = f"{today.replace(day=(today.day - 1)) if today.day > 1 else today}"
        #print(f"Filter: {DateFilterBegin} ~ {DateFilterEnd}")
    
        prevDate = today.replace(day=1) - datetime.timedelta(days=1)
        prevDateFilterBegin = f"{prevDate.replace(day=1)}"
        prevDateFilterEnd = f"{prevDate}"
        #print(f"Filter: {prevDateFilterBegin} ~ {prevDateFilterEnd}")

        output["output"]["date"]["duration"]["begin"] = DateFilterBegin
        output["output"]["date"]["duration"]["end"] = DateFilterEnd
        output["output"]["date"]["previous"]["begin"] = prevDateFilterBegin
        output["output"]["date"]["previous"]["end"] = prevDateFilterEnd

        for k, v in self.getAllResult().items():
            target = k
            if k.find("adsense") > 0:
                target = "Adsense China" if k.find("cn") > 0 or k.find("china") > 0 else "Adsense Global"
            elif k.find("admob") > 0:
                target = "Admob China" if k.find("cn") > 0 or k.find("china") > 0 else "Admob Global"
    
            prevItemInfo = self.getDateRangeReport(v["Date"], 'Date', prevDateFilterBegin, prevDateFilterEnd, '%Y-%m-%d', '%m/%d %a')
            item = self.getDateRangeReport(v["Date"], 'Date', DateFilterBegin, DateFilterEnd, '%Y-%m-%d', '%m/%d %a')
    
            compareInfo = {}
            for lookup in csvCommonInfo.CSV_OUTPUT_REPORT_COMPARISON_INFO:
                compareInfo[lookup] = (item[lookup] - prevItemInfo[lookup]) * 100 / prevItemInfo[lookup]

            output["output"]["csv"]["data"].append([
                f"{target}",
                item['Estimated earnings (USD)'],
                compareInfo['Estimated earnings (USD)'],
                item['Average earnings (USD)'],
                compareInfo['Average earnings (USD)'],
                item['Average CPC'],
                compareInfo['Average CPC'],
                item['Lowest earnings'],
                item['Lowest earnings info'],
                item['Highest earnings'],
                item['Highest earnings info'],
            ])

            output["output"]["csv"]["total"]["Cumulative Revenue"] += item['Estimated earnings (USD)']
            output["output"]["csv"]["total"]["Average Daily Revenue"] += item['Average earnings (USD)']

        return output

    def getDailyMarkDownReport(self, pickedDate: datetime.date, pickedReportKeyword: list[str]) -> str:
        data = self.getDailySummaryReport(pickedDate, pickedReportKeyword)

        output = [ 
            f"### Date Range: {data['output']['date']['duration']['begin']} ~ {data['output']['date']['duration']['end']}",
            f"#### compare: {data['output']['date']['previous']['begin']} ~ {data['output']['date']['previous']['end']}",
            f"| Item | Cumulative Revenue | Average Daily Revenue | Average CPC | Min Daily Revenue | Max Daily Revenue ",
            f"| -- | --: | --: | --: | --: | --: ",
        ]

        for item in data["output"]["csv"]["data"]:
            output.append( f"| {item[0]} | {item[1]:,.2f} | {item[3]:,.2f} ({item[4]:.2f}%) | {item[5]:.4f} ({item[6]:.2f}%) | {item[7]:,.2f} [{item[8]}] | {item[9]:,.2f} [{item[10]}] " )

        output.append( f"| Total | {data['output']['csv']['total']['Cumulative Revenue']:,.2f} | {data['output']['csv']['total']['Average Daily Revenue']:,.2f} | | | ")

        return "\n".join(output)

if __name__ == '__main__':
    import sys
    obj = AdsenseCSVHelper(sys.argv[1:] if len(sys.argv) >= 2 else '')
    #obj.enableDebug()
    obj.readAllCSVRawFile()
    #print(obj.getAllJSONResult())
    print(obj.getDailyMarkDownReport(datetime.date.today(), ["adsense", "admob"]))
