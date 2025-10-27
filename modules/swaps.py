from helpers.utils import *
from helpers.data import tokens_data_
import json, eth_abi
from eth_account.messages import encode_structured_data
from web3._utils.contracts import encode_abi


#+
class Woofi():

    def __init__(self, w3, max_slip, helper):
        self.project = 'WOOFI'
        self.headers = {
            'authority': 'fi-api.woo.org',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://fi.woo.org',
            'referer': 'https://fi.woo.org/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.max_slip = max_slip

    def get_quote(self, token_in, token_out, amount):
        params = {
            'from_token': token_in,
            'to_token': token_out,
            'from_amount': str(amount),
            'network': 'base',
        }
        for i in range(3):
            try:
                result = self.help.fetch_url(url='https://fi-api.woo.org/woofi_swap', type='get', params=params, headers=self.headers, retries=5, timeout=5)
                if result.get('status', '') == 'ok':
                    return result['data']
                else:
                    raise Exception
            except Exception:
                time.sleep(i * 1)
        return None

    def get_external_tx(self, token_in, token_out, amount):
        token_in = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_in.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_in
        token_out = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_out.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_out
        params = {
            'fromTokenAddress': token_in,
            'toTokenAddress': token_out,
            'amount': amount,
            'fromAddress': '0x27425e9FB6A9A625E8484CFD9620851D1Fa322E5',
            'slippage': str(int(min(1, self.max_slip))),
            'disableEstimate': 'true',
            'allowPartialFill': 'false',
            'referrer': '0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191',
            'fee': 1
        }
        for i in range(3):
            try:
                result = self.help.fetch_url(url='https://api-kronos-woo.1inch.io/v5.2/8453/swap', type='get', params=params, headers=self.headers, retries=5, timeout=5)
                return result
            except Exception:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        _amount = int(amount * 10 ** token_from_data['decimal'])

        quote = self.get_quote(token_from_data['address'].lower(), token_to_data['address'].lower(), _amount)
        if not quote:
            external_tx = self.get_external_tx(token_from_data['address'].lower(), token_to_data['address'].lower(), _amount)
            if not external_tx:
                return 'no_route'
            else:
                amount_min = int(int(external_tx['toAmount']) * 0.995)
                external = True
        else:
            amount_min = int(int(quote['to_amount']) * 0.995)
            external = False

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, _amount, amount_min)
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key,attempt=attempt + 1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, token_from_data['address'], new_w3.to_checksum_address('0x27425e9fb6a9a625e8484cfd9620851d1fa322e5') if external else swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, token_from_data['address'], new_w3.to_checksum_address('0x27425e9fb6a9a625e8484cfd9620851d1fa322e5') if external else swaps_data[self.project]['contract'])

        token_from_data['address'] = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_from_data['symbol'] == 'ETH' else token_from_data['address']
        token_to_data['address'] = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_to_data['symbol'] == 'ETH' else token_to_data['address']

        if external:
            args = new_w3.to_checksum_address('0x1111111254EEB25477B68fb85Ed929f73A960582'), new_w3.to_checksum_address("0x1111111254EEB25477B68fb85Ed929f73A960582"), new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address( token_to_data['address']), _amount, amount_min, account.address, external_tx['tx']['data']
            func_ = getattr(self.contract.functions, 'externalSwap')
        else:
            args = new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address']), _amount, amount_min, account.address, account.address
            func_ = getattr(self.contract.functions, 'swap')

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(_amount), func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)


class Equalizer():

    def __init__(self, w3, max_slip, helper):

        self.project = 'EQUALIZER'
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def get_headers(self):
        headers = {
            'authority': 'router.firebird.finance',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'api-h': 'YTQ4ZTdlYjc1MDViNDI0OGI2OTllZmNmNmIzZGRmOTcyM2JjZWExMjAwNDczYTM4MGYwMTUwMzZhNzdmNGE3YQ==',
            'api-key': 'firebird_equalizer_prod',
            'api-timestamp': str(int(time.time())),
            'content-type': 'application/json',
            'origin': 'https://base.equalizer.exchange',
            'referer': 'https://base.equalizer.exchange/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'x-request-id': '927593d7-2b13-4cb8-8816-0945ca9cf6d0',
        }
        return headers

    def get_quote(self, token_from, token_to, amount, account):
        token_from = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_from.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from
        token_to = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_to.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to
        params = {
            'chainId': '8453',
            'from': token_from,
            'to': token_to,
            'amount': str(amount),
            'receiver': account.address,
            'slippage': round(max(1, self.max_slip)/100, 2),
            'source': 'equalizer',
            'ref': '0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191',
        }
        for i in range(5):
            try:
                url = f"https://router.firebird.finance/aggregator/v2/quote"
                result = self.help.fetch_url(url=url, type='get', headers=self.get_headers(), params=params)
                return result
            except:
                time.sleep(i * 1)
        return None

    def get_tx(self, quote, account):
        json_data = quote
        for i in range(5):
            try:
                url = f"https://router.firebird.finance/aggregator/v2/encode"
                result = self.help.fetch_url(url=url, type='post', headers=self.get_headers(), payload=json_data)
                return result
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt > 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        _amount = int(amount * 10 ** token_from_data['decimal'])
        if token_from != 'ETH':
            _amount = int(amount * 10 ** token_from_data['decimal'])
            _amount = min(_amount, get_balance(new_w3, account, token_from_data['address']))
            amount = float(_amount / (10 ** token_from_data['decimal']) * 0.999)

        quote = self.get_quote(token_from_data['address'], token_to_data['address'], _amount, account)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        tx_ = self.get_tx(quote, account)
        if not tx_:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, int(tx_['maxReturn']['totalFrom']), int(tx_['maxReturn']['totalTo']))
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['encodedData']['router'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['encodedData']['router'])

        value = int(tx_['maxReturn']['totalFrom']) if token_from == 'ETH' else 0
        tx = make_tx(new_w3, account, value=value, to=new_w3.to_checksum_address(tx_['encodedData']['router']), data=tx_['encodedData']['data'])

        if tx == "low_native" or not tx:
            return tx
        if tx == 'attempt':
            time.sleep(3)
            if attempt > 5:
                return 'error'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)

