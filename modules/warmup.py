import json, hashlib
from helpers.data import chains_data, warmup_data
from helpers.utils import *
from web3._utils.contracts import encode_abi

class Mintfun():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'MINTFUN'
        #self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract_campaign']), abi=other_data[self.project]['ABI'])

    def get_collections(self, chain):

        url = f'https://mint.fun/api/mintfun/feed/free?range=24h&chain={chain}'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                return result['collections']
            except:
                time.sleep(i*1)
        return []

    def get_data(self, collection, chain):
        url = f'https://mint.fun/api/mintfun/contract/{chain}:{collection}/transactions'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                for tx in result['transactions']:
                    if int(tx['nftCount']) == 1:
                        return tx
            except:
                time.sleep(i*1)
        return None

    def main(self, chain_from, private_key, attempt = 0):

        if attempt > 10:
            return 'error'

        account = self.w3.eth.account.from_key(private_key)
        chain_code = chains_data[chain_from]['id']

        collections = self.get_collections(chain_code)
        if not collections:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)
        collection = random.choice(collections)

        _, contract = collection['contract'].split(':')
        tx_data = self.get_data(contract, chain_code)
        if not tx_data:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        if int(tx_data['ethValue']) > 0:
            return self.main(chain_from=chain_from, private_key=private_key, attempt = attempt + 1)

        tx = make_tx(self.w3, account, data=tx_data['callData'], to=tx_data['to'], gas_multiplier=1, value=0)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt = attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно заминтил NFT {collection['name']} за 0 ETH",account.address)
        return self.w3.to_hex(hash)

