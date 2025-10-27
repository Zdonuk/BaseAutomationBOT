from helpers.utils import *
from helpers.data import tokens_data_, CONTRACT_DATA, DATA_ABI

#+ (NOT ETH)
class Aerodrome_liq():

    def __init__(self, w3, helper):
        self.w3 = w3
        self.helper = helper
        self.project = 'AERODROME'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_data']), abi=swaps_data[self.project]['ABI_data'])
        self.route = self.w3.to_checksum_address('0x420DD381b31aEf6683db6B902084cB0FFECe40Da')

    def add_liq(self, amount, token_from, private_key, attempt = 0):

        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])
        if token_from == 'ETH':
            if get_balance(new_w3, account, '0x4200000000000000000000000000000000000006') < _amount:
                wrap = eth_wrapper(amount, 'WETH', new_w3, private_key['private_key'])

        self.good_pools = []
        user_tokens = {}
        user_tokens_ = self.contract_data.functions.tokens(20000, 0, account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3]/(10 ** t[2]))}

        self.pools = self.contract_data.functions.all(20000, 0, account.address).call()
        for r in self.pools:  # balance = r[-6]
            if r[6] > 10 ** 8 and r[9] > 10 ** 8:
                self.good_pools.append({"pool": r[0], 'symbol': r[1], "decimal": r[2], "stable": r[3], "tokenA": r[5], "reserveA": r[6], "tokenB": r[8], "reserveB": r[9], "balance": r[-6]})

        good_pools = []
        for p in self.good_pools:
            token_to = p['tokenA'] if p['tokenA'].lower() != token_from_data['address'].lower() else p['tokenB']
            token_to_data = user_tokens[token_to.lower()]
            # if token_to_data['symbol'] not in [token['symbol'] for token in tokens_data_.values() if token['liq']]:
            #     continue
            if token_to_data['balance'] > 0:
                good_pools.append({'tokenA': new_w3.to_checksum_address(token_from_data['address']), "tokenB": new_w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance'], 'stable': p['stable']})

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            approve = check_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])

        amounts = self.contract.functions.quoteAddLiquidity(choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['stable'], self.route, choosed_pool['amountA'], choosed_pool['amountB']).call()

        args = choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['stable'],  choosed_pool['amountA'],  choosed_pool['amountB'], amounts[0], amounts[1], account.address, int(time.time()+60*60)
        #ONLY WETH
        func_ = getattr(self.contract.functions, 'addLiquidity')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.add_liq(amount=amount, token_from=token_from, private_key=private_key, attempt = attempt+1)
        return new_w3.to_hex(hash)

    def rem_liq(self, private_key):
        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        self.pools = self.contract_data.functions.all(20000, 0, account.address).call()

        good_pools = [p for p in self.pools if p[-6] > 0]
        if len(good_pools) == 0:
            return 'no_route'

        choosed_pool = random.choice(good_pools)

        approve = check_approve(new_w3, account, choosed_pool[0], swaps_data[self.project]['contract'])
        if not approve:
            make_approve(new_w3, account, choosed_pool[0], swaps_data[self.project]['contract'])

        args = [choosed_pool[5], choosed_pool[8], choosed_pool[3], choosed_pool[-6], 0, 0, account.address, int(time.time()+60*60)]
        func_ = getattr(self.contract.functions, 'removeLiquidity')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.rem_liq(private_key=private_key)
        return new_w3.to_hex(hash)