#+
class Uniswap():

    def __init__(self, w3, max_slip, helper):

        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'UNISWAP'
        self.available_tokens = tokens_data_
        self.headers = {
            'authority': 'api.uniswap.org',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://app.uniswap.org',
            'referer': 'https://app.uniswap.org/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_quoter = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_quoter']), abi=swaps_data[self.project]['ABI_quoter'])
        #self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                payload = {"query": "\n      query MyQuery { liquidityPools(first: 50, orderBy: totalValueLockedUSD, orderDirection: desc) { id name symbol totalLiquidityUSD totalValueLockedUSD inputTokens(orderBy: id, orderDirection: desc) { symbol name id decimals } tick } }"}
                result = self.helper.fetch_url(url='https://api.thegraph.com/subgraphs/name/steegecs/uniswap-v3-base', type='post', payload=payload)
                return result['data']['liquidityPools']
            except:
                time.sleep(i * 1)
        return []

    def get_route(self, token_from, token_to):

        max_liq, pool_ = 0, None
        for pool in self.pools:
            tokens = {token['id'].lower(): token for token in pool['inputTokens']}
            if token_from in tokens and token_to in tokens:
                liquidity = float(pool['totalValueLockedUSD'])
                if liquidity > max_liq:
                    max_liq = liquidity
                    pool_ = pool
        if pool_:
            return [pool_]

        for pool in self.pools:
            tokens = {token['id'].lower(): token for token in pool['inputTokens']}
            if token_from in tokens:
                token_X = tokens[token_from]['id'].lower()
                for sub_pool in self.pools:
                    sub_tokens = {token['id'].lower(): token for token in sub_pool['inputTokens']}
                    if token_to in sub_tokens and token_X in sub_tokens:
                        return [pool, sub_pool]

        good_pools = []
        for pool in self.pools:
            tokens = {token['id'].lower(): token for token in pool['inputTokens']}
            if token_from in tokens:
                token_X = tokens[token_from]['id'].lower()
                for sub_pool in self.pools:
                    sub_tokens = {token['id'].lower(): token for token in sub_pool['inputTokens']}
                    token_Y = sub_tokens[token_X]['id'].lower() if token_X in sub_tokens else None
                    for sub_pool_ in self.pools:
                        sub_pool_tokens = {token['id'].lower(): token for token in sub_pool_['inputTokens']}
                        if token_to in sub_pool_tokens and token_Y in sub_pool_tokens:
                            good_pools.append([pool, sub_pool, sub_pool_])

        if good_pools:
            preferred_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
            for p in good_pools:
                pool_tokens = {token['id'].lower(): token for token in p[0]['inputTokens']}
                token_x = pool_tokens[token_from]['id'].lower() if token_from in pool_tokens else None
                if token_x and token_x.lower() in preferred_tokens:
                    return p
            return random.choice(good_pools)
        else:
            return []

    def get_quote(self, token_in, token_out, amount, account):

        token_in = 'ETH' if token_in == '0x4200000000000000000000000000000000000006' else token_in
        token_out = 'ETH' if token_out == '0x4200000000000000000000000000000000000006' else token_out
        data = {"tokenInChainId":8453,"tokenIn":token_in,"tokenOutChainId":8453,"tokenOut":token_out,"amount":str(amount),"type":"EXACT_INPUT","configs":[{"protocols":["V2","V3","MIXED"],"routingType":"CLASSIC"}]}
        for i in range(3):
            try:
                result = self.helper.fetch_url(url='https://api.uniswap.org/v2/quote', type='post', payload=data, headers=self.headers, retries=5, timeout=5)
                return result
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, permit=False, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        quote = self.get_quote(token_from_data['address'], token_to_data['address'], int(amount * 10 ** token_from_data['decimal']), account)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, permit=permit, attempt=attempt+1)
        if quote.get('errorCode', None) == 'QUOTE_ERROR':
            return 'no_route'

        inputs = []
        commands = ''
        type_quote = 0
        best_route, best_output = None, 0
        for route_ in quote['quote']['route']:
            if int(route_[-1]['amountOut']) > best_output:
                best_output, best_route = int(route_[-1]['amountOut']), route_

        if not best_route:
            return 'no_route'

        for i, step in enumerate(best_route):
            payer_is_sender = True if i == 0 else False
            token_in_address = step['tokenIn']['address']
            token_out_address = step['tokenOut']['address']
            fee = int(step['fee'])
            path = new_w3.to_bytes(hexstr=f"{token_in_address[2:]}{fee:06x}{token_out_address[2:]}")
            try:
                amount_in = int(step['amountIn'])
                amount_out = int(step['amountOut'])
            except:
                amount_in = int(step['amountIn'])
                amount_out = int(best_route[-1]['amountOut'])
                path_str = f"{token_in_address[2:]}"
                for step in range(len(best_route)):
                    path_str += f"{int(best_route[step]['fee']):06x}{best_route[step]['tokenOut']['address'][2:]}"
                path = new_w3.to_bytes(hexstr=path_str)
                type_quote = 1
            if i == 0 and token_in_address.lower() == '0x4200000000000000000000000000000000000006':
                inputs.append((eth_abi.encode([input["type"] for input in swaps_data[self.project]['FUNC_MAP']['WRAP_ETH']["inputs"]], ['0x0000000000000000000000000000000000000002', amount_in])).hex())
                commands += '0b'
                payer_is_sender = False
            if i == 0 and token_in_address.lower() != '0x4200000000000000000000000000000000000006' and permit:
                message = { "details": { "token": token_in_address, "amount": 2**160-1, "expiration": int(time.time())+24*60*60*30, "nonce": 0 }, "spender": "0x198EF79F1F515F02dFE9e3115eD9fC07183f02fC", "sigDeadline": int(time.time())+60*30}
                structured_message = { 'types': swaps_data[self.project]['STRUCTURE_DATA']['types'], 'primaryType': swaps_data[self.project]['STRUCTURE_DATA']['primaryType'], 'domain': swaps_data[self.project]['STRUCTURE_DATA']['domain'], 'message': message, }
                encoded_message = encode_structured_data(structured_message)
                signed_message = account.sign_message(encoded_message)
                func = new_w3.eth.contract(abi=[swaps_data[self.project]['FUNC_MAP']['PERMIT2_PERMIT']]).functions.PERMIT2_PERMIT(((token_in_address, 2**160-1, message['details']['expiration'], message['details']['nonce']), message['spender'], message['sigDeadline']), new_w3.to_bytes(hexstr=signed_message.signature.hex()))
                data = encode_abi(new_w3, func.abi, (((token_in_address, 2**160-1, message['details']['expiration'], 0), message['spender'], message['sigDeadline']), new_w3.to_bytes(hexstr=signed_message.signature.hex())))
                #inputs.append((eth_abi.encode([input["type"] for input in swaps_data[self.project]['FUNC_MAP']['PERMIT2_PERMIT']["inputs"]], (((token_in_address, 2**160-1, message['details']['expiration'], 0), message['spender'], message['sigDeadline']), signed_message.signature.hex()))).hex())
                inputs.append(data[2:])
                commands += '0a'

            inputs.append((eth_abi.encode([input["type"] for input in swaps_data[self.project]['FUNC_MAP']['V3_SWAP_EXACT_IN']["inputs"]], ['0x0000000000000000000000000000000000000001', amount_in, amount_out, path, payer_is_sender])).hex())

            commands += '00'
            if i == len(inputs) != 0 and token_out_address.lower() == '0x4200000000000000000000000000000000000006' and type_quote != 1:
                inputs.append((eth_abi.encode([input["type"] for input in swaps_data[self.project]['FUNC_MAP']['UNWRAP_WETH']["inputs"]], ['0x0000000000000000000000000000000000000001', amount_out])).hex())
                commands += '0c'
            if type_quote == 1:
                break

        inputs = [f"0x{input_}" for input_ in inputs]
        args = f"0x{commands}", inputs, int(time.time()+300)

        slip = check_slippage(self.helper.get_prices_combined(), token_from, token_to, int(best_route[0]['amountIn']), int(best_route[-1]['amountOut']))
        if slip > self.max_slip:
            print(slip, int(best_route[0]['amountIn']), int(best_route[-1]['amountOut']))
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, permit=permit, attempt=attempt + 1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract_permit'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract_permit'])

        func_ = getattr(self.contract.functions, 'execute')

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(best_route[0]['amountIn']), func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx
        if tx == "uni_rerun":
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, permit=not permit, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, permit=permit, attempt=attempt + 1)
        return new_w3.to_hex(hash)

#+
class Sushiswap():

    def __init__(self, w3, max_slip, helper):

        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'SUSHISWAP'
        self.available_tokens = tokens_data_
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
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data['SUSHISWAP']['contract']), abi=swaps_data['SUSHISWAP']['ABI'])

    def get_quote(self, token_in, token_out, amount, account):
        from_token_id = 'ETH' if token_in == '0x4200000000000000000000000000000000000006' else token_in
        token_in = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_in == '0x4200000000000000000000000000000000000006' else token_in
        token_out = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_out == '0x4200000000000000000000000000000000000006' else token_out
        url = f'https://swap.sushi.com/{"v3.2"}?chainId={str(8453)}&tokenIn={token_in}&tokenOut={token_out}&fromTokenId={from_token_id}&toTokenId={token_out}&amount={str(amount)}&maxPriceImpact={int(self.max_slip)/100}&gasPrice=109471544&to={account.address}&preferSushi=true'
        for i in range(3):
            try:
                result = self.helper.fetch_url(url=url, type='get', headers=self.headers, retries=5, timeout=5)
                return json.loads(result)
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, factor=1, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        quote = self.get_quote(token_from_data['address'], token_to_data['address'], int(amount * 10 ** token_from_data['decimal']), account)
        if not quote.get('route', {}).get('status') == 'Success':
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, factor=factor, attempt=attempt+1)
        route = quote['route']
        if float(route['priceImpact']) > self.max_slip/100:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, factor=factor, attempt=attempt+2)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data['SUSHISWAP']['contract'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data['SUSHISWAP']['contract'])

        func_ = getattr(self.contract.functions, 'processRoute')
        args = quote['args']['tokenIn'], int(route['amountIn']), quote['args']['tokenOut'], int(route['amountOut']*factor), account.address, quote['args']['routeCode']

        tx = make_tx(new_w3, account, value=int(route['amountIn']) if token_from == 'ETH' else 0, func=func_, args=args)

        if tx == "low_native" or not tx or tx == 'error':
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, factor=factor, attempt=attempt+1)
        if tx == 'factor':
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, factor=factor*0.99, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, factor=factor, attempt=attempt+1)
        return new_w3.to_hex(hash)


class Maverick():

    def __init__(self, w3, max_slip, helper):
        self.project = 'MAVERICK'
        self.headers = {
            'authority': 'api.izumi.finance',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru,en;q=0.9',
            'origin': 'https://zksync.izumi.finance',
            'referer': 'https://zksync.izumi.finance/',
            'sec-ch-ua': '"Chromium";v="112", "YaBrowser";v="23", "Not:A-Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 YaBrowser/23.5.4.674 Yowser/2.5 Safari/537.36',
        }
        self.help = helper
        self.available_tokens = self.get_all_tokens()
        self.pools = self.get_pools()
        self.w3 = w3
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']),abi=swaps_data[self.project]['ABI'])
        self.max_slip = max_slip

    def get_all_tokens(self):
        for i in range(5):
            try:
                result = self.help.fetch_url(
                    url='https://api.mav.xyz/api/tokens/8453',
                    type='get', headers=self.headers)
                tokens = {}
                for r in result['tokens']:
                    if int(r['chainId']) == 8453:
                        tokens[r['symbol'].lower()] = r
                return tokens
            except:
                time.sleep(i * 1)
                return {}

    def get_pools(self):
        for i in range(5):
            try:
                result = self.help.fetch_url(
                    url='https://api.mav.xyz/api/v2/pools/8453', #reserve url https://api.mav.xyz/api/poolsv2/8453
                    type='get')
                return result['pools']
            except:
                time.sleep(i * 1)
        return {}

    def get_prices(self):
        token_symbols = list(self.available_tokens.keys())
        params = {'t': token_symbols}
        for i in range(5):
            try:
                result = self.help.fetch_url(url='https://api.mav.xyz/api/prices/8453', type='get', headers=self.headers, params=params)
                self.prices = {}
                for token, price in result['prices'].items():
                    self.prices[token] = price['usd']
                return self.prices
            except:
                time.sleep(i * 1)
        self.prices = {}
        return {}

    def find_swap_route(self, token_from, token_to):

        filtered_pools = [
            pool for pool in self.pools if
            (
                    (pool['tokenA']['symbol'].lower() == token_from.lower() and pool['tokenB']['symbol'].lower() == token_to.lower()) or
                    (pool['tokenA']['symbol'].lower() == token_to.lower() and pool['tokenB']['symbol'].lower() == token_from.lower())
            )
        ]

        highest_volume_pool = max(filtered_pools, key=lambda pool: float(pool["totalVolume"]["amount"]), default=None)

        return [highest_volume_pool] if highest_volume_pool else []

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        self.prices = self.get_prices()

        route = self.find_swap_route(token_from, token_to)

        if not route or len(route) > 2:
            return 'no_route'

        tokens = [route[0]['tokenA']['address'], route[0]['tokenB']['address']] if route[0]['tokenA']['symbol'] == token_from else [route[0]['tokenB']['address'], route[0]['tokenA']['address']]
        [tokens.append(route[i]['tokenB']['address']) if route[i]['tokenA']['address'] in tokens else tokens.append(
            route[i]['tokenA']['address']) for i in range(1, len(route))]

        # tokens = [route[1]['tokenX_address'], route[1]['tokenY_address'], route[-1]['tokenX_address']]
        if token_from == 'ETH' and len(tokens) == 3:
            tokens[0], tokens[1] = tokens[1], tokens[0]

        fees = [int(r['fee']*10**6) for r in route]

        path = f"{tokens[0]}{route[0]['id'][2:]}{tokens[1][2:]}" #if token_from != 'ETH' else f"{tokens[1]}{route[0]['id'][2:]}{tokens[0][2:]}"

        token_to_amount = amount * self.prices[self.available_tokens[token_from.lower()]['priceId']] / self.prices[self.available_tokens[token_to.lower()]['priceId']]
        amount_decimals = int(amount * (10 ** self.available_tokens[token_from.lower()]['decimals']))
        min_amount = int((token_to_amount * ((100-(self.max_slip))/100)) * 10 ** self.available_tokens[token_to.lower()]['decimals'])

        args = path, account.address, int(time.time() + 600), int(amount_decimals), int(min_amount)

        if token_from == 'ETH' or token_to == 'ETH':
            if token_from == "ETH":
                add_data = [self.contract.encodeABI(fn_name='refundETH', args=[])]
                func = 'multicall'
            else:
                args = path, '0x0000000000000000000000000000000000000000', int(time.time() + 600), int(amount_decimals), int(min_amount)
                add_data = [self.contract.encodeABI(fn_name='unwrapWETH9', args=[0, account.address])]
                func = 'multicall'
        else:
            add_data, func = '', 'multicall'

        swap_data = [self.contract.encodeABI(fn_name='exactInput', args=[args])]
        if add_data:
            swap_data += add_data

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, amount_decimals, min_amount)
        if (slip * 0.5) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from != "ETH":
            approve = check_approve(new_w3, account, self.available_tokens[token_from.lower()]['address'], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from.lower()]['address'], swaps_data[self.project]['contract'])

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(amount_decimals), func=func_, args=swap_data, args_positioning=False)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)


