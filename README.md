## Goals
1. Grab transaction-level data for the Tron blockchain via API calls
2. Use data to analyze the effectiveness of Israeli Administrative Seizure Orders (ASOs)

## Data

### `aso_inventory.csv`

Contains all known ASOs from the [NBCTF web site](https://nbctf.mod.gov.il/en/Minister%20Sanctions/PropertyPerceptions/Pages/Blockchain1.aspx) as of 11/1/2023.

| field name | description|
| --- | --- |
| # | an index |  
| ASO | in the form of (order #)/(year) |  
| Date Signed| found, usually, on the last page of the ASO |
| Date Last Updated| found on the [NBCTF web site](https://nbctf.mod.gov.il/en/Minister%20Sanctions/PropertyPerceptions/Pages/Blockchain1.aspx)  |
| # Tron Addresses| manual inspection of the ASO |
| # Binance Accounts| manual inspection of the ASO |
| Target | manual inspection of the ASO |


### `tron_wallets.csv`

Contains every Tron wallet address appearing across all ASOs.

(Note: due to the poor quality of the pdfs, some manual labor was involved in ensuring data quality.  Cross referencing the [Tronscan](https://tronscan.org) helped tremendously.)

| field name | description|
| --- | --- |
| num | an index |
| wallet | Tron address of the wallet of concern |
| date_created | per Tronscan API calls, verified on [Tronscan](https://tronscan.org) |
| date_most_recent | per Tronscan API calls, verified on [Tronscan](https://tronscan.org) |
| aso | the ASO the wallet was listed on |
| aso_line_num | the line # listed in the ASO |
| note | (optional) |

