from helpers.utils import *
from helpers.data import derivs_data

#fee 0 ETH
class Onchain():
    def __init__(self, w3, helper, logger):
        self.project = 'ONCHAIN TRADE'
        self.help = helper
        self.logger = logger
        self.w3 = w3
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(derivs_data['onchain']['contract']), abi=derivs_data['onchain']['ABI'])
        self.contract_reader = self.w3.eth.contract(address=self.w3.to_checksum_address(derivs_data['onchain']['contract_reader']), abi=derivs_data['onchain']['ABI_reader'])

    def check_positions(self, account):
        tokens = {'0x13E97db9ad7a736005d229302E9eF9bDc6c538fF'.lower(): 'BTC', '0x4200000000000000000000000000000000000006'.lower(): 'ETH'}
        positions = []
        data = self.contract_reader.functions.getPositionList2(account.address).call()
        for i in range(len(data[0]) - 1):
            if int(data[3][i * 12]) != 0:
                position = {
                    "collateral": data[0][i],
                    "index": data[1][i],
                    "token": tokens.get(data[1][i].lower(), 'NONE'),
                    "is_long": data[2][i],
                    "margin": int(data[3][i * 12]),
                    "notional": int(data[3][i * 12 + 1]),
                    "size": int(data[3][i * 12 + 2]),
                    "entry_finding": int(data[3][i * 12 + 3]),
                    "entry_index": int(data[3][i * 12 + 4]),
                    "entry_collateral": int(data[3][i * 12 + 5]),
                    "mmr": int(data[3][i * 12 + 6]),
                    "funding_fee": int(data[3][i * 12 + 7]),
                    "trading_fee": int(data[3][i * 12 + 8]),
                    "pnl": int(data[3][i * 12 + 9]),
                    "remain_margin": int(data[3][i * 12 + 10]),
                    "margin_ratio": int(data[3][i * 12 + 11]),
                }
                positions.append(position)
        return positions

    def make_position(self, account, amount, new_w3, leverage=False):

        _amount = int(amount * 10 ** 6)

        approve = check_approve(new_w3, account, '0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca', derivs_data['onchain']['contract'])
        if not approve:
            make_approve(new_w3, account, '0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca', derivs_data['onchain']['contract'])

        pos_type = random.choice([True, False])
        min_out = int(_amount * 10 ** 12 * (1.01 if pos_type else 0.99999))

        if leverage:
            leverage = random.uniform(1, 3)
            min_out = int(min_out * leverage)
        token_to = random.choice([{'address': '13E97db9ad7a736005d229302E9eF9bDc6c538fF', 'token': 'BTC'}, {'address': '4200000000000000000000000000000000000006', 'token': 'ETH'}])
        args = new_w3.to_checksum_address('d9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'), new_w3.to_checksum_address('139f18aC2a9FA34E0225FD2AAE983fc969b35540'), new_w3.to_checksum_address(token_to['address']), pos_type, _amount, 0, min_out, 0, 0
        func_ = getattr(self.contract.functions, 'increasePosition')
        tx = make_tx(new_w3, account, func=func_, args=args, gas_multiplier=1)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.make_position(account=account, amount=amount, new_w3=new_w3, leverage=leverage)

        self.logger.log_success(f"{self.project} | Успешно открыл {'LONG' if pos_type else 'SHORT'} позицию токена {token_to['token']} {f'с плечём {round(leverage, 2)} ' if leverage else ''}размером {round(amount, 3)} USDC", account.address)
        return new_w3.to_hex(hash)

    def close_position(self, account, position, new_w3):

        args = new_w3.to_checksum_address(position['collateral']), new_w3.to_checksum_address(position['index']), position['is_long'], position['trading_fee'], \
        position['notional'], position['entry_collateral'], position['entry_index'], account.address, new_w3.to_checksum_address('d9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA')

        func_ = getattr(self.contract.functions, 'decreasePosition')
        tx = make_tx(new_w3, account, func=func_, args=args, gas_multiplier=1)

        if tx == "low_native" or not tx:
            return tx
        if tx == 'already_closed':
            return 'no_positions'

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.close_position(account=account, position=position, new_w3=new_w3)

        self.logger.log_success(f"{self.project} | Успешно закрыл {'LONG' if position['is_long'] else 'SHORT'} позицию токена {position['token']} размером {round(position['notional']/10**18, 3)} USDC",account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key, amount, withdraw_all=False):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        positions = self.check_positions(account)

        if not positions:
            if withdraw_all:
                return 'no_positions'
            return self.make_position(account, amount, new_w3)
        else:
            return self.close_position(account, random.choice(positions), new_w3)