class Aerodrome():

    def __init__(self, w3, max_slip, helper):
        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'AERODROME'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_data']), abi=swaps_data[self.project]['ABI_data'])
        self.route = self.w3.to_checksum_address('0x420DD381b31aEf6683db6B902084cB0FFECe40Da')

    def get_route(self, token_from, token_to):

        for pool in self.good_pools:
            if (pool['tokenA'].lower() == token_from and pool['tokenB'].lower() == token_to) or (
                    pool['tokenB'].lower() == token_from and pool['tokenA'].lower() == token_to):
                return [pool]
        for pool in self.good_pools:
            if pool['tokenA'].lower() == token_from or pool['tokenB'].lower() == token_from:
                token_X = pool['tokenA'].lower() if pool['tokenA'].lower() != token_from else pool['tokenB'].lower()
                for sub_pool in self.good_pools:
                    if (sub_pool['tokenA'].lower() == token_X and sub_pool['tokenB'].lower() == token_to) or (sub_pool['tokenB'].lower() == token_X and sub_pool['tokenA'].lower() == token_to):
                        return [pool, sub_pool]

        good_pools = []
        for pool in self.good_pools:
            if pool['tokenA'].lower() == token_from or pool['tokenB'].lower() == token_from:
                token_X = pool['tokenA'].lower() if pool['tokenA'].lower() != token_from else pool['tokenB'].lower()
                for sub_pool in self.good_pools:
                    token_Y = sub_pool['tokenA'].lower() if sub_pool['tokenA'].lower() != token_X else sub_pool['tokenB'].lower()
                    for sub_pool_ in self.good_pools:
                        if (sub_pool_['tokenA'].lower() == token_Y and sub_pool_['tokenB'].lower() == token_to) or (sub_pool_['tokenB'].lower() == token_Y and sub_pool_['tokenA'].lower() == token_to):
                            good_pools.append([pool, sub_pool, sub_pool_])
        if good_pools:
            prefered_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
            for p in good_pools:
                token_x = p[0]['tokenA'] if p[0]['tokenA'].lower() != token_from else p[0]['tokenB']
                if token_x.lower() in prefered_tokens:
                    return p
        else:
            return []

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        self.pools = self.contract_data.functions.all(20000, 0, account.address).call()
        self.good_pools = []
        for r in self.pools:  # balance = r[-6]
            if r[6] > 10 ** 8 and r[9] > 10 ** 8:
                self.good_pools.append(
                    {"pool": r[0], 'symbol': r[1], "decimal": r[2], "stable": r[3], "tokenA": r[5], "reserveA": r[6],
                     "tokenB": r[8], "reserveB": r[9], "balance": r[-6]})

        route = self.get_route(token_from_data['address'].lower(), token_to_data['address'].lower())
        if not route:
            return 'no_route'

        if len(route) == 1:
            path = [[new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address']), route[0]['stable'], self.route]]
        elif len(route) == 2:
            token_x = route[0]['tokenA'].lower() if token_from_data['address'].lower() != route[0]['tokenA'].lower() else route[0]['tokenB'].lower()
            path = [(new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), route[0]['stable'], self.route), (new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_to_data['address']), route[1]['stable'], self.route)]
        elif len(route) == 3:
            token_x = route[0]['tokenA'].lower() if token_from_data['address'].lower() != route[0]['tokenA'].lower() else route[0]['tokenB'].lower()
            token_y = route[1]['tokenA'].lower() if token_x != route[1]['tokenA'].lower() else route[1]['tokenB'].lower()
            path = [(new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), route[0]['stable'], self.route), (new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_y), route[1]['stable'], self.route), (new_w3.to_checksum_address(token_y), new_w3.to_checksum_address(token_to_data['address']), route[2]['stable'], self.route)]
        else:
            return 'no_route'
        _amount = int(amount * 10 ** token_from_data['decimal'])
        min_amount_out_data = self.contract.functions.getAmountsOut(_amount, path).call()
        min_amount_out = min_amount_out_data[len(route)]

        args = _amount, min_amount_out, path, account.address, int(time.time()+60*30)

        slip = check_slippage(self.helper.get_prices_combined(), token_from, token_to, _amount, min_amount_out)
        if (slip*0.5) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from == 'ETH':
            args = min_amount_out, path, account.address, int(time.time() + 60 * 30)
            func = 'swapExactETHForTokens'
        else:
            approve = check_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'])
            if token_to == 'ETH':
                func = 'swapExactTokensForETH'
            else:
                func = 'swapExactTokensForTokens'

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(_amount), func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)


class Baseswap():

    def __init__(self, w3, max_slip, helper):
        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'BASESWAP'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                result = self.helper.fetch_url(url='https://api.dexscreener.com/latest/dex/pairs/base/0x07cfa5df24fb17486af0cbf6c910f24253a674d3,0x74cb6260be6f31965c239df6d6ef2ac2b5d4f020,0xbf61c798641a9afe9a8fae60d6a0054fb767f4f5,0x0be2ef4a1cc597ddd2a354505e08d7934802029d,0x9e574f9ad6ca1833f60d5bb21655dd45278a6e3a,0x317d373e590795e2c09d73fad7498fc98c0a692b,0xab067c01c7f5734da168c699ae9d23a4512c9fdb,0x6eda0a4e05ff50594e53dbf179793cadd03689e5,0xa2b120cab75aefdfafda6a14713349a3096eed79,0x7fb35b3967798ce8322cc50ef52553bc5ee4c306,0xd7530ce11d2592824bce690a8abf88b7351a3e35,0x696b4d181eb58cd4b54a59d2ce834184cf7ac31a,0x7fea0384f38ef6ae79bb12295a9e10c464204f52,0xc52328d5af54a12da68459ffc6d0845e91a8395f,0x41d160033c222e6f3722ec97379867324567d883,0xe80b4f755417fb4baf4dbd23c029db3f62786523,0x6d3c5a4a7ac4b1428368310e4ec3bb1350d01455,0x9a0b05f3cf748a114a4f8351802b3bffe07100d4',type='get')
                return result['pairs']
            except:
                time.sleep(i * 1)
        return []

    def get_route(self, token_from, token_to):

        max_liq, pool_ = 0, None
        for pool in self.pools:
            if (pool['baseToken']['address'].lower() == token_from and pool['quoteToken']['address'].lower() == token_to) or (pool['quoteToken']['address'].lower() == token_from and pool['baseToken']['address'].lower() == token_to):
                if float(pool['liquidity']['usd']) > max_liq:
                    max_liq = float(pool['liquidity']['usd'])
                    pool_ = pool
        if pool_:
            return [pool_]
        for pool in self.pools:
            if pool['baseToken']['address'].lower() == token_from or pool['quoteToken']['address'].lower() == token_from:
                token_X = pool['baseToken']['address'].lower() if pool['baseToken']['address'].lower() != token_from else pool['quoteToken']['address'].lower()
                for sub_pool in self.pools:
                    if (sub_pool['baseToken']['address'].lower() == token_X and sub_pool['quoteToken']['address'].lower() == token_to) or (sub_pool['quoteToken']['address'].lower() == token_X and sub_pool['baseToken']['address'].lower() == token_to):
                        return [pool, sub_pool]

        good_pools = []
        for pool in self.pools:
            if pool['baseToken']['address'].lower() == token_from or pool['quoteToken']['address'].lower() == token_from:
                token_X = pool['baseToken']['address'].lower() if pool['baseToken']['address'].lower() != token_from else pool['quoteToken']['address'].lower()
                for sub_pool in self.pools:
                    token_Y = sub_pool['baseToken']['address'].lower() if sub_pool['baseToken']['address'].lower() != token_X else sub_pool['quoteToken']['address'].lower()
                    for sub_pool_ in self.pools:
                        if (sub_pool_['baseToken']['address'].lower() == token_Y and sub_pool_['quoteToken']['address'].lower() == token_to) or (sub_pool_['quoteToken']['address'].lower() == token_Y and sub_pool_['baseToken']['address'].lower() == token_to):
                            good_pools.append([pool, sub_pool, sub_pool_])
        if good_pools:
            prefered_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
            for p in good_pools:
                token_x = p[0]['baseToken']['address'] if p[0]['baseToken']['address'].lower() != token_from else p[0]['quoteToken']['address']
                if token_x.lower() in prefered_tokens:
                    return p
        else:
            return []

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        route = self.get_route(token_from_data['address'].lower(), token_to_data['address'].lower())
        if not route:
            return 'no_route'

        if len(route) == 1:
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 2:
            token_x = route[0]['baseToken']['address'].lower() if token_from_data['address'].lower() != route[0]['baseToken']['address'].lower() else route[0]['quoteToken']['address'].lower()
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 3:
            token_x = route[0]['baseToken']['address'].lower() if token_from_data['address'].lower() != route[0]['baseToken']['address'].lower() else route[0]['quoteToken']['address'].lower()
            token_y = route[1]['baseToken']['address'].lower() if token_x != route[1]['baseToken']['address'].lower() else route[1]['quoteToken']['address'].lower()
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_y), new_w3.to_checksum_address(token_to_data['address'])]
        else:
            return 'no_route'
        _amount = int(amount * 10 ** token_from_data['decimal'])

        min_amount_out_data = self.contract.functions.getAmountsOut(_amount, path).call()
        min_amount_out = min_amount_out_data[len(route)]

        slip = check_slippage(self.helper.get_prices_combined(), token_from, token_to, _amount, min_amount_out)
        if (slip) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        min_amount_out = int(min_amount_out * 0.995)

        args = _amount, min_amount_out, path, account.address, int(time.time() + 60 * 30)

        if token_from == 'ETH':
            args = min_amount_out, path, account.address, int(time.time() + 60 * 30)
            func = 'swapExactETHForTokens'
        else:
            approve = check_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'])
            if token_to == 'ETH':
                func = 'swapExactTokensForETH'
            else:
                func = 'swapExactTokensForTokens'

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(_amount), func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)