class Lido():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'LIDO'

    def main(self, chain_from, private_key, attempt = 0):

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        tx = make_tx(self.w3, account, data='0xa1903eab0000000000000000000000000000000000000000000000000000000000000000', to=self.w3.to_checksum_address('0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84'), gas_multiplier=1, value=value)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt = attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно внёс в стейкинг {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Starknet():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.help = helper
        self.project = 'STARKNET BRIDGE'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data['STARKNET']['contract']), abi=warmup_data['STARKNET']['ABI'])

    def get_message_fee(self, stark_address, value):
        url = f'https://alpha-mainnet.starknet.io/feeder_gateway/estimate_message_fee?blockNumber=pending'
        for i in range(5):
            try:
                payload = {"from_address":"993696174272377493693496825928908586134624850969","to_address":"0x073314940630fd6dcda0d772d4c972c4e0a9946bef9dabf4ef84eda8ef542b82","entry_point_selector":"0x2d757788a8d8d6f21d1cd40bce38a8222d70654214e96ff95d8086e684fbee5","payload":[f"0x{stark_address}",value,"0x0"]}
                result = self.help.fetch_url(url=url, type='post', payload=payload)
                return int(result['overall_fee'])
            except :
                time.sleep(i * 1)
        return 0

    def main(self, chain_from, private_key, attempt = 0):

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        hash_object = hashlib.sha256(account.address.encode())
        stark_address = hash_object.hexdigest()
        stark_address = stark_address[:63]

        fee = self.get_message_fee(stark_address, hex(value))


        dep_func = self.contract.functions.deposit(value, int(stark_address, 16))
        dep_data = encode_abi(self.w3, dep_func.abi, [value, int(stark_address, 16)])
        data = f"0xe2bbb158{dep_data[2:]}"

        tx = make_tx(self.w3, account, value=value+fee, data=data, to=self.w3.to_checksum_address(warmup_data['STARKNET']['contract']))

        if tx == "low_native" or not tx or tx == 'error':
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        self.logger.log_success(f"{self.project} | Успешно сделал бридж {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Zora():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'ZORA BRIDGE'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data['ZORA']['contract']), abi=warmup_data['ZORA']['ABI'])

    def main(self, chain_from, private_key, attempt = 0):

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        func_ = getattr(self.contract.functions, 'depositTransaction')
        args = account.address, 0, 100000, False, '0x'
        tx = make_tx(self.w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx or tx == 'error':
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        self.logger.log_success(f"{self.project} | Успешно сделал бридж {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Optimismbridge():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'OPTIMISM BRIDGE'

    def main(self, chain_from, private_key, attempt=0):
        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        if chain_from == 'ETH':

            data = '0xb1a1a8820000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000'
            to = self.w3.to_checksum_address('0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1')

            tx = make_tx(self.w3, account, data=data, to=to, gas_multiplier=1.1, value=value)

            if tx == "low_native" or not tx:
                return tx

            sign = account.sign_transaction(tx)
            hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
            tx_status = check_for_status(self.w3, hash)
            if not tx_status:
                return self.main(chain_from=chain_from, private_key=private_key, attempt = attempt + 1)
            self.logger.log_success(f"{self.project} | Успешно забриджил в OPTIMISM {_value} ETH", account.address)
        else:

            contract = self.w3.eth.contract( address=self.w3.to_checksum_address(warmup_data['OPTIMISM']['contract']), abi=warmup_data['OPTIMISM']['ABI'])
            func_ = getattr(contract.functions, 'withdraw')

            args = self.w3.to_checksum_address('DeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000'), value, 0, "0x"

            tx = make_tx(self.w3, account, value=value, func=func_, args=args)

            if tx == "low_native" or not tx:
                return tx

            sign = account.sign_transaction(tx)
            hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
            tx_status = check_for_status(self.w3, hash)
            if not tx_status:
                return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
            self.logger.log_success(f"{self.project} | забриджил в ETH MAINNET {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Arbitrumbridge():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'ARBITRUM BRIDGE'

    def main(self, chain_from, private_key, attempt=0):
        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        if chain_from == 'ETH':
            data = '0x439370b1'
            to = [{'address': self.w3.to_checksum_address('0xc4448b71118c9071Bcb9734A0EAc55D18A153949'), "chain": 'ARB NOVA'}, {'address': self.w3.to_checksum_address('0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f'), "chain": 'ARB ONE'}]
            to = random.choice(to)
        else:
            to = {"address": '0x0000000000000000000000000000000000000064', "chain": 'ETH MAINNET'}
            data = f'0x25e16063000000000000000000000000{account.address[2:]}'

        tx = make_tx(self.w3, account, data=data, to=to['address'], gas_multiplier=1, value=value)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt = attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно забриджил в {to['chain']} {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Polygonbridge():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'POLYGON BRIDGE'

    def main(self, chain_from, private_key, attempt=0):
        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        data = f'0x4faa8a26000000000000000000000000{account.address[2:]}'
        to = [{'address': self.w3.to_checksum_address('0xA0c68C638235ee32657e8f720a23ceC1bFc77C77'), "chain": 'POLYGON'},]
        to = random.choice(to)

        tx = make_tx(self.w3, account, data=data, to=to['address'], gas_multiplier=1, value=value)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt = attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно забриджил в {to['chain']} {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Aave():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'AAVE'

    def main(self, chain_from, private_key, attempt=0):
        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data['AAVE'][chain_from]['contract']), abi=warmup_data['AAVE'][chain_from]['ABI'])

        func_ = getattr(contract.functions, 'depositETH')

        args = self.w3.to_checksum_address(warmup_data['AAVE'][chain_from]['pool']), account.address, 0

        tx = make_tx(self.w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно сделал SUPPLY на сумму {_value} ETH", account.address)
        return self.w3.to_hex(hash)

class Approve():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'RANDOM APPROVE'
        self.headers = {
                'authority': 'api.uniswap.org',
                'accept': '*/*',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'text/plain;charset=UTF-8',
                'origin': 'https://app.uniswap.org',
                'referer': 'https://app.uniswap.org/',
                'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            }

    def get_tokens(self, chain):
        url = 'https://gateway.ipfs.io/ipns/tokens.uniswap.org'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                tokens = []
                for token in result['tokens']:
                    if int(token['chainId']) == chain:
                        tokens.append(token)
                return tokens
            except:
                time.sleep(i * 1)
        return []

    def main(self, chain_from, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        account = self.w3.eth.account.from_key(private_key)
        chain_code = chains_data[chain_from]['id']
        tokens = self.get_tokens(chain_code)

        token = random.choice(tokens)

        random_dapp = random.choice(list(warmup_data['APPROVE'][chain_from]))
        dapp_address = self.w3.to_checksum_address(warmup_data['APPROVE'][chain_from][random_dapp])

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(token['address']), abi=TOKEN_ABI)
        func_ = getattr(contract.functions, 'approve')
        args = dapp_address, random.randint(10000000000000000000000000000000, 115792089237316195423570985008687907853269984665640564039457584007913129)
        tx = make_tx(self.w3, account, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно сделал APPROVE токена {token['symbol']} для {random_dapp}",account.address)
        return self.w3.to_hex(hash)

class Uniswap():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'UNISWAP'
        self.headers = {
                'authority': 'api.uniswap.org',
                'accept': '*/*',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'text/plain;charset=UTF-8',
                'origin': 'https://app.uniswap.org',
                'referer': 'https://app.uniswap.org/',
                'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            }

    def get_tokens(self, chain):
        url = 'https://gateway.ipfs.io/ipns/tokens.uniswap.org'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                tokens = []
                for token in result['tokens']:
                    if int(token['chainId']) == chain:
                        tokens.append(token)
                return tokens
            except:
                time.sleep(i * 1)
        return []

    def get_quote(self, token, amount, chain, account):
        url = 'https://api.uniswap.org/v2/quote'
        payload = {"tokenInChainId":chain,"tokenIn":"ETH","tokenOutChainId":chain,"tokenOut":token,"amount":str(amount),"type":"EXACT_INPUT","configs":[{"useSyntheticQuotes":False,"recipient":account.address,"swapper":account.address,"routingType":"DUTCH_LIMIT"},{"protocols":["V2","V3","MIXED"],"routingType":"CLASSIC"}]}
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='post', payload=payload, headers=self.headers)
                return result
            except:
                time.sleep(i * 1)
        return None

    def main(self, chain_from, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)
        chain_code = chains_data[chain_from]['id']
        tokens = self.get_tokens(chain_code)

        token = random.choice(tokens)

        quote = self.get_quote(token['address'], value, chain_code, account)
        if quote.get('detail', '').lower() == 'No quotes available'.lower():
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        command = '0x0b00'
        address_this = self.w3.to_checksum_address("0x0000000000000000000000000000000000000002")
        address_sender = self.w3.to_checksum_address("0x0000000000000000000000000000000000000001")
        amount_out = int(int(quote['quote']['quote']))
        deadline = int(time.time()) + 30 * 60
        ABI_wrap = '[{"inputs":[{"name":"recipient","type":"address"},{"name":"amountMin","type":"uint256"}],"name":"WRAP_ETH","type":"function"}]'
        wrap_contract = self.w3.eth.contract(abi=ABI_wrap)
        wrap_func = wrap_contract.functions.WRAP_ETH(address_this, int(quote['quote']['amount']))
        wrap_data = encode_abi(self.w3, wrap_func.abi, [address_this, int(quote['quote']['amount'])])

        path = [self.w3.to_checksum_address(quote['quote']['route'][0][0]['tokenIn']['address']), self.w3.to_checksum_address(quote['quote']['route'][0][0]['tokenOut']['address'])]
        try:
            fee = int(quote['quote']['route'][0][0]['fee'])
        except:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
        fee_encoded = '{:06X}'.format(fee)
        args = address_sender, int(quote['quote']['amount']), amount_out, path, False
        ABI_sub = '[{"inputs":[{"name":"recipient","type":"address"},{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"payerIsSender","type":"bool"}],"name":"V2_SWAP_EXACT_IN","type":"function"}]'
        sub_contract = self.w3.eth.contract(abi=ABI_sub)
        sub_func = sub_contract.functions.V2_SWAP_EXACT_IN(*args)
        sub_data = encode_abi(self.w3, sub_func.abi, args)

        sub_data = sub_data[:384]

        sub_data = f"{sub_data}2b{path[0][2:]}{fee_encoded}{path[1][2:]}000000000000000000000000000000000000000000"

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data['UNISWAP'][chain_from]), abi=warmup_data['UNISWAP']['ABI'])

        func_ = getattr(contract.functions, 'execute')
        args = command, [wrap_data, sub_data], deadline
        tx = make_tx(self.w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно сделал SWAP {quote['quote']['amountDecimals']} ETH на {quote['quote']['quoteDecimals']} {quote['quote']['route'][0][0]['tokenOut']['symbol']}", account.address)
        return self.w3.to_hex(hash)

class Sushiswap():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'SUSHISWAP'
        self.headers = {
            'authority': 'tokens.sushi.com',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'if-none-match': 'W/"756ee-w1dk83JILWDmBka0UFzgRhFEbww"',
            'origin': 'https://www.sushi.com',
            'referer': 'https://www.sushi.com/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }

    def get_tokens(self, chain):
        url = 'https://tokens.sushi.com/v0'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                tokens = []
                for token in result:
                    if int(token['chainId']) == chain:
                        tokens.append(token)
                return tokens
            except:
                time.sleep(i * 1)
        return []

    def get_quote(self, token, amount, chain, account):
        url = f'https://swap.sushi.com/{"v3.1" if chain != 10 else ""}?chainId={str(chain)}&tokenIn=0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE&tokenOut={token}&fromTokenId=ETH&toTokenId={token}&amount={str(amount)}&maxPriceImpact=0.01&to={account.address}&preferSushi=true'
        for i in range(2):
            try:
                result = self.helper.fetch_url(url=url, type='get', headers=self.headers, retries=5, timeout=5)
                return json.loads(result)
            except:
                time.sleep(i * 1)
        return None

    def main(self, chain_from, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)
        chain_code = chains_data[chain_from]['id']
        tokens = self.get_tokens(chain_code)

        token = random.choice(tokens)

        quote = self.get_quote(token['address'], value, chain_code, account)
        if not quote.get('route', {}).get('status') == 'Success':
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)
        route = quote['route']
        if float(route['priceImpact']) > 0.5:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data['SUSHI'][chain_from]), abi=warmup_data['SUSHI']['ABI'])
        func_ = getattr(contract.functions, 'processRoute')
        args = quote['args']['tokenIn'], int(route['amountIn']), quote['args']['tokenOut'], int(route['amountOut']), account.address, quote['args']['routeCode']
        tx = make_tx(self.w3, account, value=int(route['amountIn']), func=func_, args=args)

        if tx == "low_native" or not tx or tx == 'error':
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно сделал SWAP {_value} ETH на {int(route['amountOut']) / (10 ** int(route['toToken']['decimals']))} {route['toToken']['symbol']}", account.address)
        return self.w3.to_hex(hash)

class Mirror():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'MIRROR'
        self.headers = {
            'authority': 'mirror.xyz',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://mirror.xyz',
            'referer': 'https://mirror.xyz/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }

    def get_collections(self, chain=10):

        for i in range(5):
            try:
                payload = {
                    'operationName': 'projectCollection',
                    'variables': {
                        'projectAddress': '0xe60aC07Be8bD7f7f33d446e1399c329928Ba8114',
                        'limit': 1000,
                        'cursorStart': int(time.time() * 1000 - 10000),
                    },
                    'query': 'query projectCollection($projectAddress: String!, $limit: Int!, $cursorStart: Float, $cursorEnd: Float, $filterDigests: [String]) {\n  projectCollects(\n    projectAddress: $projectAddress\n    limit: $limit\n    cursorStart: $cursorStart\n    cursorEnd: $cursorEnd\n    filterDigests: $filterDigests\n  ) {\n    cursorStart\n    cursorEnd\n    wnfts {\n      _id\n      address\n      eventTimestamp\n      entry {\n        ...entryDetails\n        publisher {\n          ...publisherDetails\n          __typename\n        }\n        settings {\n          ...entrySettingsDetails\n          __typename\n        }\n        writingNFT {\n          ...writingNFTDetails\n          purchases {\n            ...writingNFTPurchaseDetails\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment entryDetails on entry {\n  _id\n  body\n  hideTitleInEntry\n  publishStatus\n  publishedAtTimestamp\n  digest\n  timestamp\n  title\n  arweaveTransactionRequest {\n    transactionId\n    __typename\n  }\n  featuredImageId\n  featuredImage {\n    mimetype\n    url\n    __typename\n  }\n  publisher {\n    ...publisherDetails\n    __typename\n  }\n  __typename\n}\n\nfragment publisherDetails on PublisherType {\n  project {\n    ...projectDetails\n    __typename\n  }\n  member {\n    ...projectDetails\n    __typename\n  }\n  __typename\n}\n\nfragment projectDetails on ProjectType {\n  _id\n  address\n  avatarURL\n  description\n  displayName\n  domain\n  ens\n  gaTrackingID\n  ga4TrackingID\n  mailingListURL\n  twitterUsername\n  wnftChainId\n  externalUrl\n  headerImage {\n    ...mediaAsset\n    __typename\n  }\n  theme {\n    ...themeDetails\n    __typename\n  }\n  __typename\n}\n\nfragment mediaAsset on MediaAssetType {\n  id\n  cid\n  mimetype\n  sizes {\n    ...mediaAssetSizes\n    __typename\n  }\n  url\n  __typename\n}\n\nfragment mediaAssetSizes on MediaAssetSizesType {\n  og {\n    ...mediaAssetSize\n    __typename\n  }\n  lg {\n    ...mediaAssetSize\n    __typename\n  }\n  md {\n    ...mediaAssetSize\n    __typename\n  }\n  sm {\n    ...mediaAssetSize\n    __typename\n  }\n  __typename\n}\n\nfragment mediaAssetSize on MediaAssetSizeType {\n  src\n  height\n  width\n  __typename\n}\n\nfragment themeDetails on UserProfileThemeType {\n  accent\n  colorMode\n  __typename\n}\n\nfragment entrySettingsDetails on EntrySettingsType {\n  description\n  metaImage {\n    ...mediaAsset\n    __typename\n  }\n  title\n  __typename\n}\n\nfragment writingNFTDetails on WritingNFTType {\n  _id\n  contractURI\n  contentURI\n  deploymentSignature\n  deploymentSignatureType\n  description\n  digest\n  fee\n  fundingRecipient\n  imageURI\n  canMint\n  media {\n    id\n    cid\n    __typename\n  }\n  nonce\n  optimisticNumSold\n  owner\n  price\n  proxyAddress\n  publisher {\n    project {\n      ...writingNFTProjectDetails\n      __typename\n    }\n    __typename\n  }\n  quantity\n  renderer\n  signature\n  symbol\n  timestamp\n  title\n  version\n  network {\n    ...networkDetails\n    __typename\n  }\n  __typename\n}\n\nfragment writingNFTProjectDetails on ProjectType {\n  _id\n  address\n  avatarURL\n  displayName\n  domain\n  ens\n  __typename\n}\n\nfragment networkDetails on NetworkType {\n  _id\n  chainId\n  __typename\n}\n\nfragment writingNFTPurchaseDetails on WritingNFTPurchaseType {\n  numSold\n  __typename\n}',
                }
                result = self.helper.fetch_url(url='https://mirror.xyz/api/graphql', type='post', payload=payload, headers=self.headers)
                eligable_collections = []
                for col in result['data']['projectCollects']['wnfts']:
                    try:
                        if int(col['entry']['writingNFT']['network']['chainId']) == chain:
                            eligable_collections.append(col['entry'])
                    except:
                        pass
                return eligable_collections
            except:
                time.sleep(i*1)
        return []

    def main(self, chain_from, private_key, attempt = 0):

        if attempt > 10:
            return 'error'

        account = self.w3.eth.account.from_key(private_key)

        collections = self.get_collections()
        if not collections:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)
        collection = random.choice(collections)

        contract = collection['writingNFT']['proxyAddress']
        col_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(contract), abi=warmup_data[self.project]['ABI'])
        price = col_contract.functions.price().call()
        if price != 0:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        func_ = getattr(col_contract.functions, 'purchase')

        tx = make_tx(self.w3, account, value=int(0.00069 * 10 ** 18), func=func_, args=(account.address, ""), args_positioning=True)
        if tx == "low_native" or not tx:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt+1)

        self.logger.log_success(f"{self.project} | Успешно заминтил статью {collection['writingNFT']['title']} за 0.00069 ETH",account.address)
        return self.w3.to_hex(hash)

class Blur():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'BLUR'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data['BLUR']['contract']),  abi=warmup_data['BLUR']['ABI'])

    def main(self, chain_from, private_key, attempt = 0):

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        BETH_balance = self.contract.functions.balanceOf(account.address).call()
        action = random.choice(['deposit', 'withdraw']) if BETH_balance != 0 else 'deposit'

        func_ = getattr(self.contract.functions, action)
        args = BETH_balance if action == 'withdraw' else None
        tx = make_tx(self.w3, account, value=value if action == 'deposit' else 0, func=func_, args=args, args_positioning=False)

        if tx == "low_native" or not tx or tx == 'error':
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        self.logger.log_success(f"{self.project} | Успешно сделал {'вывод' if action == 'withdraw' else 'депозит'} {_value if action == 'deposit' else round(BETH_balance / (10 ** 18), 6)} ETH", account.address)
        return self.w3.to_hex(hash)

