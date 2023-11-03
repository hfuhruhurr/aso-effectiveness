import csv
from typing import List, Dict
import logging
from ratelimiter import RateLimiter
import requests 
import time
import math 
import pandas as pd
import creds 

BASE_URL = 'https://apilist.tronscanapi.com/api/'
TRC20_ENDPOINT = 'filter/trc20/transfers'
URL = f'{BASE_URL}{TRC20_ENDPOINT}'

rate_limit = RateLimiter(max_calls=5, period=1)

@rate_limit
def make_call(wallet, query_index, n_xfers_per_call, s):
    """
    Makes a call to the Tronscan API to retrieve transfer records for a specific wallet.

    Args:
        wallet (str): The wallet address of concern.
        query_index (int): The index of which records to start grabbing.
        n_xfers_per_call (int): How many transfer records to grab per call.
        s (requests.Session): The session object to use for making the API call.

    Returns:
        requests.Response: The response object from the API call.
    """
    logging.info(f'Making call for {wallet}, start={query_index}, limit={n_xfers_per_call}...')

    headers = {'TRON-PRO-API-KEY': creds.tronscan_api_key}

    trc20_params = {
        'limit': n_xfers_per_call,
        'start': query_index,
        'sort': '-timestamp',
        'count': 'true',
        'filterTokenValue': '0',
        'relatedAddress': wallet
    }

    for i in range(10):
        try:
            r = s.get(url=URL, headers=headers, params=trc20_params)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if i < 9:
                logging.warning(f'Retrying request for {wallet}...')
                time.sleep(i+1)
            else:
                logging.error(f'Failed to make request for {wallet} after 10 attempts.')
                return None

        if len(r.json()) == 1:
            logging.error(f'Something is amiss with {wallet}...\n{r.json()}\n')
            time.sleep(i+1)

    logging.info('...done making call.')
    return r

def grab_one_xfer(j: dict) -> list:
    """
    Extracts relevant information from a JSON object representing a transfer record.

    Args:
        j (dict): A JSON object representing a transfer record.

    Returns:
        list: A list containing the extracted information from the transfer record.
    """
    timestamp = j.get('block_ts')
    tx_id = j.get('transaction_id')
    risk_tx = j.get('riskTransaction')
    status = j.get('status')
    from_address = j.get('from_address')
    from_tag = j.get('from_address_tag', {}).get('from_address_tag')
    to_address = j.get('to_address')
    to_tag = j.get('to_address_tag', {}).get('to_address_tag')
    quant = j.get('quant')
    token_info = j.get('tokenInfo', {})
    token_id = token_info.get('tokenId')
    token_abbr = token_info.get('tokenAbbr')
    token_name = token_info.get('tokenName')
    token_decimal = token_info.get('tokenDecimal')
    token_type = token_info.get('tokenType')
    token_level = token_info.get('tokenLevel')
    contract_return = j.get('contractRet')
    result = j.get('finalResult')

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

def grab_call_xfers(j: dict) -> list:
    """
    Extracts relevant information from a JSON object representing a transfer record.

    Args:
        j (dict): A JSON object representing a transfer record.

    Returns:
        list: A list containing the extracted information from the transfer records in the JSON object.
              Each transfer record is represented as a sublist containing the extracted information.
    """
    xfers = []

    for transfer in j.get('token_transfers', []):
        xfers.append(grab_one_xfer(transfer))

    return xfers

def make_call(wallet: str, query_index: int, n_xfers_per_call: int) -> Dict:
    """
    Makes an API call to the Tronscan API to retrieve transfer records for a specific wallet.

    Args:
        wallet (str): The wallet address for which to retrieve transfer records.
        query_index (int): The index of the transfer record to start retrieving from.
        n_xfers_per_call (int): The number of transfer records to retrieve per API call.

    Returns:
        dict: The JSON response from the API call.
    """
    url = f"https://api.tronscan.org/api/transfer?address={wallet}&start={query_index}&limit={n_xfers_per_call}"
    response = requests.get(url)
    return response.json()

def grab_call_xfers(json: Dict) -> List[Dict]:
    """
    Extracts the relevant information from the JSON response of an API call.

    Args:
        json (dict): The JSON response from the API call.

    Returns:
        list: The extracted transfer records.
    """
    return json['data']

def process_wallet_xfers(wallet: str, xfers: List[Dict]) -> None:
    """
    Processes and saves the transfer records to a CSV file.

    Args:
        wallet (str): The wallet address for which the transfer records were retrieved.
        xfers (list): The transfer records to process and save.
    """
    filename = f"{wallet}_transfers.csv"
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['From', 'To', 'Amount'])
        for xfer in xfers:
            writer.writerow([xfer['from'], xfer['to'], xfer['amount']])

def grab_wallet_xfers(wallet: str, n_xfers_per_call: int) -> None:
    """
    Retrieves transfer records for a specific wallet by making API calls to the Tronscan API.
    The transfer records are grabbed in batches, processed, and saved to a CSV file.

    Args:
        wallet (str): The wallet address for which to retrieve transfer records.
        n_xfers_per_call (int): The number of transfer records to grab per API call.
    """
    print(f'  Grabbing wallet transfers for {wallet}...')

    # First call (to get total # xfers)
    json = make_call(wallet, 0, n_xfers_per_call)
    n_xfers = json['total']
    n_loops = math.ceil(n_xfers / n_xfers_per_call)

    # Grab all the xfers in the first call
    xfers = grab_call_xfers(json)

    # Grab the remaining xfers via subsequent calls
    for l in range(1, n_loops):
        query_index = l * n_xfers_per_call
        json = make_call(wallet, query_index, n_xfers_per_call)
        xfers.extend(grab_call_xfers(json))

    process_wallet_xfers(wallet, xfers)

    print('  ...Done.')

def process_wallet_xfers(wallet: str, xfers: list) -> None:
    """
    This function processes the transfer records for a specific wallet and saves them to a CSV file for future reference.
    
    Args:
        wallet (str): The wallet address for which the transfer records were retrieved.
        xfers (list): The transfer records to process and save.
        
    Returns:
        None
    """
    print(f'Processing wallet for {wallet}...')

    output_list = [[wallet] + list(xfer.values()) for xfer in xfers]

    df = pd.DataFrame(output_list)

    with open('./data/trc20_xfers.csv', 'a') as f:
        df.to_csv(f, index=False, header=False)
        
    with open('./data/trc20_wallets_processed.txt', 'a') as f:
        f.write(wallet + '\n')

    print('...Done.')


def load_wallets() -> List[str]:
    """
    Retrieves a list of wallets from a CSV file and filters out the wallets that have already been processed.

    Returns:
    - A list of wallets that have not been processed yet.
    """
    # Read the CSV file containing the wallets
    df = pd.read_csv('./data/tron_wallets.csv')
    
    # Remove any duplicate wallets from the list
    wallets = list(dict.fromkeys(df.wallet.tolist()))  # preserves order

    # Read the file containing the wallets that have already been processed
    with open('./data/trc20_wallets_processed.txt', 'r') as f:
        text = f.read()
    
    # Split the text into a list of wallets
    wallets_already_processed = text.split('\n')

    # Filter out the wallets that have already been processed
    wallets_to_process = [wallet for wallet in wallets if wallet not in wallets_already_processed]

    return wallets_to_process


if __name__ == '__main__':
    n_xfers_per_call = 50
    wallets = load_wallets()
    
    s = requests.Session()

    xfers = []
    for wallet in wallets:
        xfers.append(grab_wallet_xfers(wallet, n_xfers_per_call))