class Alienbase():

    def __init__(self, w3, max_slip, helper):
        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'ALIENBASE'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                payload = {"query":"\n      query topPools($blacklist: [String!], $timestamp24hAgo: Int) { pairDayDatas( first: 30 where: {dailyTxns_gt: 1, token0_not_in: $blacklist, token1_not_in: $blacklist, date_gt: $timestamp24hAgo} orderBy: dailyVolumeUSD orderDirection: desc ) { id reserve1 reserve0 pairAddress dailyVolumeUSD token0 { decimals id name symbol } token1 { decimals id name symbol } } }\n    ","variables":{"blacklist":["0x495c7f3a713870f68f8b418b355c085dfdc412c3","0xc3761eb917cd790b30dad99f6cc5b4ff93c4f9ea","0xe31debd7abff90b06bca21010dd860d8701fd901","0xfc989fbb6b3024de5ca0144dc23c18a063942ac1","0xe40fc6ff5f2895b44268fd2e1a421e07f567e007","0xfd158609228b43aa380140b46fff3cdf9ad315de","0xc00af6212fcf0e6fd3143e692ccd4191dc308bea","0x205969b3ad459f7eba0dee07231a6357183d3fb6","0x0bd67d358636fd7b0597724aa4f20beedbf3073a","0xedf5d2a561e8a3cb5a846fbce24d2ccd88f50075","0x702b0789a3d4dade1688a0c8b7d944e5ba80fc30","0x041929a760d7049edaef0db246fa76ec975e90cc","0xba098df8c6409669f5e6ec971ac02cd5982ac108","0x1bbed115afe9e8d6e9255f18ef10d43ce6608d94","0xe99512305bf42745fae78003428dcaf662afb35d","0xbE609EAcbFca10F6E5504D39E3B113F808389056","0x847daf9dfdc22d5c61c4a857ec8733ef5950e82e","0xdbf8913dfe14536c0dae5dd06805afb2731f7e7b","0xF1D50dB2C40b63D2c598e2A808d1871a40b1E653","0x4269e4090ff9dfc99d8846eb0d42e67f01c3ac8b"],"timestamp24hAgo":int(time.time()-(60*60*24))},"operationName":"topPools"}
                result = self.helper.fetch_url(url='https://api.thegraph.com/subgraphs/name/alienbase-xyz/alien-base',type='post', payload=payload)
                return result['data']['pairDayDatas']
            except:
                time.sleep(i * 1)
        return []

    def get_route(self, token_from, token_to):

        max_liq, pool_ = 0, None
        for pool in self.pools:
            if (pool['token0']['id'].lower() == token_from and pool['token1']['id'].lower() == token_to) or (pool['token1']['id'].lower() == token_from and pool['token0']['id'].lower() == token_to):
                if float(pool['dailyVolumeUSD']) > max_liq:
                    max_liq = float(pool['dailyVolumeUSD'])
                    pool_ = pool
        if pool_:
            return [pool_]
        for pool in self.pools:
            if pool['token0']['id'].lower() == token_from or pool['token1']['id'].lower() == token_from:
                token_X = pool['token0']['id'].lower() if pool['token0']['id'].lower() != token_from else pool['token1']['id'].lower()
                for sub_pool in self.pools:
                    if (sub_pool['token0']['id'].lower() == token_X and sub_pool['token1']['id'].lower() == token_to) or (sub_pool['token1']['id'].lower() == token_X and sub_pool['token0']['id'].lower() == token_to):
                        return [pool, sub_pool]

        good_pools = []
        for pool in self.pools:
            if pool['token0']['id'].lower() == token_from or pool['token1']['id'].lower() == token_from:
                token_X = pool['token0']['id'].lower() if pool['token0']['id'].lower() != token_from else pool['token1']['id'].lower()
                for sub_pool in self.pools:
                    token_Y = sub_pool['token0']['id'].lower() if sub_pool['token0']['id'].lower() != token_X else sub_pool['token1']['id'].lower()
                    for sub_pool_ in self.pools:
                        if (sub_pool_['token0']['id'].lower() == token_Y and sub_pool_['token1']['id'].lower() == token_to) or (sub_pool_['token1']['id'].lower() == token_Y and sub_pool_['token0']['id'].lower() == token_to):
                            good_pools.append([pool, sub_pool, sub_pool_])
        if good_pools:
            prefered_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
            for p in good_pools:
                token_x = p[0]['token0']['id'] if p[0]['token0']['id'].lower() != token_from else p[0]['token1']['id']
                if token_x.lower() in prefered_tokens:
                    return p
        else:
            return []

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        route = self.get_route(token_from_data['address'].lower(), token_to_data['address'].lower())
        if not route:
            return 'no_route'

        if len(route) == 1:
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 2:
            token_x = route[0]['token0']['id'].lower() if token_from_data['address'].lower() != route[0]['token0']['id'].lower() else route[0]['token1']['id'].lower()
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 3:
            token_x = route[0]['token0']['id'].lower() if token_from_data['address'].lower() != route[0]['token0']['id'].lower() else route[0]['token1']['id'].lower()
            token_y = route[1]['token0']['id'].lower() if token_x != route[1]['token0']['id'].lower() else route[1]['token1']['id'].lower()
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_y), new_w3.to_checksum_address(token_to_data['address'])]
        else:
            return 'no_route'
        _amount = int(amount * 10 ** token_from_data['decimal'])

        min_amount_out_data = self.contract.functions.getAmountsOut(_amount, path).call()
        min_amount_out = int(min_amount_out_data[len(route)]*0.995)

        args = _amount, min_amount_out, path, account.address, int(time.time()+60*30)

        slip = check_slippage(self.helper.get_prices_combined(), token_from, token_to, _amount, min_amount_out)
        if (slip * 0.5) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from == 'ETH':
            args = min_amount_out, path, account.address, int(time.time() + 60 * 30)
            func = 'swapExactETHForTokens'
        else:
            approve = check_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'])
            if token_to == 'ETH':
                func = 'swapExactTokensForETH'
            else:
                func = 'swapExactTokensForTokens'

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(_amount), func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)


class Swapbased():

    def __init__(self, w3, max_slip, helper):
        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'SWAPBASED'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_quoter = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_quoter']),abi=swaps_data[self.project]['ABI_quoter'])
        self.contract_v2 = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_v2']), abi=swaps_data[self.project]['ABI_v2'])
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                payload = {"query":"\n      query MyQuery { pairs(orderBy: reserveUSD, first: 15, orderDirection: desc) { id token0 { decimals id name symbol } token1 { decimals id name symbol } volumeUSD reserveUSD } }"}
                result = self.helper.fetch_url(url='https://api.thegraph.com/subgraphs/name/alienbase-xyz/alien-base',type='post', payload=payload)
                return result['data']['pairs']
            except:
                time.sleep(i * 1)
        return []

    def get_route(self, token_from, token_to):

        max_liq, pool_ = 0, None
        for pool in self.pools:
            if (pool['token0']['id'].lower() == token_from and pool['token1']['id'].lower() == token_to) or (pool['token1']['id'].lower() == token_from and pool['token0']['id'].lower() == token_to):
                if float(pool['reserveUSD']) > max_liq:
                    max_liq = float(pool['reserveUSD'])
                    pool_ = pool
        if pool_:
            return [pool_]
        for pool in self.pools:
            if pool['token0']['id'].lower() == token_from or pool['token1']['id'].lower() == token_from:
                token_X = pool['token0']['id'].lower() if pool['token0']['id'].lower() != token_from else pool['token1']['id'].lower()
                for sub_pool in self.pools:
                    if (sub_pool['token0']['id'].lower() == token_X and sub_pool['token1']['id'].lower() == token_to) or (sub_pool['token1']['id'].lower() == token_X and sub_pool['token0']['id'].lower() == token_to):
                        return [pool, sub_pool]

        good_pools = []
        for pool in self.pools:
            if pool['token0']['id'].lower() == token_from or pool['token1']['id'].lower() == token_from:
                token_X = pool['token0']['id'].lower() if pool['token0']['id'].lower() != token_from else pool['token1']['id'].lower()
                for sub_pool in self.pools:
                    token_Y = sub_pool['token0']['id'].lower() if sub_pool['token0']['id'].lower() != token_X else sub_pool['token1']['id'].lower()
                    for sub_pool_ in self.pools:
                        if (sub_pool_['token0']['id'].lower() == token_Y and sub_pool_['token1']['id'].lower() == token_to) or (sub_pool_['token1']['id'].lower() == token_Y and sub_pool_['token0']['id'].lower() == token_to):
                            good_pools.append([pool, sub_pool, sub_pool_])
        if good_pools:
            prefered_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
            for p in good_pools:
                token_x = p[0]['token0']['id'] if p[0]['token0']['id'].lower() != token_from else p[0]['token1']['id']
                if token_x.lower() in prefered_tokens:
                    return p
        else:
            return []

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        route = self.get_route(token_from_data['address'].lower(), token_to_data['address'].lower())
        if not route:
            return 'no_route'

        if len(route) == 1:
            path = f"{new_w3.to_checksum_address(token_from_data['address'])}{new_w3.to_checksum_address(token_to_data['address'])[2:]}"
            sub_path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 2:
            token_x = route[0]['token0']['id'].lower() if token_from_data['address'].lower() != route[0]['token0']['id'].lower() else route[0]['token1']['id'].lower()
            path = f"{new_w3.to_checksum_address(token_from_data['address'])}{new_w3.to_checksum_address(token_x)[2:]}{new_w3.to_checksum_address(token_to_data['address'])[2:]}"
            sub_path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 3:
            token_x = route[0]['token0']['id'].lower() if token_from_data['address'].lower() != route[0]['token0']['id'].lower() else route[0]['token1']['id'].lower()
            token_y = route[1]['token0']['id'].lower() if token_x != route[1]['token0']['id'].lower() else route[1]['token1']['id'].lower()
            path = f"{new_w3.to_checksum_address(token_from_data['address'])}{new_w3.to_checksum_address(token_x)[2:]}{new_w3.to_checksum_address(token_y)[2:]}{new_w3.to_checksum_address(token_to_data['address'])[2:]}"
            sub_path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_y), new_w3.to_checksum_address(token_to_data['address'])]

        else:
            return 'no_route'

        _amount = int(amount * 10 ** token_from_data['decimal'])

        try:
            if len(route) == 1:
                bytes_path = bytes.fromhex(path[2:])
                quote = self.contract_quoter.functions.quoteExactInput(bytes_path, _amount).call()
            else:
                quote = self.contract_quoter.functions.quoteExactInputSingle(new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address']), _amount, 0).call()
            min_amount = quote[0]
            #fees = quote[1]
            use_v3 = True
        except:
            use_v3 = False
            min_amount_data = self.contract_v2.functions.getAmountsOut(_amount, sub_path).call()
            min_amount = min_amount_data[len(route)]

        slip = check_slippage(self.helper.get_prices_combined(), token_from, token_to, _amount, min_amount)
        if (slip * 0.5) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        min_amount = int(min_amount * 0.995)

        if use_v3:
            if len(route) == 1:
                func = 'exactInputSingle'
                args = new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address']), account.address, int(time.time()+60*30), _amount, min_amount, 0
            else:
                func = 'exactInput'
                args = path, account.address, int(time.time()+60*30), _amount, min_amount

            func_ = getattr(self.contract.functions, func)
        else:
            args = _amount, min_amount, sub_path, account.address, int(time.time() + 60 * 30)
            if token_from == 'ETH':
                args = min_amount, sub_path, account.address, int(time.time() + 60 * 30)
                func = 'swapExactETHForTokens'
            else:
                if token_to == 'ETH':
                    func = 'swapExactTokensForETH'
                else:
                    func = 'swapExactTokensForTokens'
            func_ = getattr(self.contract_v2.functions, func)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'] if use_v3 else swaps_data[self.project]['contract_v2'])
            if not approve:
                make_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract'] if use_v3 else swaps_data[self.project]['contract_v2'])

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(_amount), func=func_, args=args, args_positioning=False if use_v3 else True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)


