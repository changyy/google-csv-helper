# -*- encoding: utf-8 -*-

CSV_FIELD_NAME_TRANSFORM = {
    # Adsense API Export CSV
    "DATE": "Date",
    "ESTIMATED_EARNINGS": "Estimated earnings (USD)",
    "PAGE_VIEWS": "Page views",
    "PAGE_VIEWS_RPM": "Page RPM (USD)",
    "IMPRESSIONS": "Impressions",
    "IMPRESSIONS_RPM" : "Impression RPM (USD)",
    "ACTIVE_VIEW_VIEWABILITY": "Active View Viewable",
    "CLICKS" : "Clicks",
    "IMPRESSIONS_CTR" : "CTR",
    "COST_PER_CLICK": "CPC (USD)",

    # Adsense zh-TW
    "日期" : "Date",
    "月份" : "Month",
    "星期" : "Week",
    "預估收益 (USD)": "Estimated earnings (USD)",
    "瀏覽量": "Page views",
    "網頁千次曝光收益 (USD)": "Page RPM (USD)",
    "曝光次數": "Impressions",
    "曝光千次曝光收益 (USD)": "Impression RPM (USD)",
    "Active View 可視率": "Active View Viewable",
    "點擊": "Clicks",
    "點閱率": "CTR",
    "單次點擊出價 (USD)": "CPC (USD)",

    # Adsense zh-CN
    "日期" : "Date",
    "月" : "Month",
    "周" : "Week",
    "估算收入 (USD)" : "Estimated earnings (USD)",
    "网页浏览量" : "Page views",
    "网页 RPM (USD)" : "Page RPM (USD)",
    "展示次数" : "Impressions",
    "每千次展示收入 (USD)" : "Impression RPM (USD)",
    "Active View 可见率" : "Active View Viewable",
    "点击次数" : "Clicks",
    "点击率" : "CTR",

    # Admob zh-TW
    "週次" : "Week",
    "月份" : "Month",
    "預估收益 (USD)" : "Estimated earnings (USD)",
    "曝光" : "Impressions",
    "觀察到的有效千次曝光出價 (USD)": "Impression RPM (USD)",
    "點擊次數": "Clicks",
    "點閱率 (%) (%)" : "CTR%",

    # GA3 zh-TW
    "日索引": "Date",
    "使用者": "User",
    "新使用者": "NewUser",

    # Firebase zh-CN
    "第 N 天" : "",
    "30 天" : "",
    "7 天"  : "",
    "1 天" : "",
}

CSV_FIREBASE_KEYWORD = {
    "活跃用户随时间的变化趋势如何？" : "DAU",
    "开始日期" : "Begin",
    "结束日期" : "End",
}

CSV_KEYWORD_USAGE = {
    "活跃用户随时间的变化趋势如何？" : "",
    "开始日期" : "",
    "结束日期" : "",
}

CSV_FIELD_VALUE_TRANSFORM = {
    "CTR%" : {
        "handlerType": "function",
        "handler": lambda x: str(float(x.replace('%',''))*0.01),
        "newFieldName": "CTR",
    },
    "Clicks": {
        "handlerType": "calc",
        "handler": lambda row: (row['Estimated earnings (USD)'] / row["Clicks"]) if row["Clicks"] != 0 else 0,
        "newFieldName": "CPC (USD)",
    },
    "Impressions": {
        "handlerType": "calc",
        "handler": lambda row: (row['Clicks'] / row["Impressions"]) if row["Impressions"] != 0 else 0,
        "newFieldName": "CTR",
    },
}

CSV_FIELD_NAME_DATA_TYPE = {
    #"Date": str,
    #"Month": str,
    #"Week": str,
    "Estimated earnings (USD)": 1.0,
    "Page views": 1,
    "Page RPM (USD)": 1.0,
    "Impressions": 1,
    "Impression RPM (USD)": 1.0,
    #"Active View Viewable": str,
    "CTR": 1.0,
    "Clicks": 1,
    "CPC (USD)": 1.0,
}

CSV_OUTPUT_ADSENSE_FIELDS = [
    'Estimated earnings (USD)', 'Impressions', 'Impression RPM (USD)', 'Clicks', 'CTR', 'CPC (USD)',
]

CSV_OUTPUT_GA_FIELDS = [
    'User', 'NewUser', 'PageView',
]

CSV_INPUT_CHECK_MAIN_FIELD = [
    'Date', 'Week', 'Month',
]

CSV_OUTPUT_REPORT_COMPARISON_INFO = [
	'Estimated earnings (USD)', 'Average earnings (USD)' , 'Average CPC',
]

CSV_OUTPUT_FIELD_NAME_DATA_TYPE = {
    #"Date": str,
    #"Month": str,
    #"Week": str,
    "Estimated earnings (USD)": 1.0,
    "Page views": 1,
    "Page RPM (USD)": 1.0,
    "Impressions": 1,
    "Impression RPM (USD)": 1.0,
    #"Active View Viewable": str,
    "CTR": 1.0,
    "Clicks": 1,
    "CPC (USD)": 1.0,
}

