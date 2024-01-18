# google-csv-helper

[![PyPI](https://img.shields.io/pypi/v/google-csv-helper.svg)](https://pypi.org/project/google-csv-helper/)

A simple tool for parsing google csv files.

# Installation

```
% pip install google-csv-helper
```

# Usage 

```
% tree csv 
csv
├── admob
│   └── hk
│       └── latest-day.csv
└── adsense
    ├── cn
    │   └── latest-day.csv
    └── hk
        └── latest-day.csv

6 directories, 3 files

% file csv/admob/hk/latest-day.csv 
csv/admob/hk/latest-day.csv: Unicode text, UTF-16, little-endian text

% iconv -f UTF-16 -t UTF-8 csv/admob/hk/latest-day.csv | head -n1
日期	預估收益 (USD)	觀察到的有效千次曝光出價 (USD)	請求	媒合率 (%) (%)	比對成功的請求	顯示率 (%) (%)	曝光	點閱率 (%) (%)	點擊次數	出價要求	參與競價的出價 (%)	參與競價的出價	勝出出價 (%)	勝出出價次數

% file csv/adsense/hk/latest-day.csv 
csv/adsense/hk/latest-day.csv: CSV text

% head -n1 csv/adsense/hk/latest-day.csv 
日期,預估收益 (USD),瀏覽量,網頁千次曝光收益 (USD),曝光次數,曝光千次曝光收益 (USD),Active View 可視率,點擊,點閱率,單次點擊出價 (USD)

% head -n1 csv/adsense/cn/latest-day.csv
日期,估算收入 (USD),网页浏览量,网页 RPM (USD),展示次数,每千次展示收入 (USD),Active View 可见率,点击次数,点击率,CPC (USD)
```

---

## Use Google AdSense/Admob api to get the report content and convert it into csv format

```
% google-csv-helper --google-token-file .google-account01 --google-show-report-list
% google-csv-helper --google-token-file .google-account02 --google-show-report-list
% google-csv-helper --google-token-file .google-account01 --google-adsense-latest-csv > csv/account1/adsense/latest-day.csv
% google-csv-helper --google-token-file .google-account02 --google-admob-latest-csv > csv/account2/admob/latest-day.csv
% google-csv-helper --google-token-file .google-account02 --google-adsense-latest-csv > csv/account2/adsense/latest-day.csv
% tree csv 
csv
├── account01
│   └── adsense
│       └── latest-day.csv
└── account02
    ├── adsense
    │   └── latest-day.csv
    └── admob
        └── latest-day.csv

6 directories, 3 files
```

---

## Create Dashboard reports from csv files

```
% google-csv-helper --output markdown csv
## Current:
### Date Range: 2023-06-01 ~ 2023-06-04
#### compare: 2023-05-01 ~ 2023-05-31
| Item | Cumulative Revenue | Average Daily Revenue | Average CPC | Min Daily Revenue | Max Daily Revenue 
| -- | --: | --: | --: | --: | --: 
| Admob Global | 1,234.56 | 123.45 (-12.34%) | 0.001 (-1.23%) | 234.56 [06/02 Fri] | 456.78 [06/01 Thu] 
| Adsense Global | 1,234.56 | 123.45 (-12.34%) | 0.1234 (-2.34%) | 123.45 [06/02 Fri] | 345.67 [06/01 Thu] 
| Adsense China |  1,234.56 | 123.45 (-12.34%) | 0.2345 (2.34%) | 123.45 [06/02 Fri] | 345.67 `[06/01 Thu] 
| Total | 1,234.56 | 456.78 | | | 
```

## Current:
### Date Range: 2023-06-01 ~ 2023-06-04
#### compare: 2023-05-01 ~ 2023-05-31
| Item | Cumulative Revenue | Average Daily Revenue | Average CPC | Min Daily Revenue | Max Daily Revenue 
| -- | --: | --: | --: | --: | --: 
| Admob Global | 1,234.56 | 123.45 (-12.34%) | 0.001 (-1.23%) | 234.56 [06/02 Fri] | 456.78 [06/01 Thu] 
| Adsense Global | 1,234.56 | 123.45 (-12.34%) | 0.1234 (-2.34%) | 123.45 [06/02 Fri] | 345.67 [06/01 Thu] 
| Adsense China |  1,234.56 | 123.45 (-12.34%) | 0.2345 (2.34%) | 123.45 [06/02 Fri] | 345.67 `[06/01 Thu] 
| Total | 1,234.56 | 456.78 | | | 