class Pancake():

    def __init__(self, w3, max_slip, helper):
        self.project = 'PANCAKE'
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']),abi=swaps_data[self.project]['ABI'])
        self.max_slip = max_slip
        self.pools = self.get_pools()

    def get_pools(self):
        url = 'https://api.studio.thegraph.com/query/45376/exchange-v3-base/version/latest'
        payload = { "query": """query MyQuery { pools( first: 20 orderBy: totalValueLockedUSD orderDirection: desc where: {totalValueLockedUSD_gte: "500"} ) { id token0 { decimals id name symbol } token1 { decimals id name symbol } volumeUSD totalValueLockedUSD sqrtPrice liquidity feeTier feeProtocol token0Price token1Price } }""",}
        for i in range(5):
            try:
                result = self.help.fetch_url(url=url, type='post', payload=payload)
                return result['data']['pools']
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        if token_to == 'ETH':
            token_to = "WETH"
        if token_from == 'ETH':
            token_from = "WETH"

        if not self.pools:
            return 'no_route'

        try:
            token_from_data = tokens_data_[token_from]
            token_to_data = tokens_data_[token_to]
        except:
            return "no_route"

        pool, less_fee = None, 1000000000
        for p in self.pools:
            if p['token1']['symbol'].lower() == token_from_data['symbol'].lower() and p['token0']['symbol'].lower() == token_to_data['symbol'].lower() or p['token0']['symbol'].lower() == token_from_data['symbol'].lower() and p['token1']['symbol'].lower() == token_to_data['symbol'].lower():
                if int(p['feeTier']) < less_fee:
                    pool = p

        self.prices = self.help.get_prices_combined()
        if pool is not None:

            fee = int(pool['feeTier'])
            tokens = new_w3.to_checksum_address(token_to_data['address']), new_w3.to_checksum_address(token_from_data['address'])
            amount_in = int(amount * 10 ** token_from_data['decimal'])
            amount_out_min = int(amount * self.prices[token_from] / self.prices[token_to] * ((100-self.max_slip)/100) * 10 ** token_to_data['decimal'])
            sqrt_price_limit_x96 = 0#math.isqrt(int(pool["sqrtPrice"]) * 10 ** 12)

            recipient = account.address
            add_data = ''
            if token_from == 'WETH' or token_to == 'WETH':
                # if token_from == "WETH":
                #     add_data = [self.contract.encodeABI(fn_name='refundETH', args=[])]
                if token_to == 'WETH':
                    recipient = new_w3.to_checksum_address('0x0000000000000000000000000000000000000002')
                    add_data = self.contract.encodeABI(fn_name='unwrapWETH9', args=[amount_out_min, account.address])
            else:
                add_data = ''

            args = tokens[1], tokens[0], fee, recipient, amount_in, amount_out_min, sqrt_price_limit_x96

            swap_data = [self.contract.encodeABI(fn_name='exactInputSingle', args=[args])]
            if add_data:
                swap_data.append(add_data)

            tx_args = int(time.time())+300, swap_data

        else:
            paths = []
            for p in self.pools:
                fees = []
                if p['token1']['symbol'].lower() == token_from_data['symbol'].lower() or p['token0']['symbol'].lower() == token_from_data['symbol'].lower():
                    fees.append(int(p['feeTier']))
                    intermediate_token = p['token1'] if p['token1']['symbol'].lower() != token_from_data['symbol'].lower() else p['token0']
                    for sub_p in self.pools:
                        if sub_p['token1']['symbol'].lower() == intermediate_token['symbol'].lower() and sub_p['token0']['symbol'].lower() == token_to_data['symbol'].lower() or sub_p['token0']['symbol'].lower() == intermediate_token['symbol'].lower() and sub_p['token1']['symbol'].lower() == token_to_data['symbol'].lower():
                            fees.append(int(sub_p['feeTier']))
                            path = {"intermediate_token": intermediate_token, "fees": fees}
                            paths.append(path)
            if not paths:
                return 'no_route'

            path = random.choice(paths)
            path = f"{token_from_data['address']}{'{:06X}'.format(path['fees'][0])}{path['intermediate_token']['id'][2:]}{'{:06X}'.format(path['fees'][1])}{token_to_data['address'][2:]}"
            amount_in = int(amount * 10 ** token_from_data['decimal'])
            amount_out_min = int(amount * self.prices[token_from] / self.prices[token_to] * ((100 - self.max_slip) / 100) * 10 **token_to_data['decimal'])
            if token_to == 'WETH':
                add_data = self.contract.encodeABI(fn_name='unwrapWETH9', args=[amount_out_min, account.address])
            else:
                add_data = ''
            args = path, account.address, amount_in, amount_out_min

            swap_data = [self.contract.encodeABI(fn_name='exactInput', args=[args])]
            if add_data:
                swap_data.append(add_data)

            tx_args = int(time.time()) + 300, swap_data


        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, amount_in, amount_out_min)
        if (slip * 0.5) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from != "WETH":
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract'])

        func_ = getattr(self.contract.functions, 'multicall')

        tx = make_tx(new_w3, account, value=0 if token_from != 'WETH' else int(amount_in), func=func_, args=tx_args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

#TODO V3 (V2 WORKING ONLY)
class Synthswap():
    def __init__(self, w3, max_slip, helper):
        self.w3 = w3
        self.max_slip = max_slip
        self.helper = helper
        self.project = 'SYNTHSWAP'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_v2']), abi=swaps_data[self.project]['ABI_v2'])
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                # result = self.helper.fetch_url(url='https://api.dexscreener.com/latest/dex/pairs/base/0x2c1e1a69ee809d3062ace40fb83a9bfb59623d95,0xac5af1706cc42a7c398c274c3b8ecf735e7ecb28,0x277301a4c042b5d1bdf61ab11027c2c42286afd1,0xe0712c087ecb8a0dd20914626152ebf4890708c2,0x3458ffdc3b2cc274a9d8aa8d9b0b934558b7a498,0xc33c91a7b3e62ef8f7c7870daec7af0f524abd6a',type='get')
                # return result['pairs']
                payload = {"query": "\n      query MyQuery { pairs(first: 30, orderBy: txCount, orderDirection: desc) { id reserve0 reserve1 reserveUSD token0 { decimals id name symbol } token1 { decimals id name symbol } } }"}
                result = self.helper.fetch_url(url='https://api.studio.thegraph.com/query/45189/synthswap-dex-v2/version/latest', type='post', payload=payload)
                return result['data']['pairs']
            except:
                time.sleep(i * 1)
        return []

    # def get_route(self, token_from, token_to):
    #
    #     max_liq, pool_ = 0, None
    #     for pool in self.pools:
    #         if (pool['baseToken']['address'].lower() == token_from and pool['quoteToken']['address'].lower() == token_to) or (pool['quoteToken']['address'].lower() == token_from and pool['baseToken']['address'].lower() == token_to):
    #             if float(pool['liquidity']['usd']) > max_liq:
    #                 max_liq = float(pool['liquidity']['usd'])
    #                 pool_ = pool
    #     if pool_:
    #         return [pool_]
    #     for pool in self.pools:
    #         if pool['baseToken']['address'].lower() == token_from or pool['quoteToken']['address'].lower() == token_from:
    #             token_X = pool['baseToken']['address'].lower() if pool['baseToken']['address'].lower() != token_from else pool['quoteToken']['address'].lower()
    #             for sub_pool in self.pools:
    #                 if (sub_pool['baseToken']['address'].lower() == token_X and sub_pool['quoteToken']['address'].lower() == token_to) or (sub_pool['quoteToken']['address'].lower() == token_X and sub_pool['baseToken']['address'].lower() == token_to):
    #                     return [pool, sub_pool]
    #
    #     good_pools = []
    #     for pool in self.pools:
    #         if pool['baseToken']['address'].lower() == token_from or pool['quoteToken']['address'].lower() == token_from:
    #             token_X = pool['baseToken']['address'].lower() if pool['baseToken']['address'].lower() != token_from else pool['quoteToken']['address'].lower()
    #             for sub_pool in self.pools:
    #                 token_Y = sub_pool['baseToken']['address'].lower() if sub_pool['baseToken']['address'].lower() != token_X else sub_pool['quoteToken']['address'].lower()
    #                 for sub_pool_ in self.pools:
    #                     if (sub_pool_['baseToken']['address'].lower() == token_Y and sub_pool_['quoteToken']['address'].lower() == token_to) or (sub_pool_['quoteToken']['address'].lower() == token_Y and sub_pool_['baseToken']['address'].lower() == token_to):
    #                         good_pools.append([pool, sub_pool, sub_pool_])
    #     if good_pools:
    #         prefered_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
    #         for p in good_pools:
    #             token_x = p[0]['baseToken']['address'] if p[0]['baseToken']['address'].lower() != token_from else p[0]['quoteToken']['address']
    #             if token_x.lower() in prefered_tokens:
    #                 return p
    #     else:
    #         return []
    def get_route(self, token_from, token_to):

        max_liq, pool_ = 1, None
        for pool in self.pools:
            if (pool['token0']['id'].lower() == token_from and pool['token1']['id'].lower() == token_to) or (pool['token1']['id'].lower() == token_from and pool['token0']['id'].lower() == token_to):
                if float(pool['reserveUSD']) > max_liq:
                    max_liq = float(pool['reserveUSD'])
                    pool_ = pool
        if pool_:
            return [pool_]
        for pool in self.pools:
            if pool['token0']['id'].lower() == token_from or pool['token1']['id'].lower() == token_from:
                token_X = pool['token0']['id'].lower() if pool['token0']['id'].lower() != token_from else pool['token1']['id'].lower()
                for sub_pool in self.pools:
                    if (sub_pool['token0']['id'].lower() == token_X and sub_pool['token1']['id'].lower() == token_to) or (sub_pool['token1']['id'].lower() == token_X and sub_pool['token0']['id'].lower() == token_to):
                        return [pool, sub_pool]

        good_pools = []
        for pool in self.pools:
            if pool['token0']['id'].lower() == token_from or pool['token1']['id'].lower() == token_from:
                token_X = pool['token0']['id'].lower() if pool['token0']['id'].lower() != token_from else pool['token1']['id'].lower()
                for sub_pool in self.pools:
                    token_Y = sub_pool['token0']['id'].lower() if sub_pool['token0']['id'].lower() != token_X else sub_pool['token1']['id'].lower()
                    for sub_pool_ in self.pools:
                        if (sub_pool_['token0']['id'].lower() == token_Y and sub_pool_['token1']['id'].lower() == token_to) or (sub_pool_['token1']['id'].lower() == token_Y and sub_pool_['token0']['id'].lower() == token_to):
                            good_pools.append([pool, sub_pool, sub_pool_])
        if good_pools:
            prefered_tokens = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'.lower(), '0x4200000000000000000000000000000000000006'.lower()]
            for p in good_pools:
                token_x = p[0]['token0']['id'] if p[0]['token0']['id'].lower() != token_from else p[0]['token1']['id']
                if token_x.lower() in prefered_tokens:
                    return p
        else:
            return []

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        route = self.get_route(token_from_data['address'].lower(), token_to_data['address'].lower())
        if not route:
            return 'no_route'

        if len(route) == 1:
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 2:
            token_x = route[0]['token0']['id'].lower() if token_from_data['address'].lower() != route[0]['token0']['id'].lower() else route[0]['token1']['id'].lower()
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_to_data['address'])]
        elif len(route) == 3:
            token_x = route[0]['token0']['id'].lower() if token_from_data['address'].lower() != route[0]['token0']['id'].lower() else route[0]['token1']['id'].lower()
            token_y = route[1]['token0']['id'].lower() if token_x != route[1]['token0']['id'].lower() else route[1]['token1']['id'].lower()
            path = [new_w3.to_checksum_address(token_from_data['address']), new_w3.to_checksum_address(token_x), new_w3.to_checksum_address(token_y), new_w3.to_checksum_address(token_to_data['address'])]
        else:
            return 'no_route'
        _amount = int(amount * 10 ** token_from_data['decimal'])

        min_amount_out_data = self.contract.functions.getAmountsOut(_amount, path).call()
        min_amount_out = min_amount_out_data[len(route)]

        args = _amount, min_amount_out, path, account.address, int(time.time()+60*30)

        slip = check_slippage(self.helper.get_prices_combined(), token_from, token_to, _amount, min_amount_out)
        if (slip * 0.5) > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from == 'ETH':
            args = min_amount_out, path, account.address, int(time.time() + 60 * 30)
            func = 'swapExactETHForTokens'
        else:
            approve = check_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract_v2'])
            if not approve:
                make_approve(new_w3, account, token_from_data['address'], swaps_data[self.project]['contract_v2'])
            if token_to == 'ETH':
                func = 'swapExactTokensForETH'
            else:
                func = 'swapExactTokensForTokens'

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0 if token_from != 'ETH' else int(_amount), func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

