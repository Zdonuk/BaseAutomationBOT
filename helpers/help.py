import random
from web3 import Web3
import requests, time, tls_client
from helpers.data import tokens_data_, CONTRACT_DATA, DATA_ABI
from settings import settings_dict
from helpers.utils import get_balance

class helper():

    def __init__(self, use_tls=True, print_out=False):

        self.w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/base'))
        self.print_out = print_out
        if use_tls:
            self.tls_clients = ['safari_15_3','safari_15_6_1','safari_16_0','firefox108','chrome112']
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(CONTRACT_DATA),abi=DATA_ABI)
        self.proxy = {'tls': None, 'requests': None}

    def check_proxy(self):
        headers = {
            'authority': 'api.whatismyip.com',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://www.whatismyip.com',
            'referer': 'https://www.whatismyip.com/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }
        proxy_ = f"http://{settings_dict['requests_proxy']}"
        proxy = {"http": proxy_, "https": proxy_}
        url_proxy = 'https://api.ipify.org'
        url_check = 'https://api.whatismyip.com/proxy-check.php'
        try:
            res_proxy = self.fetch_url(url_proxy, type='get', proxies=proxy, retries=5, timeout=10, text=True)
            if res_proxy == settings_dict['requests_proxy'].split('@')[1].split(":")[0]:
                self.proxy = {'tls': proxy_, 'requests': proxy}
                res_check = self.fetch_url(url_check, type='post', proxies=proxy, headers=headers, retries=3, timeout=5)
                try:
                    is_proxy = res_check['is_proxy']
                    conutry = res_check['country_code']
                    return is_proxy, conutry
                except:
                    return 'yes', 'UNKNOWN'
            else:
                raise Exception
        except Exception:
            self.proxy = {'tls': None, 'requests': None}
            return 'no', None

    def fetch_url(self, url, type, payload=None, headers=None, params=None, data=None, cookies=None, proxies=None, content=False, text=False, timeout=60, retries=15):
        for i in range(retries):
            if proxies == None:
                proxies = self.proxy['requests']
            try:
                if type == "get":
                    response = requests.get(url, timeout=timeout, headers=headers, params=params, cookies=cookies, proxies=proxies)
                    if content:
                        return response.content
                    if text:
                        return response.text
                    return response.json()
                elif type == "post":
                    response = requests.post(url, timeout=timeout, json=payload, headers=headers, params=params, data=data, cookies=cookies, proxies=proxies)
                    if text:
                        return response.text
                    return response.json()
            except Exception:
                time.sleep(i * 1)
        return

    def get_tls_session(self):

        return tls_client.Session(client_identifier=random.choice(self.tls_clients))

    def fetch_tls(self, url, type, session, payload=None, headers=None, params=None, proxies=None, text=False):
        for i in range(15):
            if proxies == None:
                proxies = self.proxy['tls']
            try:
                if type == "get":
                    response = session.get(url, headers=headers, params=params, proxy=proxies)
                    if text:
                        return response.text
                    return response.json()
                elif type == "post":
                    response = session.post(url, json=payload, headers=headers, params=params, proxy=proxies)
                    if text:
                        return response.text
                    return response.json()
            except:
                time.sleep(i * 1)
        return

    def get_user_tokens(self, address, filter_len=12, retries=25, sleep_time=10, reserved=False):
        if reserved:
            return self.get_user_tokens_reserved(address)
        for i in range(retries):
            try:
                tokens_ = self.contract_data.functions.getBalances(self.w3.to_checksum_address(address)).call()
                tokens = {}
                for token in tokens_:
                    if not tokens.get(token[1].upper()) or tokens.get(token[1].upper(), {}).get('balance', 0) == 0:
                        tokens[token[1].upper()] = {"balance": token[3], "address": token[0], "symbol": token[1].upper(), "decimals": token[2], 'amount': float(token[3]/(10**token[2]))}
                return tokens
            except Exception:
                time.sleep(i * 1)
        return {}

    def get_user_tokens_reserved(self, address):
        for i in range(3):
            try:
                tokens = {}
                for token, data in tokens_data_.items():
                    if token != 'ETH':
                        balance = get_balance(self.w3, None, data['address'], address=address)
                    else:
                        balance = self.w3.eth.get_balance(address)
                    tokens[token] = {"balance": balance, "address": data['address'], "symbol": data['symbol'],"decimals": data['decimal'], 'amount': balance / (10 ** data['decimal'])}
                return tokens
            except:
                pass
        return {}

    def get_all_tokens(self):
        for i in range(5):
            try:
                result = self.fetch_url(url='https://raw.githubusercontent.com/izumiFinance/izumi-tokenList/main/build/tokenList.json', type='get')
                tokens = {}
                for r in result:
                    if 8453 in r['chains']:
                        tokens[r['symbol']] = r['contracts']['8453']
                        tokens[r['symbol']]['symbol'] = r['symbol']
                return tokens
            except:
                time.sleep(i*1)
        return {}

    def get_prices(self):
        token_symbols = list(self.get_all_tokens().keys())
        params = {'t': token_symbols}
        for i in range(5):
            try:
                result = self.fetch_url(url='https://api.izumi.finance/api/v1/token_info/price_info/', type='get', params=params)
                self.prices = result['data']
                return result['data']
            except:
                time.sleep(i * 1)
        return self.get_prices_reserved()

    def get_prices_reserved(self, ids_=None):
        if not ids_:
            ids = [data['id'] for data in tokens_data_.values()]
        else:
            ids = ids_
        ids_str = '%2C'.join(ids)
        id_to_symbol = {data['id']: symbol for symbol, data in tokens_data_.items()}
        for i in range(5):
            try:
                url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd'
                res = self.fetch_url(url=url, type='get')
                prices = {}
                for token_id, price in res.items():
                    symbol = id_to_symbol.get(token_id)
                    if symbol:
                        prices[symbol] = float(price['usd'])
                return prices
            except:
                time.sleep(i * 1)
        self.prices = {}
        return {}

    def get_prices_combined(self):
        try:
            prices1 = {}
            prices2 = self.get_prices_reserved()

            for key, value in prices2.items():
                if key not in prices1 or prices1[key] == 0:
                    prices1[key] = value
            prices1 = {k: v for k, v in prices1.items() if v != 0}
            prices1['USDC'] = 1
            prices1['USD+'] = 1
            eth = prices1['ETH']
            return prices1
        except Exception:
            return self.get_prices_combined()

    def get_web3(self, proxy, w3, attempt = 0):

        if attempt > 25:
            return

        try:
            proxy_full = 'http://' + proxy
            proxy = {'http': proxy_full,'https': proxy_full}
            session = requests.Session()
            session.proxies = proxy

            rpc = str(w3.provider).replace('RPC connection ', '')

            web3 = Web3(Web3.HTTPProvider(rpc, session=session))
            connection_established = web3.is_connected()
            if connection_established:
                return web3
            else:
                raise Exception
        except Exception:
            time.sleep(5)

        return self.get_web3(proxy=proxy, w3=w3, attempt=attempt+1)

if __name__ == "__main__":

    help = helper()


    prices = help.get_prices_combined()
    print(prices)

    tokens = help.get_user_tokens('0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191')

    for token in tokens.items():
        print(token)