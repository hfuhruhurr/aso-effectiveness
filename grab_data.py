import requests 
import time
import math 
import pandas as pd
import creds 

def make_call(wallet, query_index, n_xfers_per_call):
    print(f'Making call for {wallet}, start={query_index}, limit={n_xfers_per_call}...')

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

    for i in range(10):
        try:
            r = s.get(url=url, headers=headers, params=trc20_params) 
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemError(e)

        if len(r.json()) == 1:  # {'message': 'internal server error'}
            print(f'Something is amiss with {wallet}...\n{r.json()}\n')
            time.sleep(i)
        
    print('...done making call.')
    return r

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

def grab_call_xfers(j):
    print('  Grabbing call transfers...')

    xfers = []
    n_xfers_this_call = len(j['token_transfers'])

    for x in range(n_xfers_this_call):
        xfers.append(grab_one_xfer(j['token_transfers'][x]))

    print('  ...Done.')    
    return xfers

def grab_wallet_xfers(wallet, n_xfers_per_call):
    print(f'  Grabbing wallet transfers for {wallet}...')

    # first call (to get total # xfers)
    json = make_call(wallet, 0, n_xfers_per_call).json()
    n_xfers = json['total']
    n_loops = math.ceil(n_xfers / n_xfers_per_call)

    # grab all the xfers in the first call
    xfers = grab_call_xfers(json)

    # grab the remaining xfers via subsequent calls
    for l in range(1, n_loops):
        query_index = l * n_xfers_per_call
        json = make_call(wallet, query_index, n_xfers_per_call).json()
        xfers.extend(grab_call_xfers(json))

    process_wallet_xfers(wallet, xfers)

    print('  ...Done.')    
    return 

def process_wallet_xfers(wallet, xfers):
    print(f'  Processing wallet for {wallet}...')

    # if we got here, we successfully read all xfers for this wallet
    # write the xfers for posteriority so we don't have to reprocess that wallet
    output_list = []
    
    for xfer in xfers:
        output_list.append([wallet] + xfer)

    df = pd.DataFrame(output_list)

    with open('./data/trc20_xfers.csv', 'a') as f:
        df.to_csv(f, index=False, header=False)
        
    with open('./data/trc20_wallets_processed.txt', 'a') as f:
        f.write(wallet + '\n')

    print('  ...Done.')    
    return 


def load_wallets():
    df = pd.read_csv('./data/tron_wallets.csv')
    wallets = list(dict.fromkeys(df.wallet.tolist()))  # preserves order

    with open('./data/trc20_wallets_processed.txt', 'r') as f:
        text = f.read()
    wallets_already_processed = text.split('\n')

    wallets_to_process = [wallet for wallet in wallets if wallet not in wallets_already_processed]

    return wallets_to_process


if __name__ == '__main__':
    n_xfers_per_call = 50
    wallets = load_wallets()
    
    s = requests.Session()

    xfers = []
    for wallet in wallets:
        xfers.append(grab_wallet_xfers(wallet, n_xfers_per_call))