#+
class Odos():

    def __init__(self, w3, max_slip, helper):
        self.project = 'ODOS'
        self.headers = {
            'authority': 'api.odos.xyz',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://app.odos.xyz',
            'referer': 'https://app.odos.xyz/',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'x-sec-fetch-site': 'same-origin',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def quote(self, amount, token_from, token_to, account):
        for i in range(5):
            payload = {
                        'chainId': 8453,
                        'inputTokens': [
                            {
                                'tokenAddress': "0x0000000000000000000000000000000000000000" if token_from == "ETH" else self.available_tokens[token_from]['address'],
                                'amount': str(int(amount*10**18)) if token_from == "ETH" else str(int(amount*10**int(self.available_tokens[token_from]['decimal']))),
                            },
                        ],
                        'outputTokens': [
                            {
                                'tokenAddress': "0x0000000000000000000000000000000000000000" if token_to == "ETH" else self.available_tokens[token_to]['address'],
                                'proportion': 1,
                            },
                        ],
                        'gasPrice': 0.25,
                        'userAddr': account.address,
                        'slippageLimitPercent': 1,
                        'sourceBlacklist': [],
                        'pathViz': True,
                        'referralCode': 3169696969,
                        'compact': True,
                        'likeAsset': False,
                    }
            try:
                result = self.help.fetch_url(url='https://api.odos.xyz/sor/quote/v2', type='post', payload=payload, headers=self.headers)
                return result
            except:
                time.sleep(i * 1)
        return {}

    def swap_requsets(self, path_id, account):
        for i in range(5):
            try:
                payload = {"userAddr":account.address,"pathId":path_id,"simulate":False}
                result = self.help.fetch_url(url='https://api.odos.xyz/sor/assemble', type='post', payload=payload, headers=self.headers)
                return result
            except:
                time.sleep(i * 1)
        return {}

    def swap(self, amount, token_from, token_to, private_key, attempt=0):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        if attempt != 0:
            time.sleep(1)
        if attempt > 10:
            return "error"

        account = new_w3.eth.account.from_key(private_key['private_key'])

        quote = self.quote(amount, token_from, token_to, account)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        swap_data = self.swap_requsets(quote['pathId'], account)
        if not swap_data or swap_data.get('detail', 'none').lower() == 'Input token not available'.lower():
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        try:
            out_amount = int(swap_data['inputTokens'][0]['amount'])
            in_amount = int(swap_data['outputTokens'][0]['amount'])
        except:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, out_amount, in_amount)
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        if token_from != 'ETH':
            approve = check_approve(self.w3, account, self.available_tokens[token_from]['address'], swap_data['transaction']['to'])
            if not approve:
                make_approve(self.w3, account, self.available_tokens[token_from]['address'], swap_data['transaction']['to'])

        tx = make_tx(new_w3, account, value=int(swap_data['transaction']['value']), to=swap_data['transaction']['to'], data=swap_data['transaction']['data'])

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key)

        return new_w3.to_hex(hash)

#+
class Inch():
    def __init__(self, w3, max_slip, helper):
        self.project = '1INCH'
        self.headers = {
            'authority': 'api.odos.xyz',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://app.odos.xyz',
            'referer': 'https://app.odos.xyz/',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'x-sec-fetch-site': 'same-origin',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def quote(self, amount, token_from, token_to, account):
        for i in range(5):
            try:
                token_from = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_from.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from
                token_to = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_to.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to
                url = f"https://api-symbiosis.1inch.io/v5.0/8453/swap?fromTokenAddress={token_from}&toTokenAddress={token_to}&amount={amount}&fromAddress={account.address}&destReceiver={account.address}&slippage={int(self.max_slip)}&disableEstimate=true&allowPartialFill=false&referrer=0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191&fee=1" #&protocols=ZKSYNC_MUTE%2CZKSYNC_ONE_INCH_LIMIT_ORDER_V3%2CZKSYNC_PMMX%2CZKSYNC_SPACEFI%2CZKSYNC_SYNCSWAP%2CZKSYNC_GEM%2CZKSYNC_MAVERICK_V1%2CZKSYNC_WOOFI_V2&usePatching=false
                # url2 = f'https://api-symbiosis.1inch.io/v5.0/324/quote?fromTokenAddress={token_from}&toTokenAddress={token_to}&amount={amount}&gasPrice=250000000&protocolWhiteList=ZKSYNC_MUTE,ZKSYNC_ONE_INCH_LIMIT_ORDER_V3,ZKSYNC_PMMX,ZKSYNC_SPACEFI,ZKSYNC_SYNCSWAP,ZKSYNC_GEM,ZKSYNC_MAVERICK_V1,ZKSYNC_WOOFI_V2&walletAddress={self.account.address}&preset=maxReturnResult'
                result = self.help.fetch_url(url=url, type='get', headers=self.headers)
                return result
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        if attempt != 0:
            time.sleep(1)
        if attempt > 10:
            return "error"

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'error'

        try:
            _amount = int(amount * 10 ** int(token_from_data['decimals']))
        except:
            _amount = int(amount * 10 ** int(token_from_data['decimal']))

        if token_from != 'ETH':
            _amount = int(amount * 10 ** token_from_data['decimal'])
            _amount = min(_amount, get_balance(new_w3, account, token_from_data['address']))
            amount = float(_amount / (10 ** token_from_data['decimal']) * 0.999)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract'])

        quote = self.quote(str(_amount), token_from_data['address'], token_to_data['address'], account)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        if quote.get('description', 'none').lower() == 'insufficient liquidity':
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        elif quote.get('error', False):
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, int(quote['fromTokenAmount']), int(quote['toTokenAmount']))
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        tx = make_tx(new_w3, account, value=int(quote['tx']['value']), to=new_w3.to_checksum_address(quote['tx']['to']), data=quote['tx']['data'])

        if tx == "low_native" or not tx:
            return tx
        if tx == 'attempt':
            time.sleep(3)
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)

