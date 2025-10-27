from helpers.utils import *
from helpers.data import lending_data, tokens_data

class Granary():
    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'GRANARY'
        self.logger = logger
        self.eth_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['ETH']), abi=lending_data[self.project]['ABI']['ETH'])
        self.usdc_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['USDBC']), abi=lending_data[self.project]['ABI']['USDBC'])
        self.contract_data = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['DATA']), abi=lending_data[self.project]['ABI']['DATA'])
        self.contract_pool = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['POOL']), abi=lending_data[self.project]['ABI']['POOL'])

    def redeem(self, value, token, account, new_w3):
        if token == "ETH":
            allowance = check_approve(new_w3, account, '0x9c29a8eC901DBec4fFf165cD57D4f9E03D4838f7', lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, '0x9c29a8eC901DBec4fFf165cD57D4f9E03D4838f7', lending_data[self.project]['contracts'][token])
        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'withdraw' if token == 'USDBC' else 'withdrawETH')
        args = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', 115792089237316195423570985008687907853269984665640564039457584007913129639935, account.address] if token == 'USDBC' else ['0xB702cE183b4E1Faa574834715E5D4a6378D0eEd3', 115792089237316195423570985008687907853269984665640564039457584007913129639935, account.address]
        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def mint(self, value, token, account, new_w3):
        if token == "USDBC":
            allowance = check_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])

        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'depositETH' if token == 'ETH' else 'deposit')
        args = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', value, account.address, 0] if token == 'USDBC' else ['0xB702cE183b4E1Faa574834715E5D4a6378D0eEd3', account.address, 0]
        tx = make_tx(new_w3, account, value=0 if token == 'USDBC' else value, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def main(self, private_key, token, value, withdraw = False, attempt = 0):

        value = int(value * 10 ** 18) if token == 'ETH' else int(value * 10 ** 6)
        ETH_PRICE = float(self.help.get_prices()['ETH'])

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        if token == 'USDBC':
            value = min(value, get_balance(new_w3, account, '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'))

        snapshot_eth = self.contract_data.functions.getUserReserveData('0x4200000000000000000000000000000000000006', account.address).call()
        snapshot_usdc = self.contract_data.functions.getUserReserveData('0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', account.address).call()
        supplied, c_stable_debt, c_variable_debt, p_stable_debt, s_variable_debt, s_borrow_rate, l_rate, stabe_rate_last, use_as_col = snapshot_eth
        supplied_, c_stable_debt_, c_variable_debt_, p_stable_debt_, s_variable_debt_, s_borrow_rate_, l_rate_, stabe_rate_last_, use_as_col_ = snapshot_usdc

        tokens = {}
        tokens['ETH'] = {"supplied": supplied, "borrowed": c_variable_debt, "repay_token": "USDC", 'decimals': 18}
        tokens['USDBC'] = {"supplied": supplied_, "borrowed": c_variable_debt_, "repay_token": "ETH", 'decimals': 6}

        if withdraw and (tokens['ETH']['supplied'] < 10**12 and tokens['USDBC']['supplied'] < 10000 and tokens['ETH']['borrowed'] < 10**12and tokens['USDBC']['borrowed'] < 1000):
            return 'good'

        need_borrow, need_supply, need_redeem = False, False, False
        # if (tokens['ETH']['supplied'] > 10 ** 16 or tokens['USDC']['supplied'] > 10000000) and (tokens['ETH']['borrowed'] < 10 ** 12 and tokens['USDC']['borrowed'] < 10000):
        #     need_borrow = True
        if 0.01 < tokens[token]['supplied'] / (10 ** tokens[token]['decimals']) * ETH_PRICE:
            need_redeem = True
        else:
            need_supply = True
        if withdraw:
            need_borrow, need_supply, need_redeem = False, False, True

        if need_supply:
            self.logger.log(f"{self.project} | Делаю SUPPLY {value/(10**tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash = self.mint(value, token, account, new_w3)
            if tx_hash and tx_hash != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал SUPPLY ({value/(10**tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash
        # elif need_borrow:
        #     borrow_value = random.randint(int(tokens[tokens[token]['repay_token']]['max_borrow']*0.5), int(tokens[tokens[token]['repay_token']]['max_borrow']*0.95))
        #     self.logger.log(f"{self.project} | Делаю BORROW {borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}", wallet=account.address)
        #     tx_hash = self.borrow(borrow_value, tokens[token]['repay_token'], account)
        #     if tx_hash and tx_hash != 'low_native':
        #         self.logger.log_success(f"{self.project} | Сделал BORROW ({borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}) успешно!", wallet=account.address)
        #     return tx_hash
        elif need_redeem:
            if tokens[token]['supplied'] == 0:
                return True
            # balance = self.w3.eth.get_balance(account.address) if tokens[token]['repay_token'] == 'ETH' else get_balance(self.w3, account, tokens_data['USDC']['address'])
            # borrowed_value = min(balance, tokens[tokens[token]['repay_token']]['actual_borrowed'])
            #
            # if borrowed_value == 0 and tokens[tokens[token]['repay_token']]['actual_borrowed'] > balance:
            #     return f'swap_{tokens[token]["repay_token"]}_{tokens[tokens[token]["repay_token"]]["actual_borrowed"]-balance}'
            # if borrowed_value > (1000 if tokens[token]['repay_token'] == 'USDC' else 10**12):
            #     self.logger.log(f"{self.project} | Делаю REPAY {borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}",wallet=account.address)
            #     tx_hash = self.repay(borrowed_value, tokens[token]['repay_token'], account)
            #     if tx_hash and tx_hash != 'low_native':
            #         self.logger.log_success(f"{self.project} | Сделал REPAY ({borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])}) успешно!", wallet=account.address)
            #     time.sleep(random.uniform(3, 5))
            #if (tokens[token]['supplied'] > 10**12 if token == 'ETH' else 1000) and tokens[token]['supplied'] != 0:
            self.logger.log(f"{self.project} | Делаю WITHDRAW {tokens[token]['supplied'] / (10 ** tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash_ = self.redeem(tokens[token]['supplied'], token, account, new_w3)
            if tx_hash_ and tx_hash_ != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash_)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал WITHDRAW ({tokens[token]['supplied'] / (10 ** tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash_

class Moonwell():
    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'MOONWELL'
        self.logger = logger
        self.eth_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['ETH']), abi=lending_data[self.project]['ABI']['ETH'])
        self.eth_contract2 = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['ETH2']), abi=lending_data[self.project]['ABI']['ETH2'])
        self.usdc_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['USDBC']), abi=lending_data[self.project]['ABI']['USDBC'])
        self.markets_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['MARKETS']),abi=lending_data[self.project]['ABI']['MARKETS'])

    def check_markets(self, account, new_w3):
        addresses = self.markets_contract.functions.getAllMarkets().call()
        for address_ in addresses:
            if not self.markets_contract.functions.checkMembership(account.address, new_w3.to_checksum_address(address_)).call():
                func_ = getattr(self.markets_contract.functions, 'enterMarkets')
                tx = make_tx(new_w3, account, func=func_, args=addresses, args_positioning=False)
                if tx == "low_native" or not tx:
                    return tx
                sign = account.sign_transaction(tx)
                hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
                return new_w3.to_hex(hash)
        return

    def redeem(self, value, token, account, new_w3):
        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'redeem')
        tx = make_tx(new_w3, account, value=0, func=func_, args=value, args_positioning=False)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def mint(self, value, token, account, new_w3):
        if token == "USDBC":
            allowance = check_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])

        func_ = getattr(self.eth_contract2.functions if token == 'ETH' else self.usdc_contract.functions, 'mint')
        args = value if token == 'USDBC' else account.address
        tx = make_tx(new_w3, account, value=0 if token == 'USDBC' else value, func=func_, args=args, args_positioning=False)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def main(self, private_key, token, value, withdraw = False, attempt = 0):

        value = int(value * 10 ** 18) if token == 'ETH' else int(value * 10 ** 6)
        ETH_PRICE = float(self.help.get_prices()['ETH'])

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        if token == 'USDBC':
            value = min(value, get_balance(new_w3, account, '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'))

        snapshot_eth = self.eth_contract.functions.getAccountSnapshot(account.address).call()
        snapshot_usdc = self.usdc_contract.functions.getAccountSnapshot(account.address).call()
        _, balance, borrow_balance, rate = snapshot_eth
        _, balance_, borrow_balance_, rate_ = snapshot_usdc

        tokens = {}
        tokens['ETH'] = {"actual_supplied": int(balance * rate / (10 ** 18)), "protocol_supplied": balance, "actual_borrowed": borrow_balance, "protocol_borrower": borrow_balance, "repay_token": "USDC",'decimals': 18}
        tokens['USDBC'] = {"actual_supplied": int(balance_ * rate_ / (10 ** 18)), "protocol_supplied": balance_, "actual_borrowed": borrow_balance_, "protocol_borrower": borrow_balance_,"repay_token": "ETH", 'decimals': 6}

        if withdraw and (tokens['ETH']['actual_supplied'] < 10**12 and tokens['USDBC']['actual_supplied'] < 10000 and tokens['ETH']['actual_borrowed'] < 10**12 and tokens['USDBC']['actual_borrowed'] < 1000):
            return 'good'

        need_borrow, need_supply, need_redeem = False, False, False
        # if (tokens['ETH']['supplied'] > 10 ** 16 or tokens['USDC']['supplied'] > 10000000) and (tokens['ETH']['borrowed'] < 10 ** 12 and tokens['USDC']['borrowed'] < 10000):
        #     need_borrow = True
        if 0.01 < tokens[token]['actual_supplied'] / (10 ** tokens[token]['decimals']) * ETH_PRICE:
            need_redeem = True
        else:
            need_supply = True
        if withdraw:
            need_borrow, need_supply, need_redeem = False, False, True

        if need_supply:
            self.logger.log(f"{self.project} | Делаю SUPPLY {value/(10**tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash = self.mint(value, token, account, new_w3)
            if tx_hash and tx_hash != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал SUPPLY ({value/(10**tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash
        # elif need_borrow:
        #     borrow_value = random.randint(int(tokens[tokens[token]['repay_token']]['max_borrow']*0.5), int(tokens[tokens[token]['repay_token']]['max_borrow']*0.95))
        #     self.logger.log(f"{self.project} | Делаю BORROW {borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}", wallet=account.address)
        #     tx_hash = self.borrow(borrow_value, tokens[token]['repay_token'], account)
        #     if tx_hash and tx_hash != 'low_native':
        #         self.logger.log_success(f"{self.project} | Сделал BORROW ({borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}) успешно!", wallet=account.address)
        #     return tx_hash
        elif need_redeem:
            if tokens[token]['protocol_supplied'] == 0:
                return True
            # balance = self.w3.eth.get_balance(account.address) if tokens[token]['repay_token'] == 'ETH' else get_balance(self.w3, account, tokens_data['USDC']['address'])
            # borrowed_value = min(balance, tokens[tokens[token]['repay_token']]['actual_borrowed'])
            #
            # if borrowed_value == 0 and tokens[tokens[token]['repay_token']]['actual_borrowed'] > balance:
            #     return f'swap_{tokens[token]["repay_token"]}_{tokens[tokens[token]["repay_token"]]["actual_borrowed"]-balance}'
            # if borrowed_value > (1000 if tokens[token]['repay_token'] == 'USDC' else 10**12):
            #     self.logger.log(f"{self.project} | Делаю REPAY {borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}",wallet=account.address)
            #     tx_hash = self.repay(borrowed_value, tokens[token]['repay_token'], account)
            #     if tx_hash and tx_hash != 'low_native':
            #         self.logger.log_success(f"{self.project} | Сделал REPAY ({borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])}) успешно!", wallet=account.address)
            #     time.sleep(random.uniform(3, 5))
            #if (tokens[token]['supplied'] > 10**12 if token == 'ETH' else 1000) and tokens[token]['supplied'] != 0:
            self.logger.log(f"{self.project} | Делаю WITHDRAW {tokens[token]['actual_supplied'] / (10 ** tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash_ = self.redeem(tokens[token]['protocol_supplied'], token, account, new_w3)
            if tx_hash_ and tx_hash_ != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash_)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал WITHDRAW ({tokens[token]['actual_supplied'] / (10 ** tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash_

class Sonnie():
    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'SONNIE'
        self.logger = logger
        self.eth_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['ETH']), abi=lending_data[self.project]['ABI']['ETH'])
        self.usdc_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['USDBC']), abi=lending_data[self.project]['ABI']['USDBC'])
        self.markets_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['MARKETS']),abi=lending_data[self.project]['ABI']['MARKETS'])

    def check_markets(self, account, new_w3):
        addresses = self.markets_contract.functions.getAllMarkets().call()
        for address_ in addresses:
            if not self.markets_contract.functions.checkMembership(account.address, new_w3.to_checksum_address(address_)).call():
                func_ = getattr(self.markets_contract.functions, 'enterMarkets')
                tx = make_tx(new_w3, account, func=func_, args=addresses, args_positioning=False)
                if tx == "low_native" or not tx:
                    return tx
                sign = account.sign_transaction(tx)
                hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
                return new_w3.to_hex(hash)
        return

    def redeem(self, value, token, account, new_w3):
        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'redeem')
        tx = make_tx(new_w3, account, value=0, func=func_, args=value, args_positioning=False)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def mint(self, value, token, account, new_w3):

        allowance = check_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])
        if not allowance:
            make_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])

        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'mint')

        tx = make_tx(new_w3, account, value=0, func=func_, args=value, args_positioning=False)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def main(self, private_key, token, value, withdraw = False, attempt = 0):

        value = int(value * 10 ** 18) if token == 'ETH' else int(value * 10 ** 6)
        ETH_PRICE = float(self.help.get_prices()['ETH'])

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        if token == 'USDBC':
            value = min(value, get_balance(new_w3, account, '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'))
        if token == 'ETH':
            if get_balance(new_w3, account, '0x4200000000000000000000000000000000000006') < value:
                wrap = eth_wrapper(value, 'WETH', new_w3, private_key['private_key'], in_decimals=False)

        snapshot_eth = self.eth_contract.functions.getAccountSnapshot(account.address).call()
        snapshot_usdc = self.usdc_contract.functions.getAccountSnapshot(account.address).call()
        _, balance, borrow_balance, rate = snapshot_eth
        _, balance_, borrow_balance_, rate_ = snapshot_usdc

        tokens = {}
        tokens['ETH'] = {"actual_supplied": int(balance * rate / (10 ** 18)), "protocol_supplied": balance, "actual_borrowed": borrow_balance, "protocol_borrower": borrow_balance, "repay_token": "USDC",'decimals': 18}
        tokens['USDBC'] = {"actual_supplied": int(balance_ * rate_ / (10 ** 18)), "protocol_supplied": balance_, "actual_borrowed": borrow_balance_, "protocol_borrower": borrow_balance_,"repay_token": "ETH", 'decimals': 6}

        if withdraw and (tokens['ETH']['actual_supplied'] < 10**12 and tokens['USDBC']['actual_supplied'] < 10000 and tokens['ETH']['actual_borrowed'] < 10**12 and tokens['USDBC']['actual_borrowed'] < 1000):
            return 'good'

        need_borrow, need_supply, need_redeem = False, False, False
        # if (tokens['ETH']['supplied'] > 10 ** 16 or tokens['USDC']['supplied'] > 10000000) and (tokens['ETH']['borrowed'] < 10 ** 12 and tokens['USDC']['borrowed'] < 10000):
        #     need_borrow = True
        if 0.01 < tokens[token]['actual_supplied'] / (10 ** tokens[token]['decimals']) * ETH_PRICE:
            need_redeem = True
        else:
            need_supply = True
        if withdraw:
            need_borrow, need_supply, need_redeem = False, False, True

        if need_supply:
            self.logger.log(f"{self.project} | Делаю SUPPLY {value/(10**tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash = self.mint(value, token, account, new_w3)
            if tx_hash and tx_hash != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал SUPPLY ({value/(10**tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash
        # elif need_borrow:
        #     borrow_value = random.randint(int(tokens[tokens[token]['repay_token']]['max_borrow']*0.5), int(tokens[tokens[token]['repay_token']]['max_borrow']*0.95))
        #     self.logger.log(f"{self.project} | Делаю BORROW {borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}", wallet=account.address)
        #     tx_hash = self.borrow(borrow_value, tokens[token]['repay_token'], account)
        #     if tx_hash and tx_hash != 'low_native':
        #         self.logger.log_success(f"{self.project} | Сделал BORROW ({borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}) успешно!", wallet=account.address)
        #     return tx_hash
        elif need_redeem:
            if tokens[token]['protocol_supplied'] == 0:
                return True
            # balance = self.w3.eth.get_balance(account.address) if tokens[token]['repay_token'] == 'ETH' else get_balance(self.w3, account, tokens_data['USDC']['address'])
            # borrowed_value = min(balance, tokens[tokens[token]['repay_token']]['actual_borrowed'])
            #
            # if borrowed_value == 0 and tokens[tokens[token]['repay_token']]['actual_borrowed'] > balance:
            #     return f'swap_{tokens[token]["repay_token"]}_{tokens[tokens[token]["repay_token"]]["actual_borrowed"]-balance}'
            # if borrowed_value > (1000 if tokens[token]['repay_token'] == 'USDC' else 10**12):
            #     self.logger.log(f"{self.project} | Делаю REPAY {borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}",wallet=account.address)
            #     tx_hash = self.repay(borrowed_value, tokens[token]['repay_token'], account)
            #     if tx_hash and tx_hash != 'low_native':
            #         self.logger.log_success(f"{self.project} | Сделал REPAY ({borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])}) успешно!", wallet=account.address)
            #     time.sleep(random.uniform(3, 5))
            #if (tokens[token]['supplied'] > 10**12 if token == 'ETH' else 1000) and tokens[token]['supplied'] != 0:
            self.logger.log(f"{self.project} | Делаю WITHDRAW {tokens[token]['actual_supplied'] / (10 ** tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash_ = self.redeem(tokens[token]['protocol_supplied'], token, account, new_w3)
            if tx_hash_ and tx_hash_ != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash_)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал WITHDRAW ({tokens[token]['actual_supplied'] / (10 ** tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash_

class Aave():
    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'AAVE'
        self.logger = logger
        self.eth_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['ETH']), abi=lending_data[self.project]['ABI']['ETH'])
        self.usdc_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['USDBC']), abi=lending_data[self.project]['ABI']['USDBC'])
        self.contract_data = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['DATA']), abi=lending_data[self.project]['ABI']['DATA'])

    def redeem(self, value, token, account, new_w3):
        if token == "ETH":
            allowance = check_approve(new_w3, account, '0xd4a0e0b9149bcee3c920d2e00b5de09138fd8bb7', lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, '0xd4a0e0b9149bcee3c920d2e00b5de09138fd8bb7', lending_data[self.project]['contracts'][token])
        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'withdraw' if token == 'USDBC' else 'withdrawETH')
        args = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', 115792089237316195423570985008687907853269984665640564039457584007913129639935, account.address] if token == 'USDBC' else ['0xB702cE183b4E1Faa574834715E5D4a6378D0eEd3', 115792089237316195423570985008687907853269984665640564039457584007913129639935, account.address]
        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def mint(self, value, token, account, new_w3):
        if token == "USDBC":
            allowance = check_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])

        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'depositETH' if token == 'ETH' else 'deposit')
        args = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', value, account.address, 0] if token == 'USDBC' else ['0xB702cE183b4E1Faa574834715E5D4a6378D0eEd3', account.address, 0]
        tx = make_tx(new_w3, account, value=0 if token == 'USDBC' else value, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def main(self, private_key, token, value, withdraw = False, attempt = 0):

        value = int(value * 10 ** 18) if token == 'ETH' else int(value * 10 ** 6)
        ETH_PRICE = float(self.help.get_prices()['ETH'])

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        if token == 'USDBC':
            value = min(value, get_balance(new_w3, account, '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'))

        snapshot_eth = self.contract_data.functions.getUserReserveData('0x4200000000000000000000000000000000000006', account.address).call()
        snapshot_usdc = self.contract_data.functions.getUserReserveData('0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', account.address).call()
        supplied, c_stable_debt, c_variable_debt, p_stable_debt, s_variable_debt, s_borrow_rate, l_rate, stabe_rate_last, use_as_col = snapshot_eth
        supplied_, c_stable_debt_, c_variable_debt_, p_stable_debt_, s_variable_debt_, s_borrow_rate_, l_rate_, stabe_rate_last_, use_as_col_ = snapshot_usdc

        tokens = {}
        tokens['ETH'] = {"supplied": supplied, "borrowed": c_variable_debt, "repay_token": "USDC", 'decimals': 18}
        tokens['USDBC'] = {"supplied": supplied_, "borrowed": c_variable_debt_, "repay_token": "ETH", 'decimals': 6}

        if withdraw and (tokens['ETH']['supplied'] < 10**12 and tokens['USDBC']['supplied'] < 10000 and tokens['ETH']['borrowed'] < 10**12 and tokens['USDBC']['borrowed'] < 1000):
            return 'good'

        need_borrow, need_supply, need_redeem = False, False, False
        # if (tokens['ETH']['supplied'] > 10 ** 16 or tokens['USDC']['supplied'] > 10000000) and (tokens['ETH']['borrowed'] < 10 ** 12 and tokens['USDC']['borrowed'] < 10000):
        #     need_borrow = True
        if 0.01 < tokens[token]['supplied'] / (10 ** tokens[token]['decimals']) * ETH_PRICE:
            need_redeem = True
        else:
            need_supply = True
        if withdraw:
            need_borrow, need_supply, need_redeem = False, False, True

        if need_supply:
            self.logger.log(f"{self.project} | Делаю SUPPLY {value/(10**tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash = self.mint(value, token, account, new_w3)
            if tx_hash and tx_hash != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал SUPPLY ({value/(10**tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash
        # elif need_borrow:
        #     borrow_value = random.randint(int(tokens[tokens[token]['repay_token']]['max_borrow']*0.5), int(tokens[tokens[token]['repay_token']]['max_borrow']*0.95))
        #     self.logger.log(f"{self.project} | Делаю BORROW {borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}", wallet=account.address)
        #     tx_hash = self.borrow(borrow_value, tokens[token]['repay_token'], account)
        #     if tx_hash and tx_hash != 'low_native':
        #         self.logger.log_success(f"{self.project} | Сделал BORROW ({borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}) успешно!", wallet=account.address)
        #     return tx_hash
        elif need_redeem:
            if tokens[token]['supplied'] == 0:
                return True
            # balance = self.w3.eth.get_balance(account.address) if tokens[token]['repay_token'] == 'ETH' else get_balance(self.w3, account, tokens_data['USDC']['address'])
            # borrowed_value = min(balance, tokens[tokens[token]['repay_token']]['actual_borrowed'])
            #
            # if borrowed_value == 0 and tokens[tokens[token]['repay_token']]['actual_borrowed'] > balance:
            #     return f'swap_{tokens[token]["repay_token"]}_{tokens[tokens[token]["repay_token"]]["actual_borrowed"]-balance}'
            # if borrowed_value > (1000 if tokens[token]['repay_token'] == 'USDC' else 10**12):
            #     self.logger.log(f"{self.project} | Делаю REPAY {borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}",wallet=account.address)
            #     tx_hash = self.repay(borrowed_value, tokens[token]['repay_token'], account)
            #     if tx_hash and tx_hash != 'low_native':
            #         self.logger.log_success(f"{self.project} | Сделал REPAY ({borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])}) успешно!", wallet=account.address)
            #     time.sleep(random.uniform(3, 5))
            #if (tokens[token]['supplied'] > 10**12 if token == 'ETH' else 1000) and tokens[token]['supplied'] != 0:
            self.logger.log(f"{self.project} | Делаю WITHDRAW {tokens[token]['supplied'] / (10 ** tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash_ = self.redeem(tokens[token]['supplied'], token, account, new_w3)
            if tx_hash_ and tx_hash_ != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash_)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал WITHDRAW ({tokens[token]['supplied'] / (10 ** tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash_

class Seamless():
    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'SEAMLESS'
        self.logger = logger
        self.eth_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['ETH']), abi=lending_data[self.project]['ABI']['ETH'])
        self.usdc_contract = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['USDBC']), abi=lending_data[self.project]['ABI']['USDBC'])
        self.contract_data = w3.eth.contract(address=w3.to_checksum_address(lending_data[self.project]['contracts']['DATA']), abi=lending_data[self.project]['ABI']['DATA'])

    def redeem(self, value, token, account, new_w3):
        if token == "ETH":
            allowance = check_approve(new_w3, account, '0x48bf8fcd44e2977c8a9a744658431a8e6c0d866c', lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, '0x48bf8fcd44e2977c8a9a744658431a8e6c0d866c', lending_data[self.project]['contracts'][token])
        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'withdraw' if token == 'USDBC' else 'withdrawETH')
        args = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', 115792089237316195423570985008687907853269984665640564039457584007913129639935, account.address] if token == 'USDBC' else ['0x8F44Fd754285aa6A2b8B9B97739B79746e0475a7', 115792089237316195423570985008687907853269984665640564039457584007913129639935, account.address]
        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def mint(self, value, token, account, new_w3):
        if token == "USDBC":
            allowance = check_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])
            if not allowance:
                make_approve(new_w3, account, tokens_data[token]['address'], lending_data[self.project]['contracts'][token])

        func_ = getattr(self.eth_contract.functions if token == 'ETH' else self.usdc_contract.functions, 'depositETH' if token == 'ETH' else 'supply')
        args = ['0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', value, account.address, 0] if token == 'USDBC' else ['0xB702cE183b4E1Faa574834715E5D4a6378D0eEd3', account.address, 0]
        tx = make_tx(new_w3, account, value=0 if token == 'USDBC' else value, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        return new_w3.to_hex(hash)

    def main(self, private_key, token, value, withdraw = False, attempt = 0):

        value = int(value * 10 ** 18) if token == 'ETH' else int(value * 10 ** 6)
        ETH_PRICE = float(self.help.get_prices()['ETH'])

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        if token == 'USDBC':
            value = min(value, get_balance(new_w3, account, '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA'))

        snapshot_eth = self.contract_data.functions.getUserReserveData('0x4200000000000000000000000000000000000006', account.address).call()
        snapshot_usdc = self.contract_data.functions.getUserReserveData('0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA', account.address).call()
        supplied, c_stable_debt, c_variable_debt, p_stable_debt, s_variable_debt, s_borrow_rate, l_rate, stabe_rate_last, use_as_col = snapshot_eth
        supplied_, c_stable_debt_, c_variable_debt_, p_stable_debt_, s_variable_debt_, s_borrow_rate_, l_rate_, stabe_rate_last_, use_as_col_ = snapshot_usdc

        tokens = {}
        tokens['ETH'] = {"supplied": supplied, "borrowed": c_variable_debt, "repay_token": "USDC", 'decimals': 18}
        tokens['USDBC'] = {"supplied": supplied_, "borrowed": c_variable_debt_, "repay_token": "ETH", 'decimals': 6}

        if withdraw and (tokens['ETH']['supplied'] < 10**12 and tokens['USDBC']['supplied'] < 10000 and tokens['ETH']['borrowed'] < 10**12and tokens['USDBC']['borrowed'] < 1000):
            return 'good'

        need_borrow, need_supply, need_redeem = False, False, False
        # if (tokens['ETH']['supplied'] > 10 ** 16 or tokens['USDC']['supplied'] > 10000000) and (tokens['ETH']['borrowed'] < 10 ** 12 and tokens['USDC']['borrowed'] < 10000):
        #     need_borrow = True
        if 0.01 < tokens[token]['supplied'] / (10 ** tokens[token]['decimals']) * ETH_PRICE:
            need_redeem = True
        else:
            need_supply = True
        if withdraw:
            need_borrow, need_supply, need_redeem = False, False, True

        if need_supply:
            self.logger.log(f"{self.project} | Делаю SUPPLY {value/(10**tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash = self.mint(value, token, account, new_w3)
            if tx_hash and tx_hash != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал SUPPLY ({value/(10**tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash
        # elif need_borrow:
        #     borrow_value = random.randint(int(tokens[tokens[token]['repay_token']]['max_borrow']*0.5), int(tokens[tokens[token]['repay_token']]['max_borrow']*0.95))
        #     self.logger.log(f"{self.project} | Делаю BORROW {borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}", wallet=account.address)
        #     tx_hash = self.borrow(borrow_value, tokens[token]['repay_token'], account)
        #     if tx_hash and tx_hash != 'low_native':
        #         self.logger.log_success(f"{self.project} | Сделал BORROW ({borrow_value/(10**tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}) успешно!", wallet=account.address)
        #     return tx_hash
        elif need_redeem:
            if tokens[token]['supplied'] == 0:
                return True
            # balance = self.w3.eth.get_balance(account.address) if tokens[token]['repay_token'] == 'ETH' else get_balance(self.w3, account, tokens_data['USDC']['address'])
            # borrowed_value = min(balance, tokens[tokens[token]['repay_token']]['actual_borrowed'])
            #
            # if borrowed_value == 0 and tokens[tokens[token]['repay_token']]['actual_borrowed'] > balance:
            #     return f'swap_{tokens[token]["repay_token"]}_{tokens[tokens[token]["repay_token"]]["actual_borrowed"]-balance}'
            # if borrowed_value > (1000 if tokens[token]['repay_token'] == 'USDC' else 10**12):
            #     self.logger.log(f"{self.project} | Делаю REPAY {borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])} {tokens[token]['repay_token']}",wallet=account.address)
            #     tx_hash = self.repay(borrowed_value, tokens[token]['repay_token'], account)
            #     if tx_hash and tx_hash != 'low_native':
            #         self.logger.log_success(f"{self.project} | Сделал REPAY ({borrowed_value / (10 ** tokens[tokens[token]['repay_token']]['decimals'])}) успешно!", wallet=account.address)
            #     time.sleep(random.uniform(3, 5))
            #if (tokens[token]['supplied'] > 10**12 if token == 'ETH' else 1000) and tokens[token]['supplied'] != 0:
            self.logger.log(f"{self.project} | Делаю WITHDRAW {tokens[token]['supplied'] / (10 ** tokens[token]['decimals'])} {token}", wallet=account.address)
            tx_hash_ = self.redeem(tokens[token]['supplied'], token, account, new_w3)
            if tx_hash_ and tx_hash_ != 'low_native':
                tx_status = check_for_status(new_w3, tx_hash_)
                if not tx_status:
                    return self.main(private_key=private_key, token=token, value=value, withdraw=withdraw, attempt=attempt + 1)
                self.logger.log_success(f"{self.project} | Сделал WITHDRAW ({tokens[token]['supplied'] / (10 ** tokens[token]['decimals'])} {token}) успешно!", wallet=account.address)
            return tx_hash_

def initialize_lendings(classes_to_init, w3, logger, helper):
    available_swaps = {
        "Granary": Granary,
        "Moonwell": Moonwell,
        "Sonnie": Sonnie,
        "Aave": Aave,
        "Seamless": Seamless,
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, logger, helper)

    return initialized_objects

