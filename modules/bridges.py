from helpers.data import bridges_data, chains_data
from eth_account.messages import encode_defunct
from helpers.utils import *
from eth_keys import keys

#+
class Main():

    def __init__(self, w3, logger, helper, max_slip):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'MAIN BRIDGE'
        self.contract_in = self.w3['ETH'].eth.contract(address=self.w3['ETH'].to_checksum_address(bridges_data['main']['contract_in']), abi=bridges_data['main']['ABI_in'])
        self.contract_out = self.w3['BASE'].eth.contract(address=self.w3['BASE'].to_checksum_address(bridges_data['main']['contract_out']), abi=bridges_data['main']['ABI_out'])
        self.max_slip = max_slip

    def deposit(self, private_key, amount, from_chain='ETH', to_chain='BASE', minus_fee=False, attempt=0, debug=False):

        if attempt > 3:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        value = int(amount * 10 ** 18)
        if minus_fee:
            value = int(value - (new_w3.eth.gas_price * 1.05 * 75000))

        is_creation = False
        args = account.address, value, 100000, is_creation, '0x01'

        func_ = getattr(self.contract_in.functions, 'depositTransaction')
        tx = make_tx(new_w3, account, value=value, func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx
        if tx == 'mv_error':
            return self.deposit(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug, attempt=attempt+1)

        elif isinstance(tx, str) and tx.startswith('newvalue'):
            _, new_value = tx.split("_")
            return self.deposit(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.deposit(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug, attempt=attempt)

        self.logger.log_success(f'{self.project} | Успешно задепозитил в BASE {value / (10 ** 18)} ETH, жду зачисления...', wallet=account.address)
        return new_w3.to_hex(hash)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='ETH', minus_fee=False, debug=False): #TODO PROXY

        account = self.w3['BASE'].eth.account.from_key(private_key)
        value = int(amount * 10 ** 18)

        func_ = getattr(self.contract_out.functions, 'initiateWithdrawal')

        args = account.address, value, "0x01"

        tx = make_tx(self.w3['BASE'], account, value=value, func=func_, args=args, minus_fee=minus_fee)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = self.w3['BASE'].eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3['ETH'], hash)
        if not tx_status:
            return self.withdraw(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

        self.logger.log_success(f'Main Bridge | Успешно вывел из BASE {amount} ETH, жду зачисления...', wallet=account.address)
        return self.w3['BASE'].to_hex(hash)

#+
class Orbiter():

    def __init__(self, w3, logger, helper, max_slip):
        self.w3 = w3
        self.helper = helper
        self.logger = logger
        self.chains = chains_data
        self.project = 'ORBITER'
        self.max_slip = max_slip

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', minus_fee=False, attempt = 0, debug=False):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        amount = 2 if amount > 2 else amount
        if minus_fee:
            amount = amount - float(new_w3.from_wei((new_w3.eth.gas_price * 1.05 * 21000), 'ether'))

        code = self.chains[to_chain]['orbiter']

        while True:
            amount = amount * 0.99999999999999
            value_ = int(amount * 10 ** 18)
            value = int(amount * 10 ** 18 // 10000 * 10000) + code
            if len(str(value_)) == len(str(value)) and str(value).endswith(str(code)):
                break

        if value < int(0.006 * 10 ** 18):
            if attempt > 8:
                return 'error'
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, attempt=attempt + 1, debug=debug)

        tx = make_tx(new_w3, account, value=value, to=new_w3.to_checksum_address(bridges_data['orbiter']['address']), minus_fee=minus_fee)

        if len(str(tx['value'])) != len(str(value)) or not str(tx['value']).endswith(str(code)):
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, attempt=attempt+1, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt, minus_fee=minus_fee, debug=debug)

        self.logger.log_success(f'{self.project} | Успешно перевёл из {from_chain} в {to_chain} {round(value / (10 ** 18), 6)} ETH, жду зачисления...', wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee)