#+
class Dodoex():

    def __init__(self, w3, max_slip, helper):
        self.project = 'DODOEX'
        self.headers = {
            'authority': 'api.dodoex.io',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://swapbox.nabox.io',
            'referer': 'https://swapbox.nabox.io/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def quote(self, amount, token_from_data, token_to_data, account):
        for i in range(5):
            try:
                token_from = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_from_data['address'].lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from_data['address']
                token_to = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_to_data['address'].lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to_data['address']
                url = f"https://api.dodoex.io/route-service/fee-route-widget/getdodoroute?chainId=8453&apikey=8477c6932c9df6c5b8&deadLine={int(time.time())+600}&fromAmount={amount}&fromTokenAddress={token_from}&fromTokenDecimals={token_from_data['decimal']}&toTokenAddress={token_to}&slippage={round(max(1, int(self.max_slip)), 2)}&userAddr={account.address}&rebateTo=0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191&fee=9000000000000000"
                result = self.help.fetch_url(url=url, type='get', headers=self.headers)
                print(result)
                return result['data']
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt != 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        quote = self.quote(str(int(amount * 10 ** token_from_data['decimal'])), token_from_data, token_to_data, account)
        if not quote:
            if attempt > 5:
                return 'no_data'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = float(quote['priceImpact'])
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], quote['targetApproveAddr'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], quote['targetApproveAddr'])

        tx = make_tx(new_w3, account, value=int(quote['value']), to=new_w3.to_checksum_address(quote['to']), data=quote['data'])

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)


class Wowmax():
    def __init__(self, w3, max_slip, helper):
        self.project = 'WOWMAX'
        self.headers = {
            'authority': 'api-gateway.wowmax.exchange',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://app.wowmax.exchange',
            'referer': 'https://app.wowmax.exchange/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def quote(self, amount, token_from_data, token_to_data, account):
        for i in range(5):
            try:
                token_from = '0x0000000000000000000000000000000000000000' if token_from_data['address'].lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from_data['address'].lower()
                token_to = '0x0000000000000000000000000000000000000000' if token_to_data['address'].lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to_data['address'].lower()
                url = f"https://api-gateway.wowmax.exchange/chains/8453/swap?amount={amount}&from={token_from}&to={token_to}&gasPrice={self.w3.eth.gas_price}&slippage={round(max(1, self.max_slip), 2)}"
                result = self.help.fetch_url(url=url, type='get', headers=self.headers)
                return result
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt != 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        quote = self.quote(str(amount), token_from_data, token_to_data, account)
        if not quote:
            if attempt > 5:
                return 'no_data'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        try:
            if quote.get('statusCode', 0) in [500, '500']:
                return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)
        except:
            pass

        slip = float(quote['priceImpact']) * 100
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], quote['contract'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], quote['contract'])

        try:
            value = int(quote['value'])
        except:
            value = 0

        tx = make_tx(new_w3, account, value=value, to=new_w3.to_checksum_address(quote['contract']), data=quote['data'], gas=int(quote['gasUnitsConsumed']))

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)


class Openocean():
    def __init__(self, w3, max_slip, helper):
        self.project = 'OPENOCEAN'
        self.headers = {
            'authority': 'ethapi.openocean.finance',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://app.openocean.finance',
            'referer': 'https://app.openocean.finance/',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'token': '',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def quote(self, amount, token_from, token_to, account):
        for i in range(5):
            try:
                base_url = 'https://ethapi.openocean.finance/v2/8453/swap?'
                token_from['address'] = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_from['address'].lower() == '0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f'.lower() else token_from['address']
                token_to['address'] = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE' if token_to['address'].lower() == '0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f'.lower() else token_to['address']
                payload = f"inTokenSymbol={token_from['symbol']}&inTokenAddress={token_from['address']}&outTokenSymbol={token_to['symbol']}&outTokenAddress={token_to['address']}&amount={amount}&gasPrice=661105768&disabledDexIds=&slippage={self.max_slip}&account={account.address}&referrer=0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191&flags=0&referrerFee=100"
                url = f"{base_url}{payload}"
                result = self.help.fetch_url(url=url, type='get', headers=self.headers)
                return result
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt != 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        quote = self.quote(str(int(amount * 10 ** token_from_data['decimal'])), token_from_data, token_to_data, account)
        if not quote:
            if attempt > 5:
                return 'no_data'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, int(quote['inAmount']),int(quote['outAmount']))
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'],  swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract'])

        tx = make_tx(new_w3, account, value=int(quote['value']), to=new_w3.to_checksum_address(quote['to']), data=quote['data'])

        if tx == "low_native" or not tx:
            return tx
        if tx == 'ocean_rerun':
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 2)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)


class Okx():

    def __init__(self, w3, max_slip, helper):

        self.project = 'OKXSWAP'
        self.headers = {
            'authority': 'www.okx.com',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'x-sec-fetch-site': 'same-origin',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def get_quote(self, token_from, token_to, amount):
        token_from = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_from.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from
        token_to = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_to.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to
        payload = {"amount":str(amount),"chainId":8453,"toChainId":8453,"toTokenAddress":token_to,"fromTokenAddress":token_from,"slippage":self.max_slip,"slippageType":1,"pmm":"1","gasDropType":0}
        for i in range(5):
            try:
                url = f"https://www.okx.com/priapi/v1/dx/trade/multi/v2/quote?t={int(time.time())}"
                result = self.help.fetch_url(url=url, type='post', headers=self.headers, payload=payload)
                if int(result['code']) == 0:
                    return result['data']
            except:
                time.sleep(i * 1)
        return None

    def get_tx(self, quote, account):
        payload = {
            "autoSlippageInfo": {
                "autoSlippage": quote['autoSlippageInfo']['autoSlippage']
            },
            "chainId": 8453,
            "defiPlatformId": quote['defiPlatformInfo']['id'],
            "dexRouterList": quote['dexRouterList'],
            "estimateGasFee": quote['estimateGasFee'],
            "fromAmount": quote['fromTokenAmount'],
            "fromTokenAddress": quote['fromToken']['tokenContractAddress'],
            "fromTokenDecimal": quote['fromToken']['decimals'],
            "gasDropType": 0,
            "gasPrice": '0.25',
            "minimumReceived": quote['minimumReceived'],
            "originDexRouterList": quote['originDexRouterList'],
            'pmm':"1",
            'priorityFee':"0.0001",
            'quoteType':quote['quoteType'],
            'slippage':quote['realSlippage'],
            'toAmount':quote['receiveAmount'],
            'toTokenAddress':quote['toToken']['tokenContractAddress'],
            'toTokenDecimal':quote['toToken']['decimals'],
            'userWalletAddress':account.address,
        }

        for i in range(5):
            try:
                url = f"https://www.okx.com/priapi/v1/dx/trade/multi/v2/saveOrder?t={int(time.time())}"
                result = self.help.fetch_url(url=url, type='post', headers=self.headers, payload=payload)
                if int(result['code']) == 0:
                    return result['data']
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        if token_from != 'ETH':
            _amount = int(amount * 10 ** token_from_data['decimal'])
            _amount = min(_amount, get_balance(new_w3, account, token_from_data['address']))
            amount = float(_amount / (10 ** token_from_data['decimal']) * 0.999)

        quote = self.get_quote(token_from_data['address'], token_to_data['address'], amount)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        tx_ = self.get_tx(quote, account)
        if not tx_:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, float(quote['fromTokenAmount'])*10**token_from_data['decimal'], float(quote['receiveAmount'])*10**token_to_data['decimal'])
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract_approve'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], swaps_data[self.project]['contract_approve'])

        value = tx_['callData'].get('value', 0)
        tx = make_tx(new_w3, account, value=int(value), to=new_w3.to_checksum_address(tx_['callData']['to']), data=tx_['callData']['data'])

        if tx == "low_native" or not tx:
            return tx
        if tx == 'attempt':
            time.sleep(3)
            if attempt > 5:
                return 'error'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)