class Wrapper():
    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'WRAPPER'

    def main(self, chain_from, private_key, attempt = 0):

        contract = self.w3.eth.contract(address=self.w3.to_checksum_address(warmup_data[self.project][chain_from]), abi=warmup_data[self.project]['ABI'])

        account = self.w3.eth.account.from_key(private_key)
        _value = random.uniform(0.00001, 0.000001)
        value = int(_value * 10 ** 18)

        BETH_balance = contract.functions.balanceOf(account.address).call()
        action = random.choice(['deposit', 'withdraw']) if BETH_balance != 0 else 'deposit'

        func_ = getattr(contract.functions, action)
        args = BETH_balance if action == 'withdraw' else None
        tx = make_tx(self.w3, account, value=value if action == 'deposit' else 0, func=func_, args=args, args_positioning=False)

        if tx == "low_native" or not tx or tx == 'error':
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(self.w3, hash)
        if not tx_status:
            return self.main(chain_from=chain_from, private_key=private_key, attempt=attempt + 1)

        self.logger.log_success(f"{self.project} | Успешно сделал WRAP из {_value if action == 'deposit' else round(BETH_balance / (10 ** 18), 6)} {'WETH' if action == 'withdraw' else 'ETH'} в {'WETH' if action != 'withdraw' else 'ETH'} ", account.address)
        return self.w3.to_hex(hash)