#+
class Baseswap_liq():
    def __init__(self, w3, helper):
        self.w3 = w3
        self.helper = helper
        self.project = 'BASESWAP'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(CONTRACT_DATA), abi=DATA_ABI)
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                result = self.helper.fetch_url(
                    url='https://api.dexscreener.com/latest/dex/pairs/base/0x07cfa5df24fb17486af0cbf6c910f24253a674d3,0x74cb6260be6f31965c239df6d6ef2ac2b5d4f020,0xbf61c798641a9afe9a8fae60d6a0054fb767f4f5,0x0be2ef4a1cc597ddd2a354505e08d7934802029d,0x9e574f9ad6ca1833f60d5bb21655dd45278a6e3a,0x317d373e590795e2c09d73fad7498fc98c0a692b,0xab067c01c7f5734da168c699ae9d23a4512c9fdb,0x6eda0a4e05ff50594e53dbf179793cadd03689e5,0xa2b120cab75aefdfafda6a14713349a3096eed79,0x7fb35b3967798ce8322cc50ef52553bc5ee4c306,0xd7530ce11d2592824bce690a8abf88b7351a3e35,0x696b4d181eb58cd4b54a59d2ce834184cf7ac31a,0x7fea0384f38ef6ae79bb12295a9e10c464204f52,0xc52328d5af54a12da68459ffc6d0845e91a8395f,0x41d160033c222e6f3722ec97379867324567d883,0xe80b4f755417fb4baf4dbd23c029db3f62786523,0x6d3c5a4a7ac4b1428368310e4ec3bb1350d01455,0x9a0b05f3cf748a114a4f8351802b3bffe07100d4',
                    type='get')
                return result['pairs']
            except:
                time.sleep(i * 1)
        return []

    def add_liq(self, amount, token_from, private_key, attempt = 0):

        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])

        user_tokens = {}
        user_tokens_ = self.contract_data.functions.getBalances(account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3] / (10 ** t[2]))}

        good_pools = []
        for p in self.pools:
            token_to = p['baseToken']['address'] if p['baseToken']['address'].lower() != token_from_data['address'].lower() else p['quoteToken']['address']
            if p['baseToken']['address'].lower() == token_from_data['address'].lower() or p['quoteToken']['address'].lower() == token_from_data['address'].lower():
                try:
                    token_to_data = user_tokens[token_to.lower()]
                    # if token_to_data['symbol'] not in [token['symbol'] for token in tokens_data_.values() if token['liq']]:
                    #     continue
                    if token_to_data['balance'] > 0:
                        good_pools.append({'pair': p['pairAddress'],'tokenA': new_w3.to_checksum_address(token_from_data['address']), "tokenB": new_w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance']})
                except:
                    pass

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            if choosed_pool[token].lower() == '0x4200000000000000000000000000000000000006'.lower():
                continue
            approve = check_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])

        pair = new_w3.eth.contract(address=new_w3.to_checksum_address(choosed_pool['pair']), abi=swaps_data[self.project]['ABI_pool'])
        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()
        reserve0 = reserves[0] if token0.lower() == token_from_data['address'].lower() else reserves[1]
        reserve1 = reserves[0] if reserve0 != reserves[0] else reserves[1]

        amountB = self.contract.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
        if amountB < choosed_pool['amountB']:
            amountA = self.contract.functions.quote(amountB, reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            choosed_pool['amountB'] = amountB
        if amountB > choosed_pool['amountB']:
            amountA = self.contract.functions.quote(choosed_pool['amountB'], reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            amountB = self.contract.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
            choosed_pool['amountB'] = amountB

        if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['tokenB'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'addLiquidityETH'
            value = choosed_pool['amountA'] if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['amountB']
            if choosed_pool['tokenB'] != '0x4200000000000000000000000000000000000006':
                args = choosed_pool['tokenB'], choosed_pool['amountB'], int(choosed_pool['amountB'] * 0.90), int(choosed_pool['amountA'] * 0.90), account.address, int(time.time()+60*60)
            else:
                args = choosed_pool['tokenA'], choosed_pool['amountA'], int(choosed_pool['amountA'] * 0.90), int( choosed_pool['amountB'] * 0.90), account.address, int(time.time() + 60 * 60)
        else:
            func = 'addLiquidity'
            value = 0
            args = choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['amountA'], choosed_pool['amountB'], int(choosed_pool['amountA'] * 0.90), int(choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.add_liq(amount=amount, token_from=token_from, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

    def rem_liq(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        good_pools = [p for p in self.pools if get_balance(new_w3, account, p['pairAddress']) > 0]
        if len(good_pools) == 0:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        approve = check_approve(new_w3, account, choosed_pool['pairAddress'], swaps_data[self.project]['contract'])
        if not approve:
            make_approve(new_w3, account, choosed_pool['pairAddress'], swaps_data[self.project]['contract'])

        balance = get_balance(new_w3, account, choosed_pool['pairAddress'])

        if choosed_pool['baseToken']['address'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['quoteToken']['address'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'removeLiquidityETH'
            token = choosed_pool['baseToken']['address'] if choosed_pool['baseToken']['address'].lower() != '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['quoteToken']['address']
            args = token, balance, 0, 0, account.address, int(time.time() + 60 * 60)
        else:
            func = 'removeLiquidity'
            args = choosed_pool['baseToken']['address'], choosed_pool['quoteToken']['address'], balance, 0, 0, account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.rem_liq(private_key=private_key)
        return new_w3.to_hex(hash)

#+
class Alienbase_liq():

    def __init__(self, w3, helper):
        self.w3 = w3
        self.helper = helper
        self.project = 'ALIENBASE'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(CONTRACT_DATA), abi=DATA_ABI)
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

    def add_liq(self, amount, token_from, private_key, attempt=0):

        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])

        user_tokens = {}
        user_tokens_ = self.contract_data.functions.getBalances(account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3] / (10 ** t[2]))}

        good_pools = []
        for p in self.pools:
            token_to = p['token0']['id'] if p['token0']['id'].lower() != token_from_data['address'].lower() else p['token1']['id']
            if p['token0']['id'].lower() == token_from_data['address'].lower() or p['token1']['id'].lower() == token_from_data['address'].lower():
                try:
                    token_to_data = user_tokens[token_to.lower()]
                    # if token_to_data['symbol'] not in [token['symbol'] for token in tokens_data_.values() if token['liq']]:
                    #     continue
                    if token_to_data['balance'] > 0:
                        good_pools.append({'pair': p['pairAddress'],'tokenA': new_w3.to_checksum_address(token_from_data['address']),"tokenB": new_w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance']})
                except:
                    pass

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            if choosed_pool[token].lower() == '0x4200000000000000000000000000000000000006'.lower():
                continue
            approve = check_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])

        pair = new_w3.eth.contract(address=new_w3.to_checksum_address(choosed_pool['pair']), abi=swaps_data[self.project]['ABI_pool'])
        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()
        reserve0 = reserves[0] if token0.lower() == token_from_data['address'].lower() else reserves[1]
        reserve1 = reserves[0] if reserve0 != reserves[0] else reserves[1]

        amountB = self.contract.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
        if amountB < choosed_pool['amountB']:
            amountA = self.contract.functions.quote(amountB, reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            choosed_pool['amountB'] = amountB
        if amountB > choosed_pool['amountB']:
            amountA = self.contract.functions.quote(choosed_pool['amountB'], reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            amountB = self.contract.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
            choosed_pool['amountB'] = amountB

        if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['tokenB'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'addLiquidityETH'
            value = choosed_pool['amountA'] if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['amountB']
            if choosed_pool['tokenB'] != '0x4200000000000000000000000000000000000006':
                args = choosed_pool['tokenB'], choosed_pool['amountB'], int(choosed_pool['amountB'] * 0.95), int( choosed_pool['amountA'] * 0.95), account.address, int(time.time() + 60 * 60)
            else:
                args = choosed_pool['tokenA'], choosed_pool['amountA'], int(choosed_pool['amountA'] * 0.95), int( choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)
        else:
            func = 'addLiquidity'
            value = 0
            args = choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['amountA'], choosed_pool['amountB'], int(choosed_pool['amountA'] * 0.95), int(choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.add_liq(amount=amount, token_from=token_from, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

    def rem_liq(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        good_pools = [p for p in self.pools if get_balance(new_w3, account, p['pairAddress']) > 0]
        if len(good_pools) == 0:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        approve = check_approve(new_w3, account, choosed_pool['pairAddress'], swaps_data[self.project]['contract'])
        if not approve:
            make_approve(new_w3, account, choosed_pool['pairAddress'], swaps_data[self.project]['contract'])

        balance = get_balance(new_w3, account, choosed_pool['pairAddress'])

        if choosed_pool['token0']['id'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['token1']['id'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'removeLiquidityETH'
            token = choosed_pool['token0']['id'] if choosed_pool['token0']['id'].lower() != '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['token1']['id']
            args = new_w3.to_checksum_address(token), balance, 0, 0, account.address, int(time.time() + 60 * 60)
        else:
            func = 'removeLiquidity'
            args = new_w3.to_checksum_address(choosed_pool['token0']['id']), new_w3.to_checksum_address(choosed_pool['token1']['id']), balance, 0, 0, account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.rem_liq(private_key=private_key)
        return new_w3.to_hex(hash)

#something wrong with pools (different routes)
class Swapbased_liq():

    def __init__(self, w3, helper):
        self.w3 = w3
        self.helper = helper
        self.project = 'SWAPBASED'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']), abi=swaps_data[self.project]['ABI'])
        self.contract_quoter = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_quoter']),abi=swaps_data[self.project]['ABI_quoter'])
        self.contract_v2 = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_v2']), abi=swaps_data[self.project]['ABI_v2'])
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(CONTRACT_DATA), abi=DATA_ABI)
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                payload = {"query":"\n      query MyQuery { pairs(orderBy: reserveUSD, first: 15, orderDirection: desc) { id token0 { decimals id name symbol } token1 { decimals id name symbol } volumeUSD reserveUSD } }"}
                result = self.helper.fetch_url(url='https://api.thegraph.com/subgraphs/name/chimpydev/swapbase',type='post', payload=payload)
                return result['data']['pairs']
            except:
                time.sleep(i * 1)
        return []

    def add_liq(self, amount, token_from, private_key, attempt=0):

        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])

        user_tokens = {}
        user_tokens_ = self.contract_data.functions.getBalances(account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3] / (10 ** t[2]))}

        good_pools = []
        for p in self.pools:
            token_to = p['token0']['id'] if p['token0']['id'].lower() != token_from_data['address'].lower() else p['token1']['id']
            if p['token0']['id'].lower() == token_from_data['address'].lower() or p['token1']['id'].lower() == token_from_data['address'].lower():
                try:
                    token_to_data = user_tokens[token_to.lower()]
                    # if token_to_data['symbol'] not in [token['symbol'] for token in tokens_data_.values() if token['liq']]:
                    #     continue
                    if token_to_data['balance'] > 0:
                        good_pools.append({'pair': p['id'],'tokenA': new_w3.to_checksum_address(token_from_data['address']),"tokenB": new_w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance']})
                except:
                    pass

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            if choosed_pool[token].lower() == '0x4200000000000000000000000000000000000006'.lower():
                continue
            approve = check_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract_v2'])
            if not approve:
                make_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract_v2'])

        pair = new_w3.eth.contract(address=new_w3.to_checksum_address(choosed_pool['pair']), abi=swaps_data[self.project]['ABI_pool'])
        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()
        reserve0 = reserves[0] if token0.lower() == token_from_data['address'].lower() else reserves[1]
        reserve1 = reserves[0] if reserve0 != reserves[0] else reserves[1]

        amountB = self.contract_v2.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
        if amountB < choosed_pool['amountB']:
            amountA = self.contract_v2.functions.quote(amountB, reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            choosed_pool['amountB'] = amountB
        if amountB > choosed_pool['amountB']:
            amountA = self.contract_v2.functions.quote(choosed_pool['amountB'], reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            amountB = self.contract_v2.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
            choosed_pool['amountB'] = amountB

        if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['tokenB'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'addLiquidityETH'
            value = choosed_pool['amountA'] if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['amountB']
            if choosed_pool['tokenB'] != '0x4200000000000000000000000000000000000006':
                args = choosed_pool['tokenB'], choosed_pool['amountB'], int(choosed_pool['amountB'] * 0.95), int(choosed_pool['amountA'] * 0.95), account.address, int(time.time() + 60 * 60)
            else:
                args = choosed_pool['tokenA'], choosed_pool['amountA'], int(choosed_pool['amountA'] * 0.95), int( choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)
        else:
            func = 'addLiquidity'
            args = choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['amountA'], choosed_pool['amountB'], int(choosed_pool['amountA'] * 0.95), int(choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)
            value = 0

        func_ = getattr(self.contract_v2.functions, func)

        tx = make_tx(new_w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.add_liq(amount=amount, token_from=token_from, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

    def rem_liq(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        good_pools = [p for p in self.pools if get_balance(new_w3, account, p['id']) > 0]
        if len(good_pools) == 0:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        approve = check_approve(new_w3, account, choosed_pool['id'], swaps_data[self.project]['contract_v2'])
        if not approve:
            make_approve(new_w3, account, choosed_pool['id'], swaps_data[self.project]['contract_v2'])

        balance = get_balance(new_w3, account, choosed_pool['id'])

        if choosed_pool['token0']['id'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['token1']['id'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'removeLiquidityETH'
            token = choosed_pool['token0']['id'] if choosed_pool['token0']['id'].lower() != '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['token1']['id']
            args = new_w3.to_checksum_address(token), balance, 0, 0, account.address, int(time.time() + 60 * 60)
        else:
            func = 'removeLiquidity'
            args = new_w3.to_checksum_address(choosed_pool['token0']['id']), new_w3.to_checksum_address(choosed_pool['token1']['id']), balance, 0, 0, account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract_v2.functions, func)

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.rem_liq(private_key=private_key)
        return new_w3.to_hex(hash)

#TODO
class Sushi_liq():
    def __init__(self, w3, logger, helper):
        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'SUSHISWAP'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_liq']), abi=swaps_data[self.project]['ABI_liq'])
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data['AERODROME']['contract_data']), abi=swaps_data['AERODROME']['ABI_data'])
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                result = self.helper.fetch_url(url='https://pools.sushi.com/api/v0?chainIds=8453&isWhitelisted=true&orderBy=liquidityUSD&orderDir=desc&protocols=SUSHISWAP_V3,SUSHISWAP_V2,BENTOBOX_STABLE,BENTOBOX_CLASSIC',type='get')
                return result
            except:
                time.sleep(i * 1)
        return []

    def add_liq(self, amount, token_from, private_key, attempt=0):

        if attempt > 5:
            return 'error'

        account = self.w3.eth.account.from_key(private_key)

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])

        user_tokens = {}
        user_tokens_ = self.contract_data.functions.tokens(20000, 0, account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3] / (10 ** t[2]))}

        good_pools = []
        for p in self.pools:
            token_to = p['token0']['id'] if p['token0']['id'].lower() != token_from_data['address'].lower() else p['token1']['id']
            if p['token0']['id'].lower() == token_from_data['address'].lower() or p['token1']['id'].lower() == token_from_data['address'].lower():
                try:
                    token_to_data = user_tokens[token_to.lower()]
                    if token_to_data['balance'] > 0:
                        good_pools.append({'pair': p['pairAddress'],'tokenA': self.w3.to_checksum_address(token_from_data['address']),"tokenB": self.w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance']})
                except:
                    pass

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            if token_from == '0x4200000000000000000000000000000000000006':
                continue
            approve = check_approve(self.w3, account, choosed_pool[token], swaps_data[self.project]['contract_liq'])
            if not approve:
                make_approve(self.w3, account, choosed_pool[token], swaps_data[self.project]['contract_liq'])

#+
class Synthswap_liq():

    def __init__(self, w3, helper):
        self.w3 = w3
        self.helper = helper
        self.project = 'SYNTHSWAP'
        self.available_tokens = tokens_data_
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract_v2']),abi=swaps_data[self.project]['ABI_v2'])
        self.pools = self.get_pools()
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(CONTRACT_DATA), abi=DATA_ABI)

    def get_pools(self):
        for i in range(5):
            try:
                # result = self.helper.fetch_url(url='https://api.dexscreener.com/latest/dex/pairs/base/0x2c1e1a69ee809d3062ace40fb83a9bfb59623d95,0xac5af1706cc42a7c398c274c3b8ecf735e7ecb28,0x277301a4c042b5d1bdf61ab11027c2c42286afd1,0xe0712c087ecb8a0dd20914626152ebf4890708c2,0x3458ffdc3b2cc274a9d8aa8d9b0b934558b7a498,0xc33c91a7b3e62ef8f7c7870daec7af0f524abd6a',type='get')
                # return result['pairs']
                payload = {
                    "query": "\n      query MyQuery { pairs(first: 20, orderBy: txCount, orderDirection: desc) { id reserve0 reserve1 reserveUSD token0 { decimals id name symbol } token1 { decimals id name symbol } } }"}
                result = self.helper.fetch_url(
                    url='https://api.studio.thegraph.com/query/45189/synthswap-dex-v2/version/latest', type='post',
                    payload=payload)
                return result['data']['pairs']
            except:
                time.sleep(i * 1)
        return []

    def add_liq(self, amount, token_from, private_key, attempt=0):

        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])

        user_tokens = {}
        user_tokens_ = self.contract_data.functions.getBalances(account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3] / (10 ** t[2]))}

        good_pools = []
        for p in self.pools:
            token_to = p['token0']['id'] if p['token0']['id'].lower() != token_from_data['address'].lower() else p['token1']['id']
            if p['token0']['id'].lower() == token_from_data['address'].lower() or p['token1']['id'].lower() == token_from_data['address'].lower():
                try:
                    token_to_data = user_tokens[token_to.lower()]
                    # if token_to_data['symbol'] not in [token['symbol'] for token in tokens_data_.values() if token['liq']]:
                    #     continue
                    if token_to_data['balance'] > 0:
                        good_pools.append({'pair': p['id'],'tokenA': new_w3.to_checksum_address(token_from_data['address']),"tokenB": new_w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance']})
                except:
                    pass

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            if choosed_pool[token].lower() == '0x4200000000000000000000000000000000000006'.lower():
                continue
            approve = check_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract_v2'])
            if not approve:
                make_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract_v2'])

        pair = new_w3.eth.contract(address=self.w3.to_checksum_address(choosed_pool['pair']), abi=swaps_data[self.project]['ABI_pool'])
        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()
        reserve0 = reserves[0] if token0.lower() == token_from_data['address'].lower() else reserves[1]
        reserve1 = reserves[0] if reserve0 != reserves[0] else reserves[1]

        amountB = self.contract.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
        if amountB < choosed_pool['amountB']:
            amountA = self.contract.functions.quote(amountB, reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            choosed_pool['amountB'] = amountB
        if amountB > choosed_pool['amountB']:
            amountA = self.contract.functions.quote(choosed_pool['amountB'], reserve1, reserve0).call()
            choosed_pool['amountA'] = amountA
            amountB = self.contract.functions.quote(choosed_pool['amountA'], reserve0, reserve1).call()
            choosed_pool['amountB'] = amountB

        if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['tokenB'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'addLiquidityETH'
            value = choosed_pool['amountA'] if choosed_pool['tokenA'].lower() == '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['amountB']
            if choosed_pool['tokenB'] != '0x4200000000000000000000000000000000000006':
                args = choosed_pool['tokenB'], choosed_pool['amountB'], int(choosed_pool['amountB'] * 0.95), int( choosed_pool['amountA'] * 0.95), account.address, int(time.time() + 60 * 60)
            else:
                args = choosed_pool['tokenA'], choosed_pool['amountA'], int(choosed_pool['amountA'] * 0.95), int( choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)
        else:
            func = 'addLiquidity'
            value = 0
            args = choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['amountA'], choosed_pool['amountB'], int(choosed_pool['amountA'] * 0.95), int(choosed_pool['amountB'] * 0.95), account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=value, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.add_liq(amount=amount, token_from=token_from, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

    def rem_liq(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        good_pools = [p for p in self.pools if get_balance(new_w3, account, p['id']) > 0]
        if len(good_pools) == 0:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        approve = check_approve(new_w3, account, choosed_pool['id'], swaps_data[self.project]['contract_v2'])
        if not approve:
            make_approve(new_w3, account, choosed_pool['id'], swaps_data[self.project]['contract_v2'])

        balance = get_balance(new_w3, account, choosed_pool['id'])

        if choosed_pool['token0']['id'].lower() == '0x4200000000000000000000000000000000000006'.lower() or choosed_pool['token1']['id'].lower() == '0x4200000000000000000000000000000000000006'.lower():
            func = 'removeLiquidityETH'
            token = choosed_pool['token0']['id'] if choosed_pool['token0']['id'].lower() != '0x4200000000000000000000000000000000000006'.lower() else choosed_pool['token1']['id']
            args = new_w3.to_checksum_address(token), balance, 0, 0, account.address, int(time.time() + 60 * 60)
        else:
            func = 'removeLiquidity'
            args = new_w3.to_checksum_address(choosed_pool['token0']['id']), new_w3.to_checksum_address(choosed_pool['token1']['id']), balance, 0, 0, account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, func)

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.rem_liq(private_key=private_key)
        return new_w3.to_hex(hash)

#+ ? (NOT ETH)
class Equalizer_liq():

    def __init__(self, w3, helper):
        self.project = 'EQUALIZER'
        self.headers = {
            'authority': 'eqapi-base-vkgqs.ondigitalocean.app',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://base.equalizer.exchange',
            'referer': 'https://base.equalizer.exchange/',
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
        self.contract_data = self.w3.eth.contract(address=self.w3.to_checksum_address(CONTRACT_DATA), abi=DATA_ABI)
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(swaps_data[self.project]['contract']),abi=swaps_data[self.project]['ABI'])
        self.pools = self.get_pools()

    def get_pools(self):
        for i in range(5):
            try:
                result = self.help.fetch_url(url='https://eqapi-base-vkgqs.ondigitalocean.app/base/wallet/0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191/pairs', type='get', headers=self.headers)
                pools = []
                for pool in result['data']:
                    try:
                        if pool.get('gaugesAddress', None):
                            pools.append(pool)
                    except:
                        pass
                return pools
            except:
                time.sleep(i * 1)
        return []

    def add_liq(self, amount, token_from, private_key, attempt=0):

        if attempt > 5:
            return 'error'

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token_from_data = self.available_tokens[token_from]
        _amount = int(amount * 10 ** token_from_data['decimal'])
        if token_from == "ETH":
            token_from = "WETH"
            token_from_data = self.available_tokens[token_from]
            if get_balance(new_w3, account, '0x4200000000000000000000000000000000000006') < _amount:
                wrap = eth_wrapper(_amount, 'WETH', new_w3, private_key['private_key'], in_decimals=False)

        user_tokens = {}
        user_tokens_ = self.contract_data.functions.getBalances(account.address).call()
        for t in user_tokens_:
            user_tokens[t[0].lower()] = {"address": t[0], "symbol": t[1], "decimal": t[2], 'balance': t[3], "amount": float(t[3] / (10 ** t[2]))}

        good_pools = []
        for p in self.pools:
            token_to = p['token0']['address'] if p['token0']['address'].lower() != token_from_data['address'].lower() else p['token1']['address']
            if p['token0']['address'].lower() == token_from_data['address'].lower() or p['token1']['address'].lower() == token_from_data['address'].lower():
                try:
                    token_to_data = user_tokens[token_to.lower()]
                    # if token_to_data['symbol'] not in [token['symbol'] for token in tokens_data_.values() if token['liq']]:
                    #     continue
                    if token_to_data['balance'] > 0:
                        good_pools.append({'pair': p['address'],'tokenA': new_w3.to_checksum_address(token_from_data['address']),"tokenB": new_w3.to_checksum_address(token_to), "amountA": _amount, "amountB": token_to_data['balance'], "stable": p['stable']})
                except:
                    pass

        if not good_pools:
            return 'no_route'
        choosed_pool = random.choice(good_pools)

        for token in ['tokenA', 'tokenB']:
            approve = check_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])
            if not approve:
                make_approve(new_w3, account, choosed_pool[token], swaps_data[self.project]['contract'])

        data = self.contract.functions.quoteAddLiquidity(choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['stable'], choosed_pool['amountA'], choosed_pool['amountB']).call()
        choosed_pool['amountA'] = data[0]
        choosed_pool['amountB'] = data[1]

        args = choosed_pool['tokenA'], choosed_pool['tokenB'], choosed_pool['stable'], choosed_pool['amountA'], choosed_pool['amountB'], int(0), int(0), account.address, int(time.time() + 60 * 60)

        func_ = getattr(self.contract.functions, 'addLiquidity')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.add_liq(amount=amount, token_from=token_from, private_key=private_key, attempt=attempt + 1)
        return new_w3.to_hex(hash)

    def rem_liq(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        gauge_pool = True
        good_gauge_pools = [p for p in self.pools if get_balance(new_w3, account, p['gaugesAddress']) > 0]
        if len(good_gauge_pools) == 0:
            gauge_pool = False
            good_pools = [p for p in self.pools if get_balance(new_w3, account, p['address']) > 0]
            if len(good_pools) == 0:
                return 'no_route'
            else:
                choosed_pool = random.choice(good_pools)
                balance = get_balance(new_w3, account, choosed_pool['address'])
        else:
            choosed_pool = random.choice(good_gauge_pools)
            balance = get_balance(new_w3, account, choosed_pool['gaugesAddress'])

        if gauge_pool:
            gauge_pool = new_w3.eth.contract(address=new_w3.to_checksum_address(choosed_pool['gaugesAddress']), abi=swaps_data[self.project]['ABI_gauge'])
            func_ = getattr(gauge_pool.functions, 'withdraw')

            tx = make_tx(new_w3, account, value=0, func=func_, args=balance, args_positioning=False)

            if tx == "low_native" or not tx:
                return tx

            sign = account.sign_transaction(tx)
            hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
            tx_status = check_for_status(new_w3, hash)
            if not tx_status:
                return self.rem_liq(private_key=private_key)

        approve = check_approve(new_w3, account, choosed_pool['address'], swaps_data[self.project]['contract'])
        if not approve:
            make_approve(new_w3, account, choosed_pool['address'], swaps_data[self.project]['contract'])

        args = new_w3.to_checksum_address(choosed_pool['token0']['address']), new_w3.to_checksum_address(choosed_pool['token1']['address']), choosed_pool['stable'], balance, 0, 0, account.address, int(time.time() + 60 * 60)
        func_ = getattr(self.contract.functions, 'removeLiquidity')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.rem_liq(private_key=private_key)
        return new_w3.to_hex(hash)


def initialize_liquidity(classes_to_init, w3, helper):
    available_swaps = {
        "Aerodrome_liq": Aerodrome_liq,
        "Baseswap_liq": Baseswap_liq,
        "Alienbase_liq": Alienbase_liq,
        "Swapbased_liq": Swapbased_liq,
        "Synthswap_liq": Synthswap_liq,
        "Equalizer_liq": Equalizer_liq,
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, helper)

    return initialized_objects