class Kyberswap():

    def __init__(self, w3, max_slip, helper):

        self.project = 'KYBERSWAP'
        self.headers = {
            'authority': 'meta-aggregator-api.kyberswap.com',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'x-sec-fetch-site': 'same-origin',
        }
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def get_quote(self, token_from, token_to, amount):
        token_from = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_from.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from
        token_to = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_to.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to
        params = {"amountIn":str(amount),"saveGas":False,"gasInclude":True,"tokenIn":token_from,"tokenOut":token_to, "feeReceiver": '0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191', "feeAmount": 100, "chargeFeeBy": 'currency_in', 'isInBps': True}
        for i in range(5):
            try:
                url = f"https://meta-aggregator-api.kyberswap.com/base/api/v1/routes"
                result = self.help.fetch_url(url=url, type='get', headers=self.headers, params=params)
                if int(result['code']) == 0:
                    return result['data']
            except:
                time.sleep(i * 1)
        return None

    def get_tx(self, quote, account):
        payload = {
            "deadline": int(time.time()) + 60 * 20,
            "recipient": account.address,
            "routeSummary": quote['routeSummary'],
            "sender": account.address,
            "skipSimulateTx": False,
            "slippageTolerance": int(self.max_slip * 100),
            "source": 'kyberswap'
        }

        for i in range(5):
            try:
                url = f"https://meta-aggregator-api.kyberswap.com/base/api/v1/route/build"
                result = self.help.fetch_url(url=url, type='post', headers=self.headers, payload=payload)
                if int(result['code']) == 0:
                    return result['data']
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt > 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        _amount = int(amount * 10 ** token_from_data['decimal'])
        if token_from != 'ETH':
            _amount = int(amount * 10 ** token_from_data['decimal'])
            _amount = min(_amount, get_balance(new_w3, account, token_from_data['address']))
            amount = float(_amount / (10 ** token_from_data['decimal']) * 0.999)

        quote = self.get_quote(token_from_data['address'], token_to_data['address'], _amount)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        tx_ = self.get_tx(quote, account)
        if not tx_:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)


        slip = (1-float(tx_['amountInUsd'])/float(tx_['amountOutUsd']))*100
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['routerAddress'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['routerAddress'])

        value = int(tx_['amountIn']) if token_from == 'ETH' else 0
        tx = make_tx(new_w3, account, value=value, to=new_w3.to_checksum_address(tx_['routerAddress']), data=tx_['data'])

        if tx == "low_native" or not tx:
            return tx
        if tx == 'attempt':
            time.sleep(3)
            if attempt > 5:
                return 'error'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)


class Firebird():

    def __init__(self, w3, max_slip, helper):

        self.project = 'FIREBIRD'
        self.help = helper
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def get_headers(self):
        headers = {
            'authority': 'router.firebird.finance',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'api-h': 'YTQ4ZTdlYjc1MDViNDI0OGI2OTllZmNmNmIzZGRmOTcyM2JjZWExMjAwNDczYTM4MGYwMTUwMzZhNzdmNGE3YQ==',
            'api-key': 'firebird_equalizer_prod',
            'api-timestamp': str(int(time.time())),
            'content-type': 'application/json',
            'origin': 'https://base.equalizer.exchange',
            'referer': 'https://base.equalizer.exchange/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'x-request-id': '927593d7-2b13-4cb8-8816-0945ca9cf6d0',
        }
        return headers

    def get_quote(self, token_from, token_to, amount, account):
        token_from = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_from.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_from
        token_to = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee' if token_to.lower() == '0x4200000000000000000000000000000000000006'.lower() else token_to
        params = {
            'chainId': '8453',
            'from': token_from,
            'to': token_to,
            'amount': str(amount),
            'receiver': account.address,
            'slippage': round(max(1, self.max_slip)/100, 2),
            'source': 'CH.DAO',
            'dexes': 'aerodrome,alienbase,balancer,baldex,baseswap,baseswapv3,basofinance,dackieswap,equalizer,morphexlp,netherfi,rocketswap,sushiswapv3,swapbased,swapbasedperp,swapbasedv3,synthswap,synthswapperp,synthswapv3,thronev2,thronev3,uniswapv3,velocimeter',
            'ref': '0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191',
        }
        for i in range(5):
            try:
                url = f"https://router.firebird.finance/aggregator/v2/quote"
                result = self.help.fetch_url(url=url, type='get', headers=self.get_headers(), params=params)
                return result
            except:
                time.sleep(i * 1)
        return None

    def get_tx(self, quote, account):
        json_data = quote
        for i in range(5):
            try:
                url = f"https://router.firebird.finance/aggregator/v2/encode"
                result = self.help.fetch_url(url=url, type='post', headers=self.get_headers(), payload=json_data)
                return result
            except:
                time.sleep(i * 1)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt > 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        _amount = int(amount * 10 ** token_from_data['decimal'])
        if token_from != 'ETH':
            _amount = int(amount * 10 ** token_from_data['decimal'])
            _amount = min(_amount, get_balance(new_w3, account, token_from_data['address']))
            amount = float(_amount / (10 ** token_from_data['decimal']) * 0.999)

        quote = self.get_quote(token_from_data['address'], token_to_data['address'], _amount, account)
        if not quote:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        tx_ = self.get_tx(quote, account)
        if not tx_:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        slip = check_slippage(self.help.get_prices_combined(), token_from, token_to, int(tx_['maxReturn']['totalFrom']), int(tx_['maxReturn']['totalTo']))
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['encodedData']['router'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['encodedData']['router'])

        value = int(tx_['maxReturn']['totalFrom']) if token_from == 'ETH' else 0
        tx = make_tx(new_w3, account, value=value, to=new_w3.to_checksum_address(tx_['encodedData']['router']), data=tx_['encodedData']['data'])

        if tx == "low_native" or not tx:
            return tx
        if tx == 'fire_rerun':
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 2)
        if tx == 'attempt':
            time.sleep(3)
            if attempt > 5:
                return 'error'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)

#+
class Spaceswap():
    def __init__(self, w3, max_slip, helper):
        self.project = 'SPACESWAP'
        self.help = helper
        self.headers = {
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'x-lifi-integrator': 'jumper.exchange',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'x-lifi-sdk': '2.4.1',
            'Referer': 'https://jumper.exchange/',
            'x-lifi-widget': '2.5.0',
            'sec-ch-ua-platform': '"Windows"',
        }
        self.available_tokens = tokens_data_
        self.w3 = w3
        self.max_slip = max_slip

    def get_routes(self, amount, account, from_token_data, to_token_data):
        from_token = "0x0000000000000000000000000000000000000000" if from_token_data['symbol'] == "ETH" else from_token_data['address']
        to_token = "0x0000000000000000000000000000000000000000" if to_token_data['symbol'] == "ETH" else to_token_data['address']
        payload = {"fromChainId":8453,"fromAmount":str(amount),"fromTokenAddress":from_token,"toChainId":8453,"toTokenAddress":to_token,"fromAddress":account.address,"toAddress":account.address,"options":{"slippage":max(0.005, self.max_slip/100),"maxPriceImpact":max(1, self.max_slip),"allowSwitchChain":True,"bridges":{"deny":[]},"exchanges":{"deny":[]},"order":"RECOMMENDED","insurance":False, 'referrer': '0x5f67ffa4b3f77dd16c9c34a1a82cab8daea03191', 'fee': 0.01, "integrator":"ch.dao"}}
        url = 'https://li.quest/v1/advanced/routes'
        for i in range(7):
            try:
                res = self.help.fetch_url(url=url, type='post', payload=payload, headers=self.headers)
                return res['routes'][0]['steps'][0]
            except:
                time.sleep((1*i)+i)
        return None

    def get_tx(self, payload):
        url = 'https://li.quest/v1/advanced/stepTransaction'
        for i in range(7):
            try:
                res = self.help.fetch_url(url=url, type='post', payload=payload, headers=self.headers)
                return res['transactionRequest']
            except:
                time.sleep((1 * i) + i)
        return None

    def swap(self, amount, token_from, token_to, private_key, attempt = 0):

        if attempt != 0:
            time.sleep(1)
        if attempt > 10:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        try:
            token_from_data = self.available_tokens[token_from]
            token_to_data = self.available_tokens[token_to]
        except:
            return 'no_route'

        amount_ = int(amount * 10 ** token_from_data['decimal'])

        route = self.get_routes(amount_, account, token_from_data, token_to_data)
        if not route:
            if attempt > 5:
                return 'no_data'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key,  attempt=attempt + 1)

        tx_ = self.get_tx(route)
        if not tx_:
            if attempt > 5:
                return 'no_data'
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key,attempt=attempt + 1)

        slip = (1-float(route['estimate']['toAmountUSD'])/float(route['estimate']['fromAmountUSD']))*100
        if slip > self.max_slip:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt + 1)

        if token_from != 'ETH':
            approve = check_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['to'])
            if not approve:
                make_approve(new_w3, account, self.available_tokens[token_from]['address'], tx_['to'])

        tx = make_tx(new_w3, account, value=int(tx_['value'], 16), to=new_w3.to_checksum_address(tx_['to']), data=tx_['data'], minus_fee=False)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.swap(amount=amount, token_from=token_from, token_to=token_to, private_key=private_key, attempt=attempt+1)
        return new_w3.to_hex(hash)


def initialize_swaps(classes_to_init, w3, max_slippage, helper):
    available_swaps = {
        "Aerodrome": Aerodrome,                                      # AERODROME  | aerodrome.finance
        "Baseswap": Baseswap,                                        # BASESWAP   | baseswap.fi
        "Alienbase": Alienbase,                                      # ALIENBASE  | alienswap.xyz
        "Swapbased": Swapbased,                                      # SWAPBASED  | swapbased.finance
        "Synthswap": Synthswap,                                      # SYNTHSWAP  | synthswap.io
        "Odos": Odos,                                                # OSOS       | odos.xyz
        "Maverick": Maverick,                                        # MAVERICK   | app.mav.xyz
        "Inch": Inch,                                                # 1INCH      | app.1inch.io
        "Openocean": Openocean,                                      # OPENOCEAN  | openocean.finance
        "Okx": Okx,                                                  # OKX        | okx.com/web3/dex
        "Pancake": Pancake,                                          # PANCAKE    | pancakeswap.finance
        "Kyberswap": Kyberswap,                                      # KYBERSWAP  | kyberswap.com
        "Sushiswap": Sushiswap,                                      # SUSHISWAP  | sushi.com
        "Dodoex": Dodoex,                                            # DODOEX     | dodoex.io
        "Wowmax": Wowmax,                                            # WOWMAX     | wowmax.exchange
        "Equalizer": Equalizer,                                      # EQUALIZER  | equalizer.exchange
        "Firebird": Firebird,                                        # FIREBIRD   | firebird.finance
        "Spaceswap": Spaceswap,                                      # SPACESWAP  | spaceswap.tech
        "Woofi": Woofi,                                              # WOOFI      | fi.woo.org
        "Uniswap": Uniswap,                                          # UNISWAP    | app.uniswap.org
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, max_slippage, helper)

    return initialized_objects

