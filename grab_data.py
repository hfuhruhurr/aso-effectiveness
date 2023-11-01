import requests 
import time
import math 
import pandas as pd
import creds 

def make_call(wallet, query_index, n_xfers_per_call):
    print(f'Making call for {wallet}, {query_index}, {n_xfers_per_call}...')

    base_url = 'https://apilist.tronscanapi.com/api/'
    trc20_endpoint = 'filter/trc20/transfers'
    url = f'{base_url}{trc20_endpoint}'
    headers = {'TRON-PRO-API-KEY': creds.tronscan_api_key}
    
    trc20_params = {
        'limit': n_xfers_per_call,  # how many xfer records to grab per call (limit is 50)
        'start': query_index,       # the index of which records to start grabbing, 
        'sort': '-timestamp',       # how to sort the records returned
        'count': 'true',            # no clue what this does but Tronscan uses it
        'filterTokenValue': '0',    # no clue what this does but Tronscan uses it
        'relatedAddress': wallet    # the wallet address of concern
    }

    time.sleep(.205)  # limited to 5 calls per second

    return requests.get(url=url, headers=headers, params=trc20_params).json()    

def grab_one_xfer(j):

    timestamp = j['block_ts']
    tx_id = j['transaction_id']
    risk_tx = j['riskTransaction']
    status = j['status']
    from_address = j['from_address']
    from_tag = j['from_address_tag']['from_address_tag']
    to_address = j['to_address']
    to_tag = j['to_address_tag']['to_address_tag']
    quant = j['quant']
    token_id = j['tokenInfo']['tokenId']
    token_abbr = j['tokenInfo']['tokenAbbr']
    token_name = j['tokenInfo']['tokenName']
    token_decimal = j['tokenInfo']['tokenDecimal']
    token_type = j['tokenInfo']['tokenType']
    token_level = j['tokenInfo']['tokenLevel']
    contract_return = j['contractRet']
    result = j['finalResult']

    return [
        timestamp,
        tx_id,
        risk_tx,
        status,
        from_address,
        from_tag,
        to_address,
        to_tag,
        quant,
        token_id,
        token_abbr,
        token_name,
        token_decimal,
        token_type,
        token_level,
        contract_return,
        result
    ]

def grab_all_xfers_in_call(j, n_xfers_per_call):
    xfers = []
    n_xfers_this_call = len(j['token_transfers'])

    # print(f'  Grabbing all {n_xfers_this_call} transfers in this call...')
    
    for x in range(n_xfers_this_call):
        xfers.append(grab_one_xfer(j['token_transfers'][x]))

    return xfers

def grab_all_xfers_in_wallet(wallet, n_xfers_per_call):
    # first call (to get total # xfers)
    j = make_call(wallet, 0, n_xfers_per_call)
    n_xfers = j['total']
    n_loops = math.ceil(n_xfers / n_xfers_per_call)

    # grab all the xfers in the first call
    xfers = grab_all_xfers_in_call(j, n_xfers_per_call)

    # grab the remaining xfers via subsequent calls
    for l in range(1, n_loops):
        query_index = l * n_xfers_per_call
        j = make_call(wallet, query_index, n_xfers_per_call)
        xfers.extend(grab_all_xfers_in_call(j, n_xfers_per_call))

    [x.insert(0, wallet) for x in xfers]  # add wallet as first field
    
    return xfers 

n_xfers_per_call = 50

df = pd.read_csv('./data/wallets_with_tron_info.csv')
wallets = list(set(df.wallet.tolist()))[:3]


xfers = []
for wallet in wallets:
    xfers.append(grab_all_xfers_in_wallet(wallet, n_xfers_per_call))
    