#+
class Symbiosis():

    def __init__(self, w3, logger, helper, max_slip):
        self.w3 = w3
        self.logger = logger
        self.chains = chains_data
        self.helper = helper
        self.project = 'SYMBIOSIS'
        self.max_slip = max_slip

    def get_quote(self, from_chain, to_chain, amount, account):
        headers = {
            'accept': '*/*',
            'Content-Type': 'application/json',
        }

        json_data = {
            'tokenAmountIn': {
                'amount': str(int(amount)),
                'address': '',
                'symbol': 'ETH',
                'chainId': from_chain,
                'decimals': 18,
            },
            'tokenOut': {
                'address': '',
                'symbol': 'ETH',
                'chainId': to_chain,
                'decimals': 18,
            },
            'to': account.address,
            'from': account.address,
            'revertableAddress': account.address,
            'slippage': 500,
            'deadline': int(time.time() + 30 * 60),
        }

        for i in range(7):
            try:
                res = self.helper.fetch_url(url='https://api-v2.symbiosis.finance/crosschain/v1/swapping/exact_in', type='post', payload=json_data, headers=headers)
                if not res.get('code', 0) == 400:
                    return res
                time.sleep((1*i)+i)
            except:
                time.sleep((1*i)+i)
        return None

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', attempt = 0, minus_fee=False, debug=False):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        if attempt != 0:
            time.sleep(5)
        if attempt > 3:
            return 'error'

        chain_to_code = self.chains[to_chain]['id']
        chain_from_code = self.chains[from_chain]['id']

        amount_ = int(amount * 10 ** 18)
        if attempt == 0 and minus_fee:
            amount_ = int(amount_ - (new_w3.eth.gas_price * 1.1 * (450000 if from_chain != 'ARB' else 3500000)))


        quote = self.get_quote(chain_from_code, chain_to_code, amount_, account)
        if not quote:
            if debug:
                print(f"{self.project} | no quote")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        slippage = (1-(int(quote['tokenAmountOut']['amount'])/amount_))*100
        if slippage > self.max_slip:
            if debug:
                print(f"{self.project} | high slip")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        tx = make_tx(new_w3, account, value=int(quote['tx']['value']), to=new_w3.to_checksum_address(quote['tx']['to']), data=quote['tx']['data'], minus_fee=False)

        if tx == "low_native" or not tx:
            return tx
        elif isinstance(tx, str) and tx.startswith('newvalue'):
            _, new_value = tx.split("_")
            return self.deposit(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        self.logger.log_success( f"{self.project} | Успешно перевёл из {from_chain} в {to_chain} {round(int(quote['tx']['value']) / (10 ** 18), 6)} ETH, жду зачисления...", wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

#+
class Xyfinance():

    def __init__(self, w3, logger, helper, max_slip):
        self.w3 = w3
        self.logger = logger
        self.chains = chains_data
        self.helper = helper
        self.project = 'XY.FINANCE'
        self.max_slip = max_slip

    def get_tx(self, chain_from_code, chain_to_code, amount, account):

        url = f'https://router-api.xy.finance/xy_router/build_tx?src_chain_id={chain_from_code}&src_quote_token_address=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&src_quote_token_amount={str(amount)}&dst_chain_id={chain_to_code}&dst_quote_token_address=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&slippage={self.max_slip}&receiver={account.address}&bridge_provider=Ypool&src_bridge_token_address=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&dst_bridge_token_address=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&affiliate={self.w3["ETH"].to_checksum_address("0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191")}&commission_rate=10000'
        for i in range(7):
            try:
                res = self.helper.fetch_url(url=url, type='get')
                if res.get('success', False) is True:
                    return res
                time.sleep((1*i)+i)
            except:
                time.sleep((1*i)+i)
        return None

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', attempt = 0, minus_fee=False, debug=False):

        if attempt != 0:
            time.sleep(5)
        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        chain_to_code = self.chains[to_chain]['id']
        chain_from_code = self.chains[from_chain]['id']

        amount_ = int(amount * 10 ** 18)

        tx_ = self.get_tx(chain_from_code, chain_to_code, amount_, account)
        if not tx_:
            if debug:
                print(f"{self.project} | no tx (quote)")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        if attempt == 0 and minus_fee:
            gas = int(tx_['route']['estimated_gas']) if from_chain != 'ARB' else 2500000
            amount = amount - float(new_w3.from_wei((gas * new_w3.eth.gas_price * 1.1), 'ether'))
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        slippage = (1-(int(tx_['route']['dst_quote_token_amount'])/amount_))*100
        if slippage > self.max_slip:
            if debug:
                print(f"{self.project} | high slip")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        tx = make_tx(new_w3, account, value=int(tx_['tx']['value'], 16), to=new_w3.to_checksum_address(tx_['tx']['to']), data=tx_['tx']['data'], minus_fee=False)

        if tx == "low_native" or not tx:
            return tx
        elif isinstance(tx, str) and tx.startswith('newvalue'):
            _, new_value = tx.split("_")
            return self.bridge(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt, minus_fee=minus_fee, debug=debug)

        self.logger.log_success( f"{self.project} | Успешно перевёл из {from_chain} в {to_chain} {round(int(tx_['tx']['value'], 16) / (10 ** 18), 6)} ETH, жду зачисления...", wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

#+
class Socket():

    def __init__(self, w3, logger, helper, max_slip):
        self.w3 = w3
        self.logger = logger
        self.chains = chains_data
        self.helper = helper
        self.project = 'SOCKET'
        self.max_slip = max_slip
        self.headers = {
            'authority': 'api.socket.tech',
            'accept': 'application/json',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'api-key': '3005d5f5-fefb-49a3-841e-edb30b76ff6d',
            'content-type': 'application/json',
            'origin': 'https://layer3.xyz',
            'referer': 'https://layer3.xyz/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }

    def get_quote(self, chain_from, chain_to, amount, account):
        url = f'https://api.socket.tech/v2/quote?fromChainId={chain_from}&toChainId={chain_to}&fromTokenAddress=0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee&toTokenAddress=0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee&fromAmount={amount}&userAddress={account.address}&recipient={account.address}&singleTxOnly=true&uniqueRoutesPerBridge=true&sort=output&defaultSwapSlippage={self.max_slip}&defaultBridgeSlippage={self.max_slip}&feePercent=1&feeTakerAddress=0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191'
        for i in range(7):
            try:
                res = self.helper.fetch_url(url=url, type='get', headers=self.headers)
                if res.get('success', False) is True:
                    return res
                time.sleep((1*i)+i)
            except:
                time.sleep((1*i)+i)
        return None

    def build_tx(self, route):
        url = 'https://api.socket.tech/v2/build-tx'
        for i in range(7):
            try:
                payload = {"route": route}
                res = self.helper.fetch_url(url=url, type='post', payload=payload, headers=self.headers)
                if res.get('success', False) is True:
                    return res
                time.sleep((1*i)+i)
            except:
                time.sleep((1*i)+i)
        return None

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', attempt = 0, minus_fee=False, debug=False):

        if attempt != 0:
            time.sleep(5)
        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        chain_to_code = self.chains[to_chain]['id']
        chain_from_code = self.chains[from_chain]['id']

        amount_ = int(amount * 10 ** 18)

        if attempt == 0 and minus_fee:
            amount_ = int(amount_ - (new_w3.eth.gas_price * 1.1 * (450000 if from_chain != 'ARB' else 2500000)))


        quote = self.get_quote(chain_from_code, chain_to_code, amount_, account)
        if not quote:
            if debug:
                print(f"{self.project} | no quote")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)
        route = quote['result']['routes'][0]

        slippage = (1-(int(route['toAmount'])/int(route['fromAmount'])))*100
        if slippage > self.max_slip:
            if debug:
                print(f"{self.project} | high slip")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_ = self.build_tx(route)

        if not tx_:
            if debug:
                print(f"{self.project} | no tx ")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx = make_tx(new_w3, account, value=int(tx_['result']['value'], 16), to=new_w3.to_checksum_address(tx_['result']['txTarget']), data=tx_['result']['txData'], minus_fee=False)

        if tx == "low_native" or not tx:
            return tx
        elif isinstance(tx, str) and tx.startswith('newvalue_'):
            _, new_value = tx.split("_")
            return self.bridge(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt, minus_fee=minus_fee, debug=debug)

        self.logger.log_success( f"{self.project} | Успешно перевёл из {from_chain} в {to_chain} {round(int(tx_['result']['value'], 16) / (10 ** 18), 6)} ETH, жду зачисления...", wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

#+
class Layerswap():

    def __init__(self, w3, logger, helper, max_slip):
        self.w3 = w3
        self.logger = logger
        self.chains = chains_data
        self.helper = helper
        self.project = 'LayerSwap'
        self.max_slip = max_slip
        self.headers = {
            'authority': 'bridge-api.layerswap.io',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'access-control-allow-origin': '*',
            #'authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjFFOTg0RkJCQkFDODlGNDkxOUQ2OTdDQzFBM0IzQkY1QjUzOEIzOEFSUzI1NiIsIng1dCI6IkhwaFB1N3JJbjBrWjFwZk1HanM3OWJVNHM0byIsInR5cCI6ImF0K2p3dCJ9.eyJpc3MiOiJodHRwczovL2lkZW50aXR5LWFwaS5sYXllcnN3YXAuaW8iLCJuYmYiOjE2OTM3MzU2NTksImlhdCI6MTY5MzczNTY1OSwiZXhwIjoxNjkzODIyMDU5LCJhdWQiOiJsYXllcnN3YXBfYnJpZGdlIiwic2NvcGUiOlsibGF5ZXJzd2FwX2JyaWRnZS51c2VyIiwib2ZmbGluZV9hY2Nlc3MiXSwiYW1yIjpbImNyZWRlbnRpYWxsZXNzIl0sImNsaWVudF9pZCI6ImxheWVyc3dhcF9icmlkZ2VfdWkiLCJzdWIiOiIxMjg3OTM3IiwiYXV0aF90aW1lIjoxNjkzNzM1NjU5LCJpZHAiOiJsb2NhbCIsImVtYWlsIjoiZ3Vlc3R1c2VyZDBlNTc2YTY0ZjljNGRjODgyNTUzMjZlMDQwZjVjM2ZAbGF5ZXJzd2FwLmlvIiwidWlkIjoiMTI4NzkzNyIsInV0eXBlIjoiZ3Vlc3QifQ.hz-pB5Fp_MUcVe3aZTyWIdR8BiX94T27Qcw6N_u0SunIIMAS1IUd4jE9IoF2evSqTvS8vB9d2ANGDQvQ2u4dV3otXeZOZ8jp1ejOhZP2gui6itliWhHRlp-htTfj-d9pg_f2neR2s86pCIMKPoWg28i3WPzZQzmAlCrZbPz_3PONFwpTDZyFppBHfheyPfEr9EibR73wRhObye1sErTQsHaUtIhNq_h8cXzaJ8uFVibh90hsQiYKjCjUCPANKc_7vLRXlbCPn5NoD-Wwksh3BEJ3Rm6qexgholoCjBJ68kyfRb-cb3Nc-Qr9677hzZ8_u5DKeAy9bPpNZhi7DesPqg',
            'origin': 'https://www.layerswap.io',
            'referer': 'https://www.layerswap.io/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }

    def get_headers(self, auth=False):
        headers = self.headers
        if auth:
            headers['authorization'] = f"Bearer {auth}"
        return headers

    def get_auth(self):
        data = {
            'client_id': 'layerswap_bridge_ui',
            'grant_type': 'credentialless',
        }
        for i in range(5):
            try:
                res = self.helper.fetch_url(url='https://identity-api.layerswap.io/connect/token', type='post', headers=self.headers, data=data)
                return res['access_token']
            except:
                time.sleep((1 * i) + i)
        return None

    def get_swap(self, chain_from, chain_to, amount, account, auth):
        chain_to = self.chains[chain_to]['layer_id']
        chain_from = self.chains[chain_from]['layer_id']
        url = 'https://bridge-api.layerswap.io//api/swaps'
        payload = {"amount":amount,"source":chain_from,"destination":chain_to,"source_asset":"ETH","destination_asset":"ETH","source_address":account.address,"destination_address":account.address,"refuel":False}
        for i in range(5):
            try:
                res = self.helper.fetch_url(url=url, type='post', headers=self.get_headers(auth=auth), payload=payload)
                if res.get('error') is None:
                    return res['data']['swap_id']
                time.sleep((1 * i) + i)
            except:
                time.sleep((1 * i) + i)
        return None

    def show_swap_data(self, swap_id, auth):

        url = f'https://bridge-api.layerswap.io//api/swaps/{swap_id}'
        for i in range(5):
            try:
                res = self.helper.fetch_url(url=url, type='get', headers=self.get_headers(auth=auth))
                return res
            except:
                time.sleep((1 * i) + i)
        return None

    def get_address(self, chain_from, auth):
        chain_from = self.chains[chain_from]['layer_id']

        url = f'https://bridge-api.layerswap.io//api/deposit_addresses/{chain_from}?source=1'
        for i in range(5):
            try:
                res = self.helper.fetch_url(url=url, type='get', headers=self.get_headers(auth=auth))
                return res['data']['address']
            except:
                time.sleep((1 * i) + i)
        return None

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', attempt=0, minus_fee=False, debug=False):

        if attempt != 0:
            time.sleep(1)
        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        amount_ = int(amount * 10 ** 18)
        if attempt == 0 and minus_fee:
            amount_ = int(amount_ - (new_w3.eth.gas_price * 1.1 * (450000 if from_chain != 'ARB' else 2500000)))
            amount = float(amount_ / (10 ** 18))

        auth = self.get_auth()
        if not auth:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain,attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        swap = self.get_swap(from_chain, to_chain, amount, account, auth)
        if not swap:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        swap_data = self.show_swap_data(swap, auth)
        if not swap_data:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain,attempt=attempt + 1, minus_fee=minus_fee, debug=debug)
        total_amount = int((float(swap_data['data']['requested_amount']) + float(swap_data['data']['fee'])) * 10 ** 18)
        actual_balance = new_w3.eth.get_balance(account.address)

        if total_amount > actual_balance:
            return self.bridge(private_key=private_key, amount=amount*0.9, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        address = '0x2fc617e933a52713247ce25730f6695920b3befe'#self.get_address(from_chain, auth)

        tx = make_tx(new_w3, account, value=total_amount, to=new_w3.to_checksum_address(address))

        if tx == "low_native" or not tx:
            return tx
        elif isinstance(tx, str) and tx.startswith('newvalue_'):
            _, new_value = tx.split("_")
            return self.bridge(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt, minus_fee=minus_fee, debug=debug)

        self.logger.log_success(f"{self.project} | Успешно перевёл из {from_chain} в {to_chain} {float(swap_data['data']['requested_amount']) + float(swap_data['data']['fee'])} ETH, жду зачисления...", wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee,debug=debug)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee,debug=debug)

#+
class Lifi():

    def __init__(self, w3, logger, helper, max_slip):
        self.w3 = w3
        self.logger = logger
        self.chains = chains_data
        self.helper = helper
        self.project = 'LI.FI'
        self.max_slip = max_slip

    def get_routes(self, chain_from_code, chain_to_code, amount, account):
        payload = {"fromChainId":chain_from_code,"fromAmount":str(amount),"fromTokenAddress":"0x0000000000000000000000000000000000000000","toChainId":chain_to_code,"toTokenAddress":"0x0000000000000000000000000000000000000000","fromAddress":account.address,"toAddress":account.address,"options":{"slippage":max(0.005, self.max_slip/100),"maxPriceImpact":max(1, self.max_slip),"allowSwitchChain":True,"bridges":{"deny":[]},"exchanges":{"deny":[]},"order":"RECOMMENDED","insurance":False, 'referrer': '0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191', 'fee': 0.01, "integrator":"ch.dao"}}
        url = 'https://li.quest/v1/advanced/routes'
        for i in range(7):
            try:
                res = self.helper.fetch_url(url=url, type='post', payload=payload)
                return res['routes'][0]['steps'][0]
            except:
                time.sleep((1*i)+i)
        return None

    def get_tx(self, payload):
        url = 'https://li.quest/v1/advanced/stepTransaction'
        # json_data = {
        #     'type': payload['type'],
        #     'id': payload['id'],
        #     'tool': payload['tool'],
        #     'toolDetails': payload['toolDetails'],
        #     'action': payload['action'],
        #     'estimate': payload['estimate'],
        #     'includedSteps': payload['includedSteps'],
        #     'integrator': payload['integrator'],
        #     #'execution': {'status': 'PENDING','process': [{'type': 'CROSS_CHAIN','startedAt': int(time.time()),'message': 'Preparing bridge transaction.','status': 'STARTED',},],},
        # }
        for i in range(7):
            try:
                res = self.helper.fetch_url(url=url, type='post', payload=payload)
                return res['transactionRequest']
            except:
                time.sleep((1 * i) + i)
        return None

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', attempt = 0, minus_fee=False, debug=False):

        if attempt != 0:
            time.sleep(5)
        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        chain_to_code = self.chains[to_chain]['id']
        chain_from_code = self.chains[from_chain]['id']

        amount_ = int(amount * 10 ** 18)

        route = self.get_routes(chain_from_code, chain_to_code, amount_, account)
        if not route:
            if debug:
                print(f"{self.project} | no route (quote)")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_ = self.get_tx(route)
        if not tx_:
            if debug:
                print(f"{self.project} | no tx (quote)")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt = attempt + 1, minus_fee=minus_fee, debug=debug)

        if attempt == 0 and minus_fee:
            gas = int(tx_['route']['estimated_gas']) if from_chain != 'ARB' else 2500000
            amount = amount - float(new_w3.from_wei((gas * new_w3.eth.gas_price * 1.1), 'ether'))
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx = make_tx(new_w3, account, value=int(tx_['value'], 16), to=new_w3.to_checksum_address(tx_['to']), data=tx_['data'], minus_fee=False)

        if tx == "low_native" or not tx:
            return tx
        elif isinstance(tx, str) and tx.startswith('newvalue'):
            _, new_value = tx.split("_")
            return self.bridge(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt, minus_fee=minus_fee, debug=debug)

        self.logger.log_success(f"{self.project} | Успешно перевёл из {from_chain} в {to_chain} {round(int(tx_['value'], 16) / (10 ** 18), 6)} ETH, жду зачисления...", wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

#+
class Omnibtc():

    def __init__(self, w3, logger, helper, max_slip):

        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.logger = logger
        self.project = 'OMNIBTC'
        self.headers = {
            'authority': 'crossswap.coming.chat',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://app.omnibtc.finance',
            'referer': 'https://app.omnibtc.finance/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'x-sdk-version': '3',
        }
        self.chains = {"LINEA": 'linea', "ARB": 'arbitrum', "OPT": 'optimism', "ETH": 'ethereum', "BASE": 'base', "ERA": 'zksync era'}

    def register_ref(self, account, new_w3):
        self.helper.fetch_url('https://api.omnibtc.finance/omnireward/checkInviteCode?inviteCode=4tw5GLc2', type='get', headers=self.headers)
        timestamp = int(time.time())
        message_ = f"Address: {account.address}\nTimeStamp: {str(timestamp)} \nReferral Code: 4tw5GLc2 \nOperation: Welcome to join the Reward Event of OmniSwap"
        message = message_.encode()
        message_to_sign = encode_defunct(primitive=message)
        signed_message = new_w3.eth.account.sign_message(message_to_sign, private_key=account.key.hex())
        sig = signed_message.signature.hex()
        priv_key = keys.PrivateKey(account.key)
        pub_key = priv_key.public_key
        pub_key = f"0x04{pub_key.to_hex()[2:]}"
        json_data = {
            'content': f'Address: {account.address}\nTimeStamp: {timestamp} \nReferral Code: 4tw5GLc2 \nOperation: Welcome to join the Reward Event of OmniSwap',
            'sign': sig,
            'inviteCode': '4tw5GLc2',
            'publicKey': pub_key,
            'address': account.address,
            'time': timestamp,
        }
        for i in range(3):
            try:
                result = self.helper.fetch_url(url='https://api.omnibtc.finance/omnireward/verifyAddress', type='post', headers=self.headers, payload=json_data, retries=5, timeout=5)
                return result['accessToken']
            except:
                time.sleep(i * 1)
        return None

    def get_quote(self, chain_from_, chain_to_, amount, account):
        params = {
            'fromChain': chain_from_,
            'toChain': chain_to_,
            'fromAssetId': '-1',
            'fromToken': '0x0000000000000000000000000000000000000000',
            'toAssetId': '-1',
            'toToken': '0x0000000000000000000000000000000000000000',
            'fromAddress': account.address,
            'fromAmount': str(amount),
            'toAddress': account.address,
            'slippage': str(int(self.max_slip)/100),
            'srcSlippage': str(int(self.max_slip)/100),
            'publicKey': '',
            'platform': 'web',
        }

        for i in range(3):
            try:
                result = self.helper.fetch_url(url='https://crossswap.coming.chat/v1/quoteList', type='get', headers=self.headers, params=params, retries=5, timeout=5)
                if result == 'unsupported swap':
                    return None
                return result['quoteList']
            except:
                time.sleep(i * 1)
        return None

    def bridge(self, private_key, amount, from_chain='None', to_chain='BASE', attempt=0, minus_fee=False, debug=False):

        if attempt != 0:
            time.sleep(5)
        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3[from_chain])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[from_chain]

        account = new_w3.eth.account.from_key(private_key['private_key'])

        auth = self.register_ref(account, new_w3)

        try:
            headers = self.headers
            headers['Authorization'] = auth
            self.helper.fetch_url('https://api.omnibtc.finance/omnireward/myInfo', type='get', headers=headers)
        except:
            pass

        chain_to_ = self.chains[to_chain]
        chain_from_ = self.chains[from_chain]

        amount_ = int((amount-0.001) * 10 ** 18)

        quote = self.get_quote(chain_from_, chain_to_, amount_, account)
        if not quote:
            if debug:
                print(f"{self.project} | no quote")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx__ = random.choice(quote)['steps'][-1]

        slippage = 100 - (int(tx__['estimate']['toAmount']) / int(tx__['estimate']['fromAmount']) * 100)
        if slippage > self.max_slip:
            if debug:
                print(f"{self.project} | high slip")
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_ = tx__['txData']

        tx = make_tx(new_w3, account, value=int(tx_['value']), to=new_w3.to_checksum_address(tx_['to']), data=tx_['data'], minus_fee=False)

        if tx == "low_native" or not tx:
            return tx
        elif isinstance(tx, str) and tx.startswith('newvalue'):
            _, new_value = tx.split("_")
            return self.bridge(private_key=private_key, amount=float(new_value), from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee, debug=debug)

        hash, new_amount = send_tx(new_w3, account, tx)
        if not hash:
            return self.bridge(private_key=private_key, amount=new_amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt + 1, minus_fee=minus_fee, debug=debug)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.bridge(private_key=private_key, amount=amount, from_chain=from_chain, to_chain=to_chain, attempt=attempt, minus_fee=minus_fee, debug=debug)

        self.logger.log_success(f"{self.project} | Успешно перевёл из {from_chain} в {to_chain} {round(amount, 6)} ETH, жду зачисления...", wallet=account.address)
        return new_w3.to_hex(hash)

    def deposit(self, private_key, amount, from_chain, to_chain='BASE', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee,
                           debug=debug)

    def withdraw(self, private_key, amount, from_chain='BASE', to_chain='None', minus_fee=False, debug=False):

        return self.bridge(private_key, amount, from_chain=from_chain, to_chain=to_chain, minus_fee=minus_fee,
                           debug=debug)

def initialize_bridges(classes_to_init, w3, logger, helper, max_bridge_slippage):
    available_swaps = {
         "Main" : Main,
         "Orbiter" : Orbiter,
         "Symbiosis": Symbiosis,
         "Xyfinance": Xyfinance,
         "Socket": Socket,
         "Layerswap": Layerswap,
         "Lifi": Lifi,
         "Omnibtc": Omnibtc,
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, logger, helper, max_bridge_slippage)

    return initialized_objects