#fee 0.00025 ETH
class Unidex():
    def __init__(self, w3, helper, logger):
        self.project = 'UNIDEX'
        self.help = helper
        self.logger = logger
        self.w3 = w3
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(derivs_data['unidex']['contract']), abi=derivs_data['unidex']['ABI'])

    def check_positions(self, account):

        for i in range(5):
            try:
                url = "https://base.tempsubgraph.xyz/subgraphs/name/unidex-finance/baseleveragev2"
                query = f"query MyQuery {{ positions(where: {{ user: \"{account.address}\" }}) {{ id createdAtBlockNumber createdAtTimestamp currency fee isLong leverage liquidationPrice price margin productId size updatedAtBlockNumber updatedAtTimestamp user }} }}"
                payload = {"query": query}
                res = self.help.fetch_url(url=url, payload=payload, type='post')
                return res['data']['positions']
            except:
                time.sleep(i*1)
        return []

    def make_position(self, account, amount, new_w3, leverage=False):

        _amount = int(amount * 10 ** 8)
        __amount = int(amount * 10 ** 18)

        pos_type = random.choice([True, False])
        markets = [{'address': '0x4254432d55534400000000000000000000000000000000000000000000000000', 'token': 'BTC'}, {'address': '0x4554482d55534400000000000000000000000000000000000000000000000000', 'token': 'ETH'}]
        pos_market = random.choice(markets)
        token = new_w3.to_checksum_address('0000000000000000000000000000000000000000')

        if leverage:
            leverage = random.randint(1, 5)
            amount_with_leverage = int(_amount * leverage)
        else:
            amount_with_leverage = _amount

        args = pos_market['address'], token, '0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191', pos_type, '0x0000000000000000000000000000000000000000000000000000000000000000', int(_amount), amount_with_leverage
        func_ = getattr(self.contract.functions, 'submitOrder')
        tx = make_tx(new_w3, account, func=func_, args=args, gas_multiplier=0.7, value=new_w3.to_wei(0.00025, 'ether')+__amount)

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.make_position(account=account, amount=amount, new_w3=new_w3, leverage=leverage)

        self.logger.log_success(f"{self.project} | Успешно открыл {'LONG' if pos_type else 'SHORT'} позицию токена {pos_market['token']} {f'с плечём {round(leverage, 2)} ' if leverage else ''}размером {round(amount, 6)} ETH", account.address)
        return new_w3.to_hex(hash)

    def close_position(self, account, position, new_w3):

        token = 'BTC' if position['productId'] == '0x4254432d55534400000000000000000000000000000000000000000000000000' else 'ETH'
        args = position['productId'], new_w3.to_checksum_address(position['currency']), '0x5f67ffa4b3f77DD16C9C34A1A82CaB8dAea03191', position['isLong'], '0x0000000000000000000000000000000000000000000000000000000000000000', int(position['size'])
        func_ = getattr(self.contract.functions, 'submitCloseOrder')
        tx = make_tx(new_w3, account, func=func_, args=args, gas_multiplier=0.7, value=new_w3.to_wei(0.0003, 'ether'))

        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.close_position(account=account, position=position, new_w3=new_w3)

        self.logger.log_success(f"{self.project} | Успешно закрыл {'LONG' if position['isLong'] else 'SHORT'} позицию токена {token} размером {round(int(position['size'])/10**8, 6)} ETH",account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key, amount, withdraw_all=False):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        positions = self.check_positions(account)

        if not positions:
            if withdraw_all:
                return 'no_positions'
            return self.make_position(account, amount, new_w3)
        else:
            return self.close_position(account, random.choice(positions), new_w3)

def initialize_derives(classes_to_init, w3, logger, helper):
    available_swaps = {
        "Onchain": Onchain,
        "Unidex": Unidex,
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, helper, logger)

    return initialized_objects