class Warmup():

    def __init__(self, w3, logger, helper):
        self.w3 = w3
        self.logger = logger
        self.helper = helper

    def main(self, chain_from, wallet_data):

        if wallet_data.get('proxy', None):
            new_w3 = self.helper.get_web3(wallet_data['proxy'], self.w3[chain_from])
        else:
            new_w3 = self.w3[chain_from]

        mintfun = Mintfun(new_w3, self.logger, self.helper)         #ETH OPT
        lido = Lido(new_w3, self.logger, self.helper)               #ETH
        optimism = Optimismbridge(new_w3, self.logger, self.helper) #ETH OPT
        arbitrum = Arbitrumbridge(new_w3, self.logger, self.helper) #ETH ARB
        polygon = Polygonbridge(new_w3, self.logger, self.helper)   #ETH
        aave = Aave(new_w3, self.logger, self.helper)               #ETH OPT ARB
        approve = Approve(new_w3, self.logger, self.helper)         #ETH OPT ARB
        uniswap = Uniswap(new_w3, self.logger, self.helper)         #ETH OPT ARB
        sushiswap = Sushiswap(new_w3, self.logger, self.helper)     #ETH OPT ARB
        wrapper = Wrapper(new_w3, self.logger, self.helper)         #ETH OPT ARB
        zora = Zora(new_w3, self.logger, self.helper)               #ETH
        starknet = Starknet(new_w3, self.logger, self.helper)       #ETH
        blur = Blur(new_w3, self.logger, self.helper)               #ETH
        mirror = Mirror(new_w3, self.logger, self.helper)           #OPT

        private_key = wallet_data['private_key']

        if chain_from == 'ETH':
            #lambda : starknet.main(chain_from, private_key), OFF
            available_actions = [lambda : wrapper.main(chain_from, private_key), lambda : blur.main(chain_from, private_key),  lambda : zora.main(chain_from, private_key), lambda : sushiswap.main(chain_from, private_key), lambda : approve.main(chain_from, private_key), lambda : uniswap.main(chain_from, private_key), lambda : aave.main(chain_from, private_key), lambda : mintfun.main(chain_from, private_key), lambda : lido.main(chain_from, private_key), lambda : optimism.main(chain_from, private_key), lambda : arbitrum.main(chain_from, private_key), lambda : polygon.main(chain_from, private_key)]
            action = random.choice(available_actions)

            return action()

        if chain_from == 'OPT':
            available_actions = [lambda : wrapper.main(chain_from, private_key), lambda : mirror.main(chain_from, private_key), lambda : sushiswap.main(chain_from, private_key), lambda : approve.main(chain_from, private_key), lambda : uniswap.main(chain_from, private_key), lambda: mintfun.main(chain_from, private_key), lambda : aave.main(chain_from, private_key), lambda : optimism.main(chain_from, private_key)]
            action = random.choice(available_actions)

            return action()

        if chain_from == 'ARB':
            available_actions = [lambda : wrapper.main(chain_from, private_key), lambda : sushiswap.main(chain_from, private_key), lambda : approve.main(chain_from, private_key), lambda : uniswap.main(chain_from, private_key), lambda: arbitrum.main(chain_from, private_key), lambda : aave.main(chain_from, private_key)]
            action = random.choice(available_actions)

            return action()
