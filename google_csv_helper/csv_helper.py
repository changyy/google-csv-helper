# -*- encoding: utf-8 -*-

import csv_common as csvCommonInfo

import os
import io
import json
import pandas
import datetime

class CSVHelper:
    raw_csv_files_output = {}
    pandas_dataframe_output = {}
    debugMode = False
    def __init__(self, input_path: str|list[str]):
        self.input_path = []
        if isinstance(input_path, str):
            #self.input_path.append(input_path)
            self.findAllCSV(input_path)
        elif isinstance(input_path, list):
            for item in input_path:
                if isinstance(item, str):
                    #self.input_path.append(item)
                    self.findAllCSV(item)
        self.src_file = []
        self.src_dir = []

    def enableDebug(self):
        self.debugMode = True

    def disableDebug(self):
        self.debugMode = False

    def findAllCSV(self, input_path:str):
        output = {}
        lookup = {}
        if os.path.isfile(input_path):
            output[ os.path.dirname(input_path) ] = [input_path]
        else:
            for (dirpath, dirnames, filenames) in os.walk(input_path):
                for f in filenames:
                    if dirpath not in output:
                        output[dirpath] = []
                    full_path = os.path.join(dirpath,f)
                    if full_path not in lookup:
                        output[dirpath].append(full_path)
                        lookup[full_path] = dirpath
        self.raw_csv_files_output = output

    def readAllCSVRawFile(self):
        output = {}
        for key, values in self.raw_csv_files_output.items():
            for item in values:
                #print(item)
                df = None
                for try_encodeing in ['utf-8', 'utf-16le']:
                    try:
                        df = pandas.read_csv(item, sep='[,\\t]', engine='python', encoding=try_encodeing)
                        if len(df.index) > 1:
                            break
                    except Exception as e:
                        pass
                self.handlePandasDataFrame(key, item, df)
        return output

    def getAllJSONResult(self) -> dict[str, pandas.DataFrame]:
        output = {'key':[], 'data':{} }
        for key in self.getAllKey():
            output['key'].append(key)
            output['data'][key] = self.getResultViaCSV(key)
        return json.dumps(output)

    def getAllResult(self) -> dict[str, pandas.DataFrame]:
        return self.pandas_dataframe_output

    def getAllKey(self) -> list[str]:
        return [k for k in self.pandas_dataframe_output.keys()]

    def getResultViaPandasDataFrame(self, key:str) -> (pandas.DataFrame | None):
        if key in self.pandas_dataframe_output:
            return self.pandas_dataframe_output[key]
        return None

    def getResultViaCSV(self, key:str):
        if key in self.pandas_dataframe_output:
            output = {}
            for k, v in self.pandas_dataframe_output[key].items():
                output[k] = []
                with io.StringIO(v.to_csv()) as f:
                    csvparser = csv.reader(f)
                    csvheader = None
                    for row in csvparser:
                        if csvheader == None:
                            csvheader = row
                        else:
                            #print(row)
                            #print(csvheader)
                            for index, header in enumerate(csvheader):
                                if header in csvCommonInfo.CSV_OUTPUT_FIELD_NAME_DATA_TYPE:
                                    if isinstance(csvCommonInfo.CSV_OUTPUT_FIELD_NAME_DATA_TYPE[header], int):
                                        try:
                                            row[index] = int(row[index])
                                        except Exception as e:
                                            row[index] = 0
                                    elif isinstance(csvCommonInfo.CSV_OUTPUT_FIELD_NAME_DATA_TYPE[header], float):
                                        try:
                                            row[index] = float(row[index])
                                        except Exception as e:
                                            row[index] = 0.0
                            #print(row)
                            #sys.exit(0)
                        output[k].append(row)
            return output
        return None

    def handlePandasDataFrame(self, key:str, filename:str , dataFrame: pandas.DataFrame):
        if isinstance(dataFrame, pandas.DataFrame) == False:
            return
        #print(f"{key}: {filename}")

        fieldRename = {}
        # field name transform
        for field in dataFrame.columns:
            if field in csvCommonInfo.CSV_FIELD_NAME_TRANSFORM:
                fieldRename[field] = csvCommonInfo.CSV_FIELD_NAME_TRANSFORM[field]
        if len(fieldRename) > 0:
            dataFrame.rename(columns=fieldRename, inplace = True)

        if key not in self.pandas_dataframe_output:
            self.pandas_dataframe_output[key] = {}

        #keyField = dataFrame.columns[0]
        keyField = None
        for field in dataFrame.columns:
            if field in csvCommonInfo.CSV_INPUT_CHECK_MAIN_FIELD:
                keyField = field
                break

        # Skip
        if keyField == None:
            if self.debugMode:
                 print(f"[WARNING] keyField({csvCommonInfo.CSV_INPUT_CHECK_MAIN_FIELD}) not found, skip this data: {filename}")
            return

        for field, info in csvCommonInfo.CSV_FIELD_VALUE_TRANSFORM.items():
            if field in dataFrame.columns and info['newFieldName'] not in dataFrame.columns:
                #print(dataFrame.columns)
                if self.debugMode:
                    print(f"[INFO] create '{info['newFieldName']}' field from '{field}' dataframe via '{info['handlerType']}'")
                if info['handlerType'] == 'function':
                    dataFrame[info['newFieldName']] = dataFrame[field].apply(info['handler'])
                elif info['handlerType'] == 'calc':
                    dataFrame[info['newFieldName']] = dataFrame.apply(info['handler'], axis=1)
                #print(dataFrame[[field, info['newFieldName']]])

        for field in csvCommonInfo.CSV_OUTPUT_ADSENSE_FIELDS:
            if field not in dataFrame.columns:
                if self.debugMode:
                    print(f"[WARNING] dataField({csvCommonInfo.CSV_OUTPUT_ADSENSE_FIELDS}) not found, skip this data: {filename}")
                return
            
        if self.debugMode:
            print(f"[INFO] import file: {filename}")
        currentData = dataFrame[ [keyField] + csvCommonInfo.CSV_OUTPUT_ADSENSE_FIELDS ]
        currentDataLength = len(currentData)
        currentDateBegin = currentData[keyField][0] if currentDataLength > 0 else None
        currentDateEnd = currentData[keyField][currentDataLength - 1] if currentDataLength > 0 else None

        # set output
        if keyField not in self.pandas_dataframe_output[key]:
            self.pandas_dataframe_output[key][keyField] = currentData
            return

        # update data
        keyFieldOldData = self.pandas_dataframe_output[key][keyField][keyField]
        oldDataLength = len(keyFieldOldData)
        oldDateBegin = keyFieldOldData[0] if oldDataLength > 0 else None
        oldDateEnd = keyFieldOldData[oldDataLength-1] if oldDataLength > 0 else None

        if oldDateBegin >= currentDateBegin or oldDateEnd <= currentDateEnd:
            self.pandas_dataframe_output[key][keyField] = self.handleDataFrameMerge(self.pandas_dataframe_output[key][keyField], currentData, keyField, csvCommonInfo.CSV_OUTPUT_ADSENSE_FIELDS[0])
        return

    def handleDataFrameMerge(self, oldDataFrame: pandas.DataFrame, newDataFrame: pandas.DataFrame, keyField:str, valueField:str) -> pandas.DataFrame:
        #print("in handleDataFrameMerge")
        # https://pandas.pydata.org/docs/reference/api/pandas.concat.html?highlight=concat#pandas.concat
        # https://pandas.pydata.org/docs/reference/api/pandas.merge_ordered.html
        output = pandas.merge_ordered(oldDataFrame, newDataFrame)
        while True:
            oldSize = len(output.index)
            #print(f"Init size: {oldSize},  {output.index}")
            if oldSize <= 1:
                break
            prev = None
            for i in output.index:
                if prev == None:
                    prev = i
                    continue
                #print(f"prev: {prev}, i: {i}, max: {output.index[-1]}")
                if output.iloc[i][keyField] == output.iloc[prev][keyField]:
                    #print(f"-- prev: {prev}")
                    #print(output.iloc[prev])
                    #print(f"-- i: {i}")
                    #print(output.iloc[i])

                    if output.iloc[i][valueField] > output.iloc[prev][valueField]:
                        #print(f"remove: prev({prev}), i:{output.iloc[i][valueField]} > prev:{output.iloc[prev][valueField]}")
                        output = output.drop([prev])
                        #print(f'==> drop: {prev}, {output.index}\n')
                        prev = i
                    else:
                        #print(f"remove: i({i}), i:{output.iloc[i][valueField]} <= prev:{output.iloc[prev][valueField]}")
                        output = output.drop([i])
                        #print(f'==> drop: {i}, {output.index}\n')
                    output.reset_index(drop=True, inplace=True)
                    break
                elif prev != i:
                    prev = i

            # no change
            if oldSize == len(output.index):
                break

        return output

