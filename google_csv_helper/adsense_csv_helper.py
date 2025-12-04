# -*- encoding: utf-8 -*-

from google_csv_helper import csv_common
from google_csv_helper import csv_helper

import pandas
import datetime
import asciichartpy


def _percent_change(current_value: float, previous_value: float) -> float:
    if previous_value == 0:
        return 0.0
    try:
        return (current_value - previous_value) * 100.0 / previous_value
    except Exception:
        return 0.0

class AdsenseCSVHelper(csv_helper.CSVHelper):
    def getDateRangeReport(self, dataframe: pandas.DataFrame, keyFieldName:str, valueFilterBegin:str, valueFilterEnd:str, minmaxDateInputFormat:str, minmaxDateOutputFormat:str ):
        output = {
            'Estimated earnings (USD)': 0.0,
            'Average earnings (USD)': 0.0,
            'Average CPC': 0.0,
            'Average Impressions': 0.0,
            'Lowest earnings': 0.0,
            'Lowest earnings info': None,
            'Highest earnings': 0.0,
            'Highest earnings info': None,
            'raw': None,
        }
        if len(dataframe.index) == 0:
            if self.debugMode:
                print(f"[WARNING] dataframe is empty.")
            return output

        pickedData = dataframe[ (dataframe[keyFieldName] >= valueFilterBegin) & (dataframe[keyFieldName] <= valueFilterEnd) ]
        if len(pickedData.index) == 0:
            if self.debugMode:
                print(f"[WARNING] dataframe is empty, too. valueFilterBegin: {valueFilterBegin}, valueFilterEnd: {valueFilterEnd}")
                print(f"dataframe with (dataframe[keyFieldName] >= valueFilterBegin): { dataframe[ (dataframe[keyFieldName] >= valueFilterBegin) ] }")
                print(f"dataframe with (dataframe[keyFieldName] <= valueFilterEnd): { dataframe[ (dataframe[keyFieldName] <= valueFilterEnd) ] }")
            return output

        maxRow = pickedData[ pickedData['Estimated earnings (USD)'] == pickedData['Estimated earnings (USD)'].max() ]
        minRow = pickedData[ pickedData['Estimated earnings (USD)'] == pickedData['Estimated earnings (USD)'].min() ]

        maxRowDateInfo = datetime.datetime.strftime(datetime.datetime.strptime(maxRow.iloc[0][keyFieldName], minmaxDateInputFormat), minmaxDateOutputFormat)
        minRowDateInfo = datetime.datetime.strftime(datetime.datetime.strptime(minRow.iloc[0][keyFieldName], minmaxDateInputFormat), minmaxDateOutputFormat)

        output['Estimated earnings (USD)'] = pickedData['Estimated earnings (USD)'].sum()
        output['Average earnings (USD)'] = pickedData['Estimated earnings (USD)'].mean()
        clicks_sum = pickedData['Clicks'].sum()
        output['Average CPC'] = (pickedData['Estimated earnings (USD)'].sum() / clicks_sum) if clicks_sum != 0 else 0
        output['Average Impressions'] = pickedData['Impressions'].mean()
        output['Lowest earnings'] = minRow['Estimated earnings (USD)'].sum()
        output['Lowest earnings info'] = minRowDateInfo
        output['Highest earnings'] = maxRow['Estimated earnings (USD)'].sum()
        output['Highest earnings info'] = maxRowDateInfo

        output['raw'] = pickedData
        
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
                        "previous": {
                            "Cumulative Revenue": 0.0,
                            "Average Daily Revenue": 0.0,
                        },
                    },
                },
                "raw": {
                }
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
            #if k.find("adsense") > 0:
            #    target = "Adsense China" if k.find("cn") > 0 or k.find("china") > 0 else "Adsense Global"
            #elif k.find("admob") > 0:
            #    target = "Admob China" if k.find("cn") > 0 or k.find("china") > 0 else "Admob Global"

            # Check Format
            if "Date" not in v:
                if self.debugMode:
                    print(f"Skip by checking 'Date': {target}")
                continue
            if "Date" not in v["Date"].columns:
                if self.debugMode:
                    print(f"Skip by checking columns['Date']['Date']: {target}")
                continue
            if 'Estimated earnings (USD)' not in v["Date"].columns:
                if self.debugMode:
                    print(f"Skip by checking columns['Date']['Estimated earnings (USD)']: {target}")
                continue

            prevItemInfo = self.getDateRangeReport(v["Date"], 'Date', prevDateFilterBegin, prevDateFilterEnd, '%Y-%m-%d', '%m/%d %a')
            item = self.getDateRangeReport(v["Date"], 'Date', DateFilterBegin, DateFilterEnd, '%Y-%m-%d', '%m/%d %a')
            output["output"]["raw"][target] = [ item["raw"], prevItemInfo["raw"] ]
    
            compareInfo = {}
            for lookup in csv_common.CSV_OUTPUT_REPORT_COMPARISON_INFO:
                currentValue = item[lookup] if lookup in item else 0
                prevValue = prevItemInfo[lookup] if lookup in prevItemInfo else 0
                compareInfo[lookup] = _percent_change(currentValue, prevValue)

            output["output"]["csv"]["data"].append([
                f"{target}",
                item['Estimated earnings (USD)'] if 'Estimated earnings (USD)' in item else 0.0,
                compareInfo['Estimated earnings (USD)'],
                item['Average earnings (USD)'] if 'Average earnings (USD)' in item else 0.0,
                compareInfo['Average earnings (USD)'],
                item['Average CPC'] if 'Average CPC' in item else 0.0,
                compareInfo['Average CPC'],
                item['Lowest earnings'] if 'Lowest earnings' in item else 0.0,
                item['Lowest earnings info'] if 'Lowest earnings info' in item else None,
                item['Highest earnings'] if 'Highest earnings' in item else 0.0,
                item['Highest earnings info'] if 'Highest earnings info' in item else None,
            ])

            if 'Estimated earnings (USD)' in item:
                output["output"]["csv"]["total"]["Cumulative Revenue"] += item['Estimated earnings (USD)']
            if 'Average earnings (USD)' in item:
                output["output"]["csv"]["total"]["Average Daily Revenue"] += item['Average earnings (USD)']
            if 'Estimated earnings (USD)' in prevItemInfo:
                output["output"]["csv"]["total"]["previous"]["Cumulative Revenue"] += prevItemInfo['Estimated earnings (USD)']
            if 'Average earnings (USD)' in prevItemInfo:
                output["output"]["csv"]["total"]["previous"]["Average Daily Revenue"] += prevItemInfo['Average earnings (USD)']

        return output

    def getDailyMarkDownReport(self, pickedDate: datetime.date, pickedReportKeyword: list[str], charts: dict = {}) -> str:
        data = self.getDailySummaryReport(pickedDate, pickedReportKeyword)

        output = [ 
            f"### Date Range: {data['output']['date']['duration']['begin']} ~ {data['output']['date']['duration']['end']}",
            f"#### Compare to previous period: {data['output']['date']['previous']['begin']} ~ {data['output']['date']['previous']['end']}",
            f"| Item | Cumulative Revenue | Average Daily Revenue | Average CPC | Min Daily Revenue | Max Daily Revenue ",
            f"| -- | --: | --: | --: | --: | --: ",
        ]

        for item in data["output"]["csv"]["data"]:
            output.append( f"| {item[0]} | {item[1]:,.2f} | {item[3]:,.2f} ({item[4]:.2f}%) | {item[5]:.4f} ({item[6]:.2f}%) | {item[7]:,.2f} [{item[8]}] | {item[9]:,.2f} [{item[10]}] " )

        total_current = data['output']['csv']['total']
        total_prev = data['output']['csv']['total']['previous']
        total_avg_delta = _percent_change(total_current['Average Daily Revenue'], total_prev['Average Daily Revenue'])
        output.append( f"| Total | {total_current['Cumulative Revenue']:,.2f} | {total_current['Average Daily Revenue']:,.2f} ({total_avg_delta:.2f}%) | | | ")

        #charts = {
        #    'config': {'height': 10},
        #    'columns': {
        #        'Estimated earnings (USD)': 'Estimated earnings (USD)',
        #        'CPC (USD)': 'CPC (USD)',
        #    }, 'debug': {
        #        'showCumulativeAverageChartColumnCandidates': False,
        #        'showEachCumulativeAverageColumnChart': False,
        #    }
        #}
        if 'config' in charts and 'columns' in charts:
            output.append("#### ref")
            chartsConfig = charts['config']
            chartsOutput = charts['columns']

            if 'showCumulativeAverageChartColumnCandidates' in charts['debug'] and charts['debug']['showCumulativeAverageChartColumnCandidates']:
                for k, v in data['output']['raw'].items(): 
                    if len(v) == 0 or not isinstance(v[0], pandas.DataFrame):
                        continue
                    selectedDataFrame = v[0]
                    print(f"[INFO] {k} CumulativeAverageChart Column Candidates: {selectedDataFrame.columns.to_list()}")

            for selectedColumn, outputColumn in chartsOutput.items():
                sumOfTargetColumn = {}
                moreDetails = []
                for k, v in data['output']['raw'].items():
                    if len(v) == 0 or not isinstance(v[0], pandas.DataFrame):
                        continue
                    selectedDataFrame = v[0]
                    for selectedColumn in chartsOutput.keys():
                        if selectedColumn not in selectedDataFrame.columns:
                            continue
                        #targetValues = list(selectedDataFrame[selectedColumn])
                        #avgValues = []
                        #for i in range(len(targetValues)):
                        #    avgValues.append(sum(targetValues[0:i+1])/(i+1) if i > 0 else targetValues[i])
                        avgValues = selectedDataFrame[selectedColumn].expanding().mean().tolist()
                        sumOfTargetColumn[k] = avgValues

                        if 'showEachCumulativeAverageColumnChart' in charts['debug'] and charts['debug']['showEachCumulativeAverageColumnChart']:
                            moreDetails.append(f"###### {k} - Cumulative Average of '{selectedColumn}' Chart:")
                            moreDetails.append("```")
                            moreDetails.append(asciichartpy.plot(avgValues, cfg=chartsConfig))
                            moreDetails.append("```")
                if len(sumOfTargetColumn) > 0:
                    passDataLengthCheck = True
                    sumOfTargetColumnValue = []
                    for avgValues in sumOfTargetColumn.values():
                        if len(sumOfTargetColumnValue) == 0:
                            sumOfTargetColumnValue = avgValues
                        elif len(sumOfTargetColumnValue) != len(avgValues):
                            passDataLengthCheck = False
                            break
                        else:
                            sumOfTargetColumnValue = [sum(x) for x in zip(sumOfTargetColumnValue, avgValues)] 
                    output.append(f"##### Sum of ({', '.join(list(sumOfTargetColumn.keys()))}) - Cumulative Average of '{selectedColumn}' Chart:")
                    if len(sumOfTargetColumnValue) == 0:
                        passDataLengthCheck = False
                        output.append()
                        output.append('No Data')
                    elif not passDataLengthCheck:
                        output.append('All targetColumn lists must have the same number of elements.')
                    else:
                        output.append("```")
                        output.append(asciichartpy.plot(sumOfTargetColumnValue, cfg=chartsConfig))
                        output.append("```")

                    if len(moreDetails) > 0:
                        output = output + moreDetails

        return "\n".join(output)

    def getYearlyMarkDownReport(self, pickedDate: datetime.date) -> str:
        sections = self._build_yearly_sections(pickedDate)
        if len(sections) == 0:
            return ""
        output = []
        output.append("### Yearly / YTD Comparisons")
        for section in sections:
            output.append(f"#### {section['title']}")
            output.append(f"##### Compare to: {section['compare_title']}")
            output.append(f"| Item | Current | Previous | Δ vs prior |")
            output.append(f"| -- | --: | --: | --: |")
            for row in section['rows']:
                output.append(f"| {row['label']} | {row['current']:,.2f} | {row['previous']:,.2f} | {row['delta']:.2f}% |")
            total_delta = _percent_change(section['totals']['current'], section['totals']['previous'])
            output.append(f"| Total | {section['totals']['current']:,.2f} | {section['totals']['previous']:,.2f} | {total_delta:.2f}% |")
        monthly = self._build_monthly_sections(pickedDate)
        if monthly:
            output.append("### Monthly Comparisons")
            output.append(f"#### {pickedDate.year} vs {pickedDate.year - 1}")
            for table_name, rows in monthly['tables'].items():
                output.append(f"#### {table_name}")
                output.append(f"| Month | Revenue | Prev Revenue | Δ Revenue | Avg Daily | Prev Avg Daily | Δ Avg Daily | Avg CPC | Prev Avg CPC | Δ Avg CPC |")
                output.append(f"| -- | --: | --: | --: | --: | --: | --: | --: | --: | --: |")
                for row in rows:
                    output.append(f"| {row['month']} | {row['cur_rev']:,.2f} | {row['prev_rev']:,.2f} | {row['delta_rev']:.2f}% | {row['cur_avg']:,.2f} | {row['prev_avg']:,.2f} | {row['delta_avg']:.2f}% | {row['cur_cpc']:.4f} | {row['prev_cpc']:.4f} | {row['delta_cpc']:.2f}% |")
                if table_name in monthly['charts']:
                    for chart in monthly['charts'][table_name]:
                        output.append(f"##### {chart['title']} ({pickedDate.year})")
                        if len(chart['data']) == 0:
                            output.append("No Data")
                        else:
                            output.append("```")
                            output.append(asciichartpy.plot(chart['data'], cfg={'height': 10}))
                            output.append("```")
        return "\n".join(output)

    def _build_yearly_sections(self, pickedDate: datetime.date):
        cutoff_current = pickedDate - datetime.timedelta(days=1) if pickedDate.day > 1 else pickedDate
        current_year = pickedDate.year
        prev_year = current_year - 1
        prev_prev_year = current_year - 2

        def shift_year_safe(date_obj: datetime.date, delta: int) -> datetime.date:
            target_year = date_obj.year + delta
            month = date_obj.month
            day = date_obj.day
            while day > 28:
                try:
                    return datetime.date(target_year, month, day)
                except ValueError:
                    day -= 1
            return datetime.date(target_year, month, day)

        cutoff_prev_year = shift_year_safe(cutoff_current, -1)
        cutoff_prev_prev_year = shift_year_safe(cutoff_current, -2)

        sections = [
            {
                'title': f"{prev_year} full year",
                'compare_title': f"{prev_prev_year} full year",
                'current_start': datetime.date(prev_year, 1, 1),
                'current_end': datetime.date(prev_year, 12, 31),
                'previous_start': datetime.date(prev_prev_year, 1, 1),
                'previous_end': datetime.date(prev_prev_year, 12, 31),
            },
            {
                'title': f"{prev_year} YTD (01/01-{cutoff_prev_year})",
                'compare_title': f"{prev_prev_year} same range",
                'current_start': datetime.date(prev_year, 1, 1),
                'current_end': cutoff_prev_year,
                'previous_start': datetime.date(prev_prev_year, 1, 1),
                'previous_end': cutoff_prev_prev_year,
            },
            {
                'title': f"{current_year} YTD (01/01-{cutoff_current})",
                'compare_title': f"{prev_year} same range",
                'current_start': datetime.date(current_year, 1, 1),
                'current_end': cutoff_current,
                'previous_start': datetime.date(prev_year, 1, 1),
                'previous_end': cutoff_prev_year,
            },
        ]

        results = []
        for section in sections:
            rows = []
            total_current = 0.0
            total_previous = 0.0
            for k, v in self.getAllResult().items():
                if "Date" not in v or "Date" not in v["Date"].columns:
                    continue
                current_summary = self.getDateRangeReport(v["Date"], 'Date', f"{section['current_start']}", f"{section['current_end']}", '%Y-%m-%d', '%m/%d %a')
                previous_summary = self.getDateRangeReport(v["Date"], 'Date', f"{section['previous_start']}", f"{section['previous_end']}", '%Y-%m-%d', '%m/%d %a')
                if current_summary['raw'] is None or previous_summary['raw'] is None:
                    continue
                current_value = current_summary['Estimated earnings (USD)']
                previous_value = previous_summary['Estimated earnings (USD)']
                rows.append({
                    'label': f"{k}",
                    'current': current_value,
                    'previous': previous_value,
                    'delta': _percent_change(current_value, previous_value),
                })
                total_current += current_value
                total_previous += previous_value
            # Skip section if both sides missing data
            if total_current == 0 or total_previous == 0 or len(rows) == 0:
                continue
            results.append({
                'title': section['title'],
                'compare_title': section['compare_title'],
                'rows': rows,
                'totals': {
                    'current': total_current,
                    'previous': total_previous,
                }
            })
        return results

    def _build_monthly_sections(self, pickedDate: datetime.date):
        current_year = pickedDate.year
        prev_year = current_year - 1
        cutoff_current = pickedDate - datetime.timedelta(days=1) if pickedDate.day > 1 else pickedDate

        def month_range(year: int, month: int, cutoff: datetime.date):
            start = datetime.date(year, month, 1)
            if month == 12:
                end = datetime.date(year, 12, 31)
            else:
                end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
            if year == cutoff.year and month == cutoff.month:
                end = min(end, cutoff)
            return start, end

        def compute_stats(df: pandas.DataFrame, start: datetime.date, end: datetime.date):
            df_copy = df.copy()
            df_copy['Date_dt'] = pandas.to_datetime(df_copy['Date'], errors='coerce')
            mask = (df_copy['Date_dt'] >= pandas.to_datetime(start)) & (df_copy['Date_dt'] <= pandas.to_datetime(end))
            picked = df_copy[mask]
            if len(picked.index) == 0:
                return {'rev': 0.0, 'avg': 0.0, 'cpc': 0.0}
            rev = picked['Estimated earnings (USD)'].sum()
            clicks = picked['Clicks'].sum() if 'Clicks' in picked.columns else 0
            days = picked['Date'].nunique()
            avg = (rev / days) if days != 0 else 0.0
            cpc = (rev / clicks) if clicks != 0 else 0.0
            return {'rev': rev, 'avg': avg, 'cpc': cpc}

        tables = {}
        charts = {}
        total_months = {}

        months_to_process = []
        for m in range(1, 13):
            start_cur, end_cur = month_range(current_year, m, cutoff_current)
            if start_cur > cutoff_current:
                continue
            months_to_process.append((m, start_cur, end_cur))

        for k, v in self.getAllResult().items():
            if "Date" not in v or "Date" not in v["Date"].columns:
                continue
            item_rows = []
            avg_series = []
            cpc_series = []
            for m, start_cur, end_cur in months_to_process:
                start_prev, end_prev = month_range(prev_year, m, end_cur.replace(year=prev_year))
                cur = compute_stats(v["Date"], start_cur, end_cur)
                prev = compute_stats(v["Date"], start_prev, end_prev)
                if cur['rev'] == 0 and prev['rev'] == 0:
                    continue
                month_label = f"{current_year}-{m:02d}"
                item_rows.append({
                    'month': month_label,
                    'cur_rev': cur['rev'],
                    'cur_avg': cur['avg'],
                    'cur_cpc': cur['cpc'],
                    'prev_rev': prev['rev'],
                    'prev_avg': prev['avg'],
                    'prev_cpc': prev['cpc'],
                })
                avg_series.append(cur['avg'])
                cpc_series.append(cur['cpc'])

                # accumulate total data
                if month_label not in total_months:
                    total_months[month_label] = {'cur_rev': 0.0, 'prev_rev': 0.0, 'cur_avg_sum': 0.0, 'cur_avg_cnt': 0,
                                                 'prev_avg_sum': 0.0, 'prev_avg_cnt': 0, 'cur_cpc_sum': 0.0, 'cur_cpc_cnt': 0,
                                                 'prev_cpc_sum': 0.0, 'prev_cpc_cnt': 0}
                total_months[month_label]['cur_rev'] += cur['rev']
                total_months[month_label]['prev_rev'] += prev['rev']
                if cur['avg'] != 0:
                    total_months[month_label]['cur_avg_sum'] += cur['avg']
                    total_months[month_label]['cur_avg_cnt'] += 1
                if prev['avg'] != 0:
                    total_months[month_label]['prev_avg_sum'] += prev['avg']
                    total_months[month_label]['prev_avg_cnt'] += 1
                if cur['cpc'] != 0:
                    total_months[month_label]['cur_cpc_sum'] += cur['cpc']
                    total_months[month_label]['cur_cpc_cnt'] += 1
                if prev['cpc'] != 0:
                    total_months[month_label]['prev_cpc_sum'] += prev['cpc']
                    total_months[month_label]['prev_cpc_cnt'] += 1

            if len(item_rows) > 0:
                tables[k] = sorted(item_rows, key=lambda x: x['month'])
                if len(avg_series) > 0:
                    charts.setdefault(k, []).append({'title': f"{k} Avg Daily", 'data': avg_series})
                if len(cpc_series) > 0:
                    charts.setdefault(k, []).append({'title': f"{k} CPC", 'data': cpc_series})

        # totals across items
        total_avg_series = []
        total_cpc_series = []
        total_rows = []
        for month_label in sorted(total_months.keys()):
            info = total_months[month_label]
            cur_avg = (info['cur_avg_sum'] / info['cur_avg_cnt']) if info['cur_avg_cnt'] > 0 else 0.0
            prev_avg = (info['prev_avg_sum'] / info['prev_avg_cnt']) if info['prev_avg_cnt'] > 0 else 0.0
            cur_cpc = (info['cur_cpc_sum'] / info['cur_cpc_cnt']) if info['cur_cpc_cnt'] > 0 else 0.0
            prev_cpc = (info['prev_cpc_sum'] / info['prev_cpc_cnt']) if info['prev_cpc_cnt'] > 0 else 0.0
            total_rows.append({
                'month': f"{month_label}",
                'cur_rev': info['cur_rev'],
                'cur_avg': cur_avg,
                'cur_cpc': cur_cpc,
                'prev_rev': info['prev_rev'],
                'prev_avg': prev_avg,
                'prev_cpc': prev_cpc,
            })
            total_avg_series.append(cur_avg)
            total_cpc_series.append(cur_cpc)

        if len(total_rows) > 0:
            tables["Total"] = sorted(total_rows, key=lambda x: x['month'])
            charts.setdefault("Total", []).append({'title': "Total Avg Daily", 'data': total_avg_series})
            charts.setdefault("Total", []).append({'title': "Total CPC", 'data': total_cpc_series})

        if len(tables.keys()) == 0:
            return None

        # add deltas
        for _, rows in tables.items():
            for row in rows:
                row['delta_rev'] = _percent_change(row['cur_rev'], row['prev_rev'])
                row['delta_avg'] = _percent_change(row['cur_avg'], row['prev_avg'])
                row['delta_cpc'] = _percent_change(row['cur_cpc'], row['prev_cpc'])

        return {
            'tables': tables,
            'charts': charts,
        }
