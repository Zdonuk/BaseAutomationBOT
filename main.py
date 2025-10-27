from modules import lendings, swaps, name_services, nft_markets, liquidity, bridges, derivatives, other
from helpers.utils import eth_wrapper, wait_for_balance_change, make_tx, send_tx, check_for_status
from helpers.data import tokens_data, error_codes
from helpers.logger import Logger
from helpers.help import helper
import concurrent.futures
from settings import *
from web3 import Web3
import random
import time

class base_module():

    def __init__(self, data, w3, logger, debug=False):
        self.helper = helper(print_out=debug)
        self.w3 = dict(w3)
        self.chain = random.choice(list(self.w3.keys()))
        self.logger = logger
        self.swaps = swaps
        self.choosed_swaps = data['swaps']
        self.lendings = lendings
        self.choosed_liqs = data['liqs']
        self.liquidity = liquidity
        self.choosed_lendings = data['lendings']
        self.nft_markets = nft_markets
        self.choosed_nft_markets = data['nft_markets']
        self.name_services = name_services
        self.choosed_name_services = data['name_services']
        self.bridges = bridges
        self.choosed_bridges = data['bridges']
        self.derives = derivatives
        self.choosed_derives = data['derives']
        self.other = other
        self.choosed_other = data['misc']
        self.settings = data['settings']
        self.settings['debug'] = debug

        self.swaps_ = self.swaps.initialize_swaps(self.choosed_swaps, self.w3['BASE'], self.settings['max_slippage']*1.05, self.helper)
        self.liqs_ = self.liquidity.initialize_liquidity(self.choosed_liqs, self.w3['BASE'], self.helper)
        self.lendings_ = self.lendings.initialize_lendings(self.choosed_lendings, self.w3['BASE'], self.logger, self.helper)
        self.nft_markets_ = self.nft_markets.initialize_nft_markets(self.choosed_nft_markets, self.w3['BASE'], self.logger, self.helper)
        self.name_services_ = self.name_services.initialize_name_services(self.choosed_name_services, self.w3['BASE'], self.logger, self.settings, self.helper)
        self.bridges_ = self.bridges.initialize_bridges(self.choosed_bridges, self.w3, self.logger, self.helper, self.settings['max_bridge_slippage'])
        self.derives_ = self.derives.initialize_derives(self.choosed_derives, self.w3['BASE'], self.logger, self.helper)
        self.other_ = self.other.initialize_misc(self.choosed_other, self.w3['BASE'], self.logger, self.helper)

        if self.settings['okx']:
            self.okx = OKEX(self.settings, self.logger, self.helper)
        if self.settings['warmup']:
            self.warmup = Warmup(self.w3, self.logger, self.helper)

        self.prices = self.helper.get_prices_combined()

        self.last_gas_printed = 0
        self.last_price_check = int(time.time())
        self.liqs_added = {}

    def check_gas(self, attempt = 0):
        try:
            gas = self.w3['ETH'].from_wei(self.w3['ETH'].eth.gas_price, 'gwei')
            if gas > self.settings["max_gwei"]:
                if int(time.time()) - self.last_gas_printed > 150:
                    self.last_gas_printed = int(time.time())
                    self.logger.log_warning(f"Текущий газ ({int(gas)}) больше указанного в настройках ({self.settings['max_gwei']}), жду...")
                time.sleep(random.uniform(30, 60))
                return self.check_gas(attempt = attempt + 1)
            else:
                self.last_gas_printed = 0
                if attempt >= 2:
                    time.sleep(random.uniform(self.settings['min_after_gas_delay'], self.settings['max_after_gas_delay'])) #ЧТОБЫ НЕ ОДНОВРЕМЕННО ВЫХОДИЛИ
                    return self.check_gas(attempt=0) # СНОВА ПРОВЕРЯЕМ ГАЗ, ВДРУГ ИЗМЕНИЛСЯ, НО С ATTEMPT=0, Т.Е. БЕЗ ЗАДЕРЖКИ
                return True
        except:
            time.sleep(random.uniform(5, 10))
            return self.check_gas(attempt = attempt + 1)

    def process_wallet(self, wallet_data):

        start_delay = random.uniform(0, self.settings['max_start_delay'])
        self.logger.log(f"Жду {round(start_delay, 2)} секунд перед стартом пути...", wallet_data['address'])
        time.sleep(start_delay)
        wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])

        for index, action in enumerate(wallet_data['route']):
            action_ = action['action']

            self.check_gas()

            # if action_ != 'NFT MARKET':
            #     continue

            if int(time.time()) - self.last_price_check > 300:
                self.last_price_check = int(time.time())
                self.prices = self.helper.get_prices_combined()

            self.logger.log(f"Начинаю действие {action_}...", wallet_data['address'])

            if action_ == "SWAP" and len(self.swaps_) != 0:
                random_swap_name = random.choice(list(self.swaps_.keys()))
                swap_instance = self.swaps_[random_swap_name]
                res = self.process_swap(swap_instance, wallet_data)

            elif action_ == "LIQUDITY" and len(self.liqs_) != 0:
                random_liq_name = random.choice(list(self.liqs_.keys()))
                liq_instance = self.liqs_[random_liq_name]
                res = self.process_liq(liq_instance, wallet_data)

            elif action_ == 'LENDING' and len(self.lendings_) != 0:
                random_lendings_name = random.choice(list(self.lendings_.keys()))
                lending_instance = self.lendings_[random_lendings_name]
                res = self.process_lending(lending_instance, wallet_data)

            elif action_ == 'NFT MARKET' and len(self.nft_markets_) != 0:
                random_nft_narket_name = random.choice(list(self.nft_markets_.keys()))
                nft_market_instance = self.nft_markets_[random_nft_narket_name]
                res = self.process_nft_market(nft_market_instance, wallet_data)

            elif action_ == 'NAMESERVICE' and len(self.name_services_) != 0:
                random_nft_name = random.choice(list(self.name_services_.keys()))
                name_instance = self.name_services_[random_nft_name]
                res = self.process_name_service(name_instance, wallet_data)

            elif action_ == 'DERIVATIVE' and len(self.derives_) != 0:
                random_deriv_name = random.choice(list(self.derives_.keys()))
                deriv_instance = self.derives_[random_deriv_name]
                res = self.process_deriv(deriv_instance, wallet_data)

            elif action_ == 'OTHER' and len(self.other_) != 0:
                random_misc_name = random.choice(list(self.other_.keys()))
                misc_instance = self.other_[random_misc_name]
                res = self.process_misc(misc_instance, wallet_data)

            elif action_ == 'BRIDGE IN':
                random_bridge_name = random.choice(list(self.bridges_.keys()))
                bridge_instance = self.bridges_[random_bridge_name]
                res = self.process_bridge(bridge_instance, wallet_data, bridge_type='IN')
                if not res and index == 0:
                    self.logger.log_error(f"Закончил работу с адресом, т.к. первое действие BRIDGE - неудачно")
                    return False

            elif action_ == 'OKX WITHDRAW':
                res = self.process_okx_withdraw(action)

            elif action_ == 'OKX DEPOSIT':
                self.process_end_actions(wallet_data)
                res = self.process_okx_deposit(wallet_data)

            else:
                res = False

            if res:
                action['status'] = 1

            if index != len(wallet_data['route'])-1:
                sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
                if action_ in ['BRIDGE IN']:
                    sleep_time += random.uniform(self.settings['min_after_bridge_delay'], self.settings['max_after_bridge_delay'])
                self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
                time.sleep(sleep_time)
                wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])
                self.process_wrap(wallet_data)

        if not self.settings['okx']:
            self.process_end_actions(wallet_data)

        self.wallet_to_procced = self.wallet_to_procced - 1

        self.logger.log_success(f'Закончил работу по сгенерированному пути, осталось кошельков в работе: {self.wallet_to_procced}', wallet_data['address'])
        return True

    def process_end_actions(self, wallet_data):
        self.process_wrap(wallet_data, end=True)

        if self.settings['remove_liq_after']:
            self.logger.log('Начинаю убирать ликвидность...', wallet_data['address'])
            self.process_liq_withdraw(wallet_data) #TODO СДЕЛАТЬ ОТДЕЛЬНУЮ ФУНКЦИЮ (done)
            sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
            self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
            time.sleep(sleep_time)
            wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])

        if self.settings['swap_out_after']:
            self.logger.log('Начинаю перевод баланса в ETH...', wallet_data['address'])
            self.process_swap(None, wallet_data, swap_out=True, ignore='none')
            sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
            self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
            time.sleep(sleep_time)

        if self.settings['close_deriv_positions']:
            self.logger.log('Начинаю закрывать позиции на деривативах...', wallet_data['address'])
            self.process_deriv(None, wallet_data, close_all=True)
            sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
            self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
            time.sleep(sleep_time)
            wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])

        if self.settings['remove_lendings_afrer']:
            self.logger.log('Начинаю убирать ликвидность из лендингов...', wallet_data['address'])
            self.process_lending_withdraw(wallet_data=wallet_data)
            sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
            self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
            time.sleep(sleep_time)
            wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])
            self.process_swap(None, wallet_data, swap_out=True)

        time.sleep(3)
        wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])
        self.process_wrap(wallet_data, end=True)
        sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
        self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
        time.sleep(sleep_time)

    def process_warmup(self, wallet_data, type, chain, proceed=False):
        if proceed:
            return True
        if not self.settings['warmup']:
            return
        if (type == 'IN' and not self.settings['warmup_before_dep']) or (type == 'OUT' and not self.settings['warmup_before_withdraw']):
            return
        for i in range(self.settings['min_warmup_tx'], self.settings['max_warmup_tx']):
            for i in range(max(3, int(self.settings['attempts']))):
                try:
                    res = self.warmup.main(chain, wallet_data)
                    if res and res not in error_codes:
                        sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
                        time.sleep(sleep_time)
                        break
                except:
                    time.sleep(random.uniform(5, 10))
        return True

    def process_wrap(self, wallet_data, end=False):
        tokens = wallet_data['tokens']
        value = tokens.get('ETH', {}).get('balance', 0) if not end else 10**14
        if tokens.get('WETH', {}).get('balance', 0) > value:
            self.logger.log(f"Делаю WRAP из WETH ({round(wallet_data['tokens']['WETH']['balance'] / (10 ** 18), 5)}) в ETH...", wallet_data['address'])

            try:
                if wallet_data.get('proxy', None):
                    new_w3 = self.helper.get_web3(wallet_data['proxy'], self.w3['BASE'])
                else:
                    raise Exception
            except Exception:
                new_w3 = self.w3['BASE']

            res = eth_wrapper(tokens['WETH']['balance'], 'ETH', new_w3, wallet_data['private_key'], in_decimals=False)
            if res and res not in error_codes:
                self.logger.log_success(f"Успешно сделал WRAP из WETH ({round(wallet_data['tokens']['WETH']['balance'] / (10 ** 18), 5)}) в ETH", wallet_data['address'])
                sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
                self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
                time.sleep(sleep_time)
            else:
                self.logger.log_error('Ошибка во время WRAP, пропускаю...', wallet_data['address'])

    def decide_okx_withdraw(self, wallet):
        while True:
            try:
                wallet_data = self.wallets_with_path[wallet]
                if wallet_data['tokens'].get('ETH', {}).get('balance', 0) >= (self.settings['min_eth_balance']*10**18):
                    return True, wallet_data['address'], 0, 0
                native_balances = {chain: w3_.eth.get_balance(w3_.to_checksum_address(wallet_data['address'])) / (10 ** 18) for chain, w3_ in self.w3.items() if chain not in self.settings['black_chains'] and chain != 'BASE'}
                filtered_balances = [chain for chain, balance in native_balances.items() if self.settings['to_base_min'] <= balance and chain not in self.settings['black_chains']]
                if not filtered_balances:
                    chains = [chain for chain, data in self.okx.data.items() if chain not in self.settings['black_chains'] and chain not in ['BASE']]
                    random_chain = random.choice(chains)
                    res, address = self.okx.is_wl(wallet_data['address'], self.okx.data[random_chain]['id'], self.okx.data[random_chain]['sub_id'])
                    self.wallets_with_path[wallet_data['address']]['sub_id'] = self.okx.data[random_chain]['sub_id']
                    self.wallets_with_path[wallet_data['address']]['route'].insert(0, {'action': 'OKX WITHDRAW', 'status': 0, 'value': random.uniform(self.settings['to_base_min'], self.settings['to_base_max']), "address": wallet_data['address'], "id": self.okx.data[random_chain]['id'], 'sub_id': self.okx.data[random_chain]['sub_id']})
                    return res, wallet_data['address'], self.okx.data[random_chain]['id'], self.okx.data[random_chain]['sub_id']
                else:
                    return True, wallet_data['address'], 0, 0
            except:
                time.sleep(random.uniform(1, 5))

    def okx_add_to_wl(self):

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(50, len(self.wallets_with_path))) as executor:
            futures = list(executor.map(self.decide_okx_withdraw, self.wallets_with_path.keys()))

        results = [future for future in futures]
        for res, address, id, sub_id in results:
            for i in self.wallets_with_path.values():
                if i["address"].lower() == address.lower():
                    i["status"] = res
                    i['id'] = id
                    i['sub_id'] = sub_id
                    if res == "bad_auth":
                        #logger.log_error("AUTH CODE IS NOT VALID. STOPPED")
                        return

        false_wallets = [w for w in self.wallets_with_path.values() if w.get("status", False) == False]
        self.logger.log(f"{len(false_wallets)}/{len(self.wallets_with_path.values())} адресов нужно добавить в WL")

        wallets_by_code = {}
        for w in false_wallets:
            if w["sub_id"] not in wallets_by_code:
                wallets_by_code[w["sub_id"]] = []
            wallets_by_code[w["sub_id"]].append(w)

        # РАЗДЕЛЕНИЕ НА ЧАНКИ ПО 20
        for code in wallets_by_code:
            wallets_by_code[code] = list(chunks(wallets_by_code[code], 20))

        for code, wallets_groups in wallets_by_code.items():
            for wallets_group in wallets_groups:

                self.logger.log(f"Добавляю {len(wallets_group)} адресов в WL...")

                while True:
                    try:
                        add = self.okx.okx_add_wl_batch([w["address"] for w in wallets_group], sub_id=code, id=2)
                    except Exception as e:
                        print(e)
                        continue
                    if add == "no_mail_code" or add == "wrong_mail_code" or add == "mail_code_expired":
                        #logger.log_error(f"Error '{add}' while adding {len(wallets_group)} wallets to WL, waiting 5 minutes")
                        time.sleep(300)
                    elif add == "bad_auth":
                        #logger.log_error("AUTH CODE IS NOT VALID. STOPPED")
                        return
                    elif add == "wrong_address":
                        #logger.log_error("CHOOSED NON-EVM CHAIN. NON-EVM CHAIN CURRENTLY ARE NOT SUPPORED!")
                        return
                    elif add is True:
                        self.logger.log_success(f"Успешно добавил {len(wallets_group)} адресов в WL!")
                        time.sleep(random.uniform(35, 45))
                        break
                    else:
                        if self.settings['debug']:
                            print(f"RES ADD WL: {add}")
                        pass
        # with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        #     futures = list(executor.map(lambda i: self.okx.is_wl(i["address"], i['id'], i['sub_id']), wallets_with_path.values()))
        #
        # results = [future.result() for future in futures]
        # for res, address in results:
        #     for i in wallets_with_path.values():
        #         if i["address"].lower() == address.lower():
        #             i["status"] = res
        #             if res == "bad_auth":
        #                 logger.log_error("AUTH CODE IS NOT VALID. STOPPED")
        #                 break

        return True

    def process_okx_withdraw(self, action):
        while True:
            if self.okx.busy:
                time.sleep(random.uniform(10, 30))
                continue
            else:
                self.okx.busy = True
                try:
                    withdraw, fee = self.okx.withdraw(action)
                    if withdraw:
                        chain = next((chain for chain, data in self.okx.data.items() if data['sub_id'] == action['sub_id']), None)
                        self.okx.busy = False
                        self.logger.log_success(f"OKX | Успешно сделал вывод в сеть {chain}, жду получения...", action['address'])
                        balance_change = wait_for_balance_change(self.w3[chain], action['address'], self.w3[chain].eth.get_balance(action['address']))
                        self.logger.log_success(f"OKX | Успешно получил баланс ({round(balance_change, 6)} ETH) в сети {chain}", action['address'])
                        return True
                    self.okx.busy = False
                    time.sleep(random.uniform(20, 40))
                except:
                    self.okx.busy = False

    def process_okx_deposit(self, wallet_data):
        random_bridge = random.choice(list(self.bridges_.keys()))
        bridge_instanse = self.bridges_[random_bridge]
        self.check_gas()
        wallet_data['tokens'] = self.helper.get_user_tokens(wallet_data['address'])
        res = self.process_bridge(bridge_instanse, wallet_data, bridge_type='OUT')
        sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
        sleep_time += random.uniform(self.settings['min_after_bridge_delay'], self.settings['max_after_bridge_delay'])
        self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
        time.sleep(sleep_time)
        self.check_gas()
        self.process_warmup(wallet_data, 'OUT', res)
        sleep_time = random.uniform(self.settings["min_sleep"], self.settings["max_sleep"])
        self.logger.log(f"Жду {round(sleep_time, 2)} секунд перед следующим действием...", wallet=wallet_data['address'])
        time.sleep(sleep_time)
        while True:
            wallet_to = self.okx.get_deposit_address()
            if wallet_to:
                break
            else:
                time.sleep(random.uniform(30, 60))
        account = self.w3['ETH'].eth.account.from_key(wallet_data['private_key'])

        try:
            if wallet_data.get('proxy', None):
                new_w3 = self.helper.get_web3(wallet_data['proxy'], self.w3[res])
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3[res]

        while True:
            try:
                value = new_w3.eth.get_balance(account.address)
                break
            except Exception as e:
                pass
        while True:
            tx = make_tx(new_w3, account, to=new_w3.to_checksum_address(wallet_to), value=value, minus_fee=True)
            hash, new_value = send_tx(new_w3, account, tx)
            if not hash:
                value = new_value
                continue
            tx_status = check_for_status(new_w3, hash)
            if tx_status:
                break

        # sign = account.sign_transaction(tx)
        # hash = self.w3[res].eth.send_raw_transaction(sign.rawTransaction)

        self.logger.log_success(f'Успешно отправил на OKX из сети {res}, жду поступления...', wallet_data['address'])
        got_dep = False
        while True:
            deposit, confirmed = self.okx.check_deposit_status(wallet_to, self.okx.wallets[wallet_to]['token'])
            if deposit is True:
                if not got_dep:
                    self.logger.log(f"Задетектил депозит, жду подтверждений...", wallet_data['address'])
                    got_dep = True
                if confirmed == 2:
                    self.okx.wallets[wallet_to]['status'] = 2
                    self.logger.log_success(f"Депозит подтверждён!", wallet_data['address'])
                    return True
            time.sleep(random.uniform(10, 30))

    def show_swap_slippage(self, transaction_hash, account_address, token_from, token_to, retries=3):
        if not isinstance(transaction_hash, str) or len(transaction_hash) != 66:
            return 0, 0, 0

        for i in range(retries):
            try:
                tx = self.w3['BASE'].eth.get_transaction_receipt(transaction_hash)
                input_value, output_value = 0, 0

                if token_from == 'ETH':
                    tx_details = self.w3['BASE'].eth.get_transaction(transaction_hash)
                    input_value = tx_details['value']

                contract_address = tx['to'].lower()
                input_address = tokens_data[token_from]['address'].lower()
                output_address = tokens_data[token_to]['address'].lower()

                for log in tx['logs']:
                    try:
                        topics = log['topics']
                        if account_address[2:].lower() in topics[1].hex().lower() and input_address.lower() in log['address'].lower() and token_from != 'ETH':
                            if int(log['data'].hex(), 16) > 2 ** 160 - 1:
                                continue
                            input_value = int(log['data'].hex(), 16) if input_value < int(log['data'].hex(), 16) else input_value
                        if account_address[2:].lower() in topics[2].hex().lower() and output_address.lower() in log['address'].lower() and token_to != 'ETH':
                            if int(log['data'].hex(), 16) > 2 ** 160 - 1:
                                continue
                            output_value = int(log['data'].hex(), 16) if output_value < int(log['data'].hex(), 16) else output_value
                        elif output_address.lower() in log['address'].lower() and token_to == 'ETH':
                            if int(log['data'].hex(), 16) > 2 ** 160 - 1:
                                continue
                            output_value = int(log['data'].hex(), 16) if output_value < int(log['data'].hex(), 16) else output_value
                    except:
                        pass

                if input_value and output_value:
                    output_amount = output_value / (10 ** tokens_data[token_to]['decimal'])
                    input_amount = input_value / (10 ** tokens_data[token_from]['decimal'])
                    slip = ((output_amount * self.prices[token_to]) / (input_amount * self.prices[token_from])) * 100 - 100
                    return "{:.6f}".format(round(input_amount, 6)).rstrip('0').rstrip('.'), "{:.6f}".format(round(output_amount, 6)).rstrip('0').rstrip('.'), round(slip, 3)

                time.sleep(1)
            except:
                time.sleep(5)

        return 0, 0, 0

    def decide_swap(self, wallet_data, swap_out=False):

        eth_balance = wallet_data.get('ETH', {}).get('balance', 0)
        total_value = sum([token_data['amount'] * self.prices[token] for token, token_data in wallet_data.items() if token in list(self.prices.keys())])
        preferred_tokens = [token for token, data in tokens_data.items() if tokens_data[token]['swap'] is True]#['USDC', 'BUSD', 'USD+', 'WBTC']

        eth_value = wallet_data.get('ETH', {}).get('amount', 0) * self.prices['ETH']
        eth_contribution_percent = (eth_value / total_value) * 100

        if eth_balance < 10 ** 15 or eth_contribution_percent < 33:
            if len(wallet_data) == 1 and 'ETH' in wallet_data:
                return eth_balance / random.uniform(1.5, 2.5), 'ETH', random.choice(preferred_tokens)
            else:
                non_eth_tokens = [token for token in wallet_data.keys() if token != 'ETH']
                most_valuable_token = max(non_eth_tokens, key=lambda k: (wallet_data[k]['balance'] / (10 ** wallet_data[k]['decimals'])) * self.prices[k])
                return wallet_data[most_valuable_token]['balance'] * 0.9999 / (10 ** wallet_data[most_valuable_token]['decimals']), most_valuable_token, 'ETH'

        potential_swaps = []

        if eth_contribution_percent > 75:
            swap_to = random.choice([t for t in preferred_tokens if t != 'ETH'])
            return eth_balance / (10 ** 18) / random.uniform(1.5, 5), 'ETH', swap_to

        for token, token_data in wallet_data.items():
            if tokens_data.get(token, {}).get('swap', False) is False:
                continue
            token_value = (token_data['balance'] / (10 ** token_data['decimals'])) * self.prices[token]
            if token_value < 0.01:
                continue
            contribution_percent = (token_value / total_value) * 100

            if contribution_percent > 22 and token != 'ETH':
                swap_to = random.choice([t for t in preferred_tokens if t != token])
                amount = token_data['balance'] / (10 ** token_data['decimals'])
                amount = random.uniform(0.3, 0.99) * amount if token == 'ETH' else random.uniform(0.4, 1) * amount
                potential_swaps.append((amount, token, swap_to))

            elif 22 >= contribution_percent > 12:
                swap_to = random.choice([t for t in self.prices.keys() if t in wallet_data.keys() and t != token])
                amount = token_data['balance'] / (10 ** token_data['decimals'])
                amount = random.uniform(0.4, 0.99) * amount if token == 'ETH' else random.uniform(0.4, 1) * amount
                potential_swaps.append((amount, token, swap_to))

            elif 12 >= contribution_percent > 4:
                swap_to = random.choice([t for t in self.prices.keys() if t not in preferred_tokens and t != token])
                amount = token_data['balance'] / (10 ** token_data['decimals']) if token != 'ETH' else token_data['balance'] / 5 / (10 ** token_data['decimals'])
                amount = random.uniform(0.5, 0.99) * amount if token == 'ETH' else random.uniform(0.4, 1) * amount
                potential_swaps.append((amount, token, swap_to))

        if potential_swaps:
            return random.choice(potential_swaps)

        return None, None, None

    def change_amount(self, token_from, amount):
        value = self.prices[token_from] * amount
        new_value = min(self.settings['max_swap_value'], value)
        multiplier = random.uniform(0.6, 1) if new_value < value else 1
        return (float(new_value / self.prices[token_from])) * multiplier

    def process_swap(self, swap_instance, wallet_data, swap_out=False, ignore='NONE'):
        tokens = wallet_data['tokens']
        if not tokens:
            return

        if not swap_out:
            used_swaps = [swap_instance]

            for i in range(len(self.swaps_)):

                for i in range(max(3, int(self.settings['attempts']))):
                    token_from, token_to, amount = None, None, 0
                    try:
                        for X in range(9999999):
                            swappable_tokens = [token_ for token_ in tokens.keys() if tokens_data.get(token_, {'swap': False}).get('swap') is True]
                            if not swappable_tokens:
                                continue
                            filtered_token_data = {token: tokens[token] for token in swappable_tokens}
                            if not filtered_token_data:
                                continue

                            amount, token_from, token_to = self.decide_swap(filtered_token_data)
                            token_from_dexes = tokens_data.get(token_from, {}).get('dexs', [])
                            token_to_dexes = tokens_data.get(token_to, {}).get('dexs', [])
                            if self.settings['debug']:
                                print(f"SWAP | TOKEN FROM DATA: {token_from} / {token_from_dexes}")
                                print(f"SWAP | TOKEN TO DATA: {token_to} / {token_to_dexes}")
                                print(f"SWAP | SWAPPABLE TOKENS: {swappable_tokens}")
                            if (swap_instance.project not in token_to_dexes) or (swap_instance.project not in token_from_dexes) or token_from not in swappable_tokens or token_to not in swappable_tokens:
                                if X > 99999:
                                    swap_instance = random.choice(list(self.swaps_.values()))
                            else:
                                break

                        if not token_from or not token_to:
                            continue

                        amount = self.change_amount(token_from, amount)

                        res = swap_instance.swap(amount, token_from, token_to, wallet_data)
                        if self.settings['debug']:
                            print(f"PROCESS SWAP ({swap_instance.project} ({amount, token_from, token_to}) ) RESULT: {res}")
                        if res not in error_codes and res:
                            amount_from, amount_to, slip = self.show_swap_slippage(res, wallet_data['address'],token_from, token_to)
                            add_text = f"{token_from} ({amount_from}) в {token_to} ({amount_to}) [{'+' if slip > 0 else ''}{slip}%]" if amount_from else f"{token_from} ({amount}) в {token_to} (???)"
                            self.logger.log_success(f"{swap_instance.project} | Успешно сделал SWAP из {add_text}", wallet_data['address'])
                            return True
                        else:
                            raise Exception
                    except Exception as e:
                        if self.settings['debug']:
                            print(f"process_swap_error ({swap_instance.project} {token_from} ({round(amount, 6)}) в {token_to}): {e}")
                        time.sleep(random.uniform(3, 10))
                if len(used_swaps) < len(list(self.swaps_)):
                    while True:
                        tokens = self.helper.get_user_tokens(wallet_data['address'])
                        random_swap_name = random.choice(list(self.swaps_.keys()))
                        swap_instance = self.swaps_[random_swap_name]
                        if swap_instance in used_swaps:
                            continue
                        if self.settings['show_warnings']:
                            self.logger.log_warning(f"Меняю SWAP DEX после {max(3, int(self.settings['attempts']))} неудачных попыток на {swap_instance.project}...", wallet_data['address'])
                        used_swaps.append(swap_instance)
                        break
                else:
                    continue
            if len(list(self.swaps_.keys())) != 1:
                self.logger.log_error(f"Действие SWAP неуспешно на {len(list(self.swaps_))} DEX'ах, пропускаю!",wallet=wallet_data['address'])
            else:
                self.logger.log_error(f"Действие SWAP неуспешно после {max(3, int(self.settings['attempts']))} попыток, поменять DEX не вышло, пропускаю!", wallet=wallet_data['address'])
            return

        else:
            swappable_tokens = [token for token, data in tokens_data.items() if data['swap'] is True] # if data.get('swap', False) is not False
            if not swappable_tokens:
                return
            token_to = 'ETH'
            for token_from in swappable_tokens:
                if token_from == 'ETH' or token_from == ignore:
                    continue
                instanses = list(self.swaps_.values())
                random.shuffle(instanses)
                for swap_instance in instanses:
                    try:
                        amount = tokens.get(token_from, {}).get('amount', 0) * 0.9999
                        if amount * self.prices[token_from] < 0.01:
                            break

                        res = swap_instance.swap(amount, token_from, token_to, wallet_data)
                        if self.settings['debug']:
                            print(f"PROCESS SWAP ({swap_instance.project} ({amount, token_from, token_to}) ) RESULT: {res}")
                        if res not in error_codes and res:
                            time.sleep(random.uniform(self.settings['min_sleep']/2, self.settings['max_sleep']/2))
                            #self.logger.log_success(f"{swap_instance.project} | Успешно сделал SWAP из {token_from} ({round(amount, 6)}) в {token_to}{add}",  wallet_data['address'])
                            break
                        elif res in ['high_slip', 'no_route']:
                            continue
                        else:
                            raise Exception
                    except Exception as e:
                        if self.settings['debug']:
                            print(f"process_swap_error ({swap_instance.project}): {e}")
                        time.sleep(random.uniform(3, 5))
            return

    def calculate_liq_amount(self, selected_token, token_data):  #TODO CHANGE
        token_price = self.prices[selected_token]
        token_amount = token_data[selected_token]['amount']
        total_value = token_price * token_amount
        random_factor = random.uniform(0.6, 0.90) if selected_token != 'ETH' else random.uniform(0.2, 0.5)
        if total_value <= self.settings['max_liq_in_usd']:
            return self.settings['max_liq_in_usd'] / token_price * random_factor
        else:
            return self.settings['max_liq_in_usd'] / token_price * random_factor * 1.1

    def show_liq_data(self, transaction_hash, account_address, token_from=None, retries=3):
        if isinstance(transaction_hash, str) and len(transaction_hash) == 66:
            for i in range(retries):
                try:
                    tx = self.w3['BASE'].eth.get_transaction_receipt(transaction_hash)
                    tokens_data_ = {data['address'].lower(): data for data in tokens_data.values()}
                    values = []

                    if token_from:
                        tx_details = self.w3['BASE'].eth.get_transaction(transaction_hash)
                        if tx_details['value'] > 0:
                            values.append(['ETH', tx_details['value']])

                    for log in tx['logs']:
                        try:
                            topics = log['topics']
                            if token_from:

                                if account_address[2:].lower() in topics[1].hex().lower() and log['address'].lower() in [token_.lower() for token_ in tokens_data_.keys()]:
                                    input_value = int(log['data'].hex(), 16)
                                    if input_value > 10000000000000000000000000000000000000000000000000000000000000000000000:
                                        continue
                                    values.append([tokens_data_[log['address'].lower()]['symbol'], input_value])
                            else:
                                if account_address[2:].lower() in topics[2].hex().lower():
                                    input_value = int(log['data'].hex(), 16)
                                    if input_value > 10000000000000000000000000000000000000000000000000000000000000000000000:
                                        continue
                                    values.append([tokens_data_[log['address'].lower()]['symbol'], input_value])
                        except:
                            pass
                    if values:
                        for i in range(len(values)):
                            values[i] = [values[i][0], "{:.6f}".format(round((values[i][1] / (10 ** tokens_data[values[i][0]]['decimal'])), 6)).rstrip('0').rstrip('.')]
                        return values
                except:
                    time.sleep(2)
        return []

    def process_liq_withdraw(self, wallet_data):
        tokens = wallet_data['tokens']
        if not tokens:
            return

        liq_instances_to_process = list(self.liqs_.values())
        random.shuffle(liq_instances_to_process)

        for liq_instance in liq_instances_to_process:

            for i in range(max(3, int(self.settings['attempts']))):
                try:
                    res = liq_instance.rem_liq(wallet_data)
                    if self.settings['debug']:
                        print(f"PROCESS LIQ ({liq_instance.project}) RESULT: {res}")
                    if res and res != 'no_route':
                        continue
                    elif res == 'no_route':
                        time.sleep(random.uniform(self.settings['min_sleep'] / 2, self.settings['max_sleep'] / 2))
                        break
                    else:
                        raise Exception
                except Exception as e:
                    if self.settings['debug']:
                        print(f"process_liq_error ({liq_instance.project}): {e}")
                    time.sleep(random.uniform(3, 10))
        return

    def process_liq(self, liq_instance, wallet_data, withdraw=False, withdraw_out=False):
        tokens = wallet_data['tokens']
        if not tokens:
            return

        used_liqs = [liq_instance]
        lisq_with_no_liq = []

        liq_instances_to_process = self.liqs_ if not withdraw else self.liqs_added.get(wallet_data['address'], [])
        if len(liq_instances_to_process) == 0:
            return
            # withdraw = False
            # liq_instances_to_process = self.liqs_

        for current_liq_instance in liq_instances_to_process:
            if withdraw:
                liq_instance = current_liq_instance
            for i in range(max(3, int(self.settings['attempts']))):
                amount = 0
                try:

                    choices = [(liq_instance.add_liq, "add_liq"), (liq_instance.rem_liq, "rem_liq")]
                    if liq_instance.project in lisq_with_no_liq:
                        chosen_function, function_name = liq_instance.add_liq, "add_liq"
                    else:
                        chosen_function, function_name = random.choice(choices) if not withdraw else (liq_instance.rem_liq, "rem_liq")

                    if function_name == "add_liq":

                        liqble_tokens = [token for token in tokens if tokens_data.get(token, {}).get('liq')]
                        if not liqble_tokens:
                            continue
                        filtered_token_data = {token: tokens[token] for token in liqble_tokens}
                        if not filtered_token_data:
                            continue

                        eligible_tokens = [token for token, details in filtered_token_data.items() if 0.1 <= (details['amount'] * self.prices[token])]

                        if not eligible_tokens:
                            self.logger.log_error("Нет токенов для ликвидности, пропускаю...", wallet_data['address'])
                            if not withdraw:
                                return
                            else:
                                break

                        selected_token = random.choice(eligible_tokens)

                        while True:
                            token_from_dexes = tokens_data.get(selected_token, {}).get('dexs', [])
                            if liq_instance.project not in token_from_dexes:
                                liq_instance = random.choice(list(self.liqs_.values()))
                            else:
                                chosen_function = liq_instance.add_liq
                                break

                        amount = self.calculate_liq_amount(selected_token, filtered_token_data)
                        #print(f"PROJECT: {liq_instance.project}, TOKEN: {selected_token}")
                        res = chosen_function(amount, selected_token, wallet_data)
                    else:
                        res = chosen_function(wallet_data)
                        selected_token = None
                    if self.settings['debug']:
                        print(f"PROCESS LIQ ({liq_instance.project} ({selected_token})) RESULT: {res}")
                    if res not in error_codes and res:
                        if function_name == 'add_liq':
                            if wallet_data['address'] in self.liqs_added:
                                self.liqs_added[wallet_data['address']].append(liq_instance)
                            else:
                                self.liqs_added[wallet_data['address']] = [liq_instance]
                        data = self.show_liq_data(res, wallet_data['address'], token_from=selected_token)
                        try:
                            add_text = f"{data[0][0]} ({data[0][1]})" if len(data) == 1 else f"{data[0][0]} ({data[0][1]}) - {data[1][0]} ({data[1][1]})"
                        except:
                            add_text = ''
                        self.logger.log_success(f"{liq_instance.project} | Успешно {f'добавил ликвидность с токенами {add_text}' if function_name == 'add_liq' else f'удалил ликвидность из токенов {add_text}'}",wallet_data['address'])
                        if not withdraw:
                            return True
                        else:
                            break
                    else:
                        if selected_token == None:
                            lisq_with_no_liq.append(liq_instance.project)
                        raise Exception
                except Exception as e:
                    if self.settings['debug']:
                        print(f"process_liq_error ({liq_instance.project}): {e}")
                    time.sleep(random.uniform(3, 10))

            if len(used_liqs) < len(list(self.liqs_)):
                while True:
                    random_liq_name = random.choice(list(self.liqs_.keys()))
                    liq_instance = self.liqs_[random_liq_name]
                    if liq_instance in used_liqs:
                        continue
                    if self.settings['show_warnings']:
                        self.logger.log_warning(f"Меняю LIQ DEX после {max(3, int(self.settings['attempts']))} неудачных попыток на {liq_instance.project}...", wallet_data['address'])
                    used_liqs.append(liq_instance)
                    break
            else:
                continue
        if len(list(self.liqs_.keys())) != 1:
            self.logger.log_error(f"Действие LIQUIDITY неуспешно на {len(list(self.liqs_))} свапалках, пропускаю!",wallet=wallet_data['address'])
        else:
            self.logger.log_error(f"Действие LIQUIDITY неуспешно после {max(3, int(self.settings['attempts']))} попыток, поменять LIQ DEX не вышло, пропускаю!", wallet=wallet_data['address'])
        return

    def process_nft_market(self, nft_market_instance, wallet_data, sell=True):
        for i in range(max(3, int(self.settings['attempts'])*2)):
            try:
                tokens = wallet_data['tokens']
                if tokens['ETH']['balance'] / (10 ** 18) < self.settings['max_nft_price'] * 1.1:
                    self.logger.log_error(f"Пропускаю действие NFT MARKET, т.к. баланс менее {self.settings['max_nft_price']} ETH!", wallet=wallet_data['address'])
                    return
                if self.settings['list_nfts']:
                    if sell is True:
                        action = random.choice([lambda: nft_market_instance.buy_nft(wallet_data, self.settings['max_nft_price']), lambda: nft_market_instance.list_nft(wallet_data)])
                    else:
                        action = lambda: nft_market_instance.buy_nft(wallet_data, self.settings['max_nft_price'])
                    res = action()
                else:
                    res = nft_market_instance.buy_nft(wallet_data, self.settings['max_nft_price'])
                if self.settings['debug']:
                    print(f"PROCESS NFT ({nft_market_instance.project}) RESULT: {res}")
                if res and res not in error_codes:
                    return True
                else:
                    if res == 'no_nft':
                        sell = False
                        continue
                    raise Exception
            except Exception as e:
                if self.settings['debug']:
                    print(f"process_nft_error ({nft_market_instance.project}): {e}")
                random_market_name = random.choice(list(self.nft_markets_.keys()))
                nft_market_instance = self.nft_markets_[random_market_name]
                if self.settings['show_warnings']:
                    self.logger.log_warning(f"Меняю NFT MARKET на {nft_market_instance.project} после неудачной попытки...", wallet_data['address'])
                time.sleep(random.uniform(3, 10))
        self.logger.log_error(f"Действие NFT MARKET неуспешно после {max(3, int(self.settings['attempts']))} попыток, пропускаю!",wallet=wallet_data['address'])
        return

    def process_deriv(self, deriv_instance, wallet_data, close_all=False):

        tokens = wallet_data['tokens']
        if tokens.get('USDBC', {}).get('amount', 0) < 0.1 and close_all is False:
            if deriv_instance.project != 'UNIDEX':
                while True:
                    swap_instanse = random.choice(list(self.swaps_.values()))
                    try:
                        amount_to_swap = random.uniform(self.settings['deriv_max_value']/2, self.settings['deriv_max_value']) / self.prices['ETH']
                        actual_amount = tokens.get('ETH', {}).get('amount', 0)
                        if actual_amount == 0:
                            return
                        amount_to_swap = min(amount_to_swap, actual_amount * 0.8)
                        RES = swap_instanse.swap(float(amount_to_swap), 'ETH', 'USDBC', wallet_data)
                    except:
                        continue
                    if RES and RES not in error_codes:
                        time.sleep(random.uniform(self.settings['min_sleep'] / 2, self.settings['max_sleep'] / 2))
                        break
                tokens = self.helper.get_user_tokens(wallet_data['address'])
        if close_all is False:
            for i in range(max(3, int(self.settings['attempts']))):
                try:
                    amount_max = random.uniform(self.settings['deriv_max_value']/2, self.settings['deriv_max_value'])
                    if deriv_instance.project == 'ONCHAIN TRADE':
                        amount = min(tokens.get('USDBC', {}).get('amount', 0), amount_max) * 0.99
                    else:
                        max_eth_value = amount_max / self.prices['ETH']
                        amount = min(tokens.get('ETH', {}).get('amount', 0), max_eth_value)
                    if amount == 0:
                        return
                    res = deriv_instance.main(wallet_data, float(amount))
                    if res and res not in error_codes:
                        return True
                    else:
                        raise Exception
                except Exception as e:
                    if self.settings['debug']:
                        deriv_instance = random.choice(list(self.derives_.values()))
                        print(f"process_deriv_error ({deriv_instance.project}): {e}")
                    time.sleep(random.uniform(3, 10))
            self.logger.log_error(f"Действие DERIVATE неуспешно после {max(3, int(self.settings['attempts']))} попыток, пропускаю!", wallet=wallet_data['address'])
            return
        else:
            for deriv_instance in list(self.derives_.values()):
                for i in range(max(3, int(self.settings['attempts']))):
                    try:
                        res = deriv_instance.main(wallet_data, 0, withdraw_all=True)
                        if res == 'no_positions':
                            time.sleep(random.uniform(self.settings['min_sleep'] / 2, self.settings['max_sleep'] / 2))
                            break
                        elif res and res not in error_codes:
                            continue
                        else:
                            raise Exception
                    except Exception as e:
                        if self.settings['debug']:
                            print(f"process_deriv_error ({deriv_instance.project}): {e}")
                        time.sleep(random.uniform(3, 10))

    def process_lending(self, lending_instance, wallet_data, withdraw_out=False):
        for i in range(max(3, int(self.settings['attempts']))):
            try:
                tokens = self.helper.get_user_tokens(wallet_data['address'])
                token = 'ETH' if tokens.get('USDBC', {}).get('balance', 0) < 100000 else random.choice(['ETH', 'USDBC'])
                balance = tokens[token]['balance'] / (10 ** tokens[token]['decimals'])
                max_factor = 0.9 if token == 'USDBC' else 0.35
                factor = random.uniform(0.15, max_factor)
                value = balance*factor if self.prices[token] * balance * factor >= self.settings['lendings_max_value'] else (self.settings['lendings_max_value'] / self.prices[token] * factor)
                res = lending_instance.main(wallet_data, token, value, withdraw=withdraw_out)
                if self.settings['debug']:
                    print(f"PROCESS LENDING ({lending_instance.project}) RESULT: {res}")
                if res and res not in error_codes:
                    return True
                else:
                    raise Exception
            except Exception as e:
                if self.settings['debug']:
                    print(f"process_lending_error ({lending_instance.project}): {e}")
                time.sleep(random.uniform(3, 10))
        self.logger.log_error(f"Действие LENDING неуспешно после {max(3, int(self.settings['attempts']))} попыток, пропускаю!", wallet=wallet_data['address'])
        return

    def process_lending_withdraw(self, wallet_data):
        instanses = list(self.lendings_.values())
        random.shuffle(instanses)
        for lending_instance in instanses:
            for token in ['ETH', 'USDBC']:
                for i in range(max(3, int(self.settings['attempts']))):
                    try:
                        res = lending_instance.main(wallet_data, token, 0, withdraw=True)
                        if self.settings['debug']:
                            print(f"PROCESS LENDING ({lending_instance.project} TOKEN: {token}) RESULT: {res}")
                        if res and res not in error_codes and 'swap' not in res:
                            time.sleep(random.uniform(self.settings['min_sleep'] / 2, self.settings['max_sleep'] / 2))
                            break
                        elif isinstance(res, str) and res.startswith("swap"):
                            _, token_to_swap, amount = res.split("_")
                            token_from_swap = 'ETH' if token_to_swap == 'USDBC' else 'ETH'
                            value = int(amount) / (10 ** tokens_data[token_to_swap]['decimal']) * self.prices[token_to_swap]
                            amount_ = (value / self.prices[token_from_swap])
                            while True:
                                swap_instanse = random.choice(list(self.swaps_.values())) # amount, token_from, token_to, private_key
                                try:
                                    RES = swap_instanse.swap(round(amount_ * 1.01, 7), token_from_swap, token_to_swap, wallet_data)
                                except:
                                    continue
                                if RES and RES not in error_codes:
                                    time.sleep(random.uniform(self.settings['min_sleep'] / 2, self.settings['max_sleep'] / 2))
                                    break
                            continue
                        else:
                            raise Exception
                    except Exception as e:
                        if self.settings['debug']:
                            print(f"process_lending_error ({lending_instance.project}): {e}")
                        time.sleep(random.uniform(3, 5))

    def process_name_service(self, name_service_instance, wallet_data, res=False):
        for i in range(max(3, int(self.settings['attempts']))):
            tokens = wallet_data['tokens']
            if tokens.get('ETH', {}).get('amount', 0) < name_service_instance.price * 1.05:
                self.logger.log_error(f"Пропускаю действие NAME SERVICE, т.к. баланс менее {name_service_instance.price} ETH!", wallet=wallet_data['address'])
                return
            try:
                res = name_service_instance.domain(wallet_data)
                if self.settings['debug']:
                    print(f"PROCESS NS ({name_service_instance.project}) RESULT: {res}")
                if res and res not in error_codes:
                    return True
                else:
                    raise Exception
            except Exception as e:
                if self.settings['debug']:
                    print(f"process_names_error ({name_service_instance.project}): {e}")
                name_service_instance = random.choice(list(self.name_services_.values()))
                if self.settings['show_warnings']:
                    self.logger.log_warning(f"Ошибка во время действия NAME SERVICE, меняю на {name_service_instance.project} и пробую снова...", wallet=wallet_data['address'])
                time.sleep(random.uniform(3, 10))
        if res == 'no_route':
            if self.settings['show_warnings']:
                self.logger.log_warning(f"Действие NAME SERVICE неуспешно после {max(3, int(self.settings['attempts']))} попыток, вероятно все доменные имена уже получены!", wallet=wallet_data['address'])
        else:
            self.logger.log_error(f"Действие NAME SERVICE неуспешно после {max(3, int(self.settings['attempts']))} попыток, пропускаю!", wallet=wallet_data['address'])
        return

    def process_misc(self, misc_instance, wallet_data):
        for i in range(max(3, int(self.settings['attempts']))):
            tokens = wallet_data['tokens']
            if tokens.get('ETH',{}).get('balance', 0) / (10 ** 18) < 0.0005:
                self.logger.log_error(f"Пропускаю действие OTHER, т.к. баланс менее 0.0005 ETH!", wallet=wallet_data['address'])
                return
            try:
                res = misc_instance.main(wallet_data)
                if self.settings['debug']:
                    print(f"PROCESS MISC ({misc_instance.project}) RESULT: {res}")
                if res and res not in error_codes:
                    return True
                else:
                    raise Exception
            except Exception as e:
                if self.settings['debug']:
                    print(f"process_misc_error ({misc_instance.project}): {e}")
                misc_instance = random.choice(list(self.other_.values()))
                if self.settings['show_warnings']:
                    self.logger.log_warning(f"Ошибка во время действия OTHER, меняю на {misc_instance.project} и пробую снова...", wallet=wallet_data['address'])
                time.sleep(random.uniform(3, 10))
        self.logger.log_error(f"Действие OTHER неуспешно после {max(3, int(self.settings['attempts']))} попыток, пропускаю!", wallet=wallet_data['address'])
        return

    def process_bridge(self, bridge_instance, wallet_data, bridge_type='IN', warmup_procees=False):

        for i in range(max(3, int(self.settings['attempts']))*2):
            try:
                if bridge_type == 'IN':
                    native_balances = {chain: w3_.eth.get_balance(w3_.to_checksum_address(wallet_data['address'])) / (10 ** 18) for chain, w3_ in self.w3.items() if chain not in self.settings['black_chains'] and chain != 'BASE'}
                    filtered_balances = [chain for chain, balance in native_balances.items() if self.settings['to_base_min']*0.85 <= balance and chain not in self.settings['black_chains']]
                    if not filtered_balances:
                        self.logger.log_error(f"Пропускаю действие BRIDGE, т.к. нет балансов эфира в выбранных сетях!", wallet=wallet_data['address'])
                        return
                    random_chain = random.choice(filtered_balances)

                    if random_chain == 'ETH' and self.settings['main_prioritet'] and i < max(3, int(self.settings['attempts'])):
                        bridge_instance = self.bridges_['Main']

                    if bridge_instance.project == 'MAIN BRIDGE' and random_chain != 'ETH':
                        non_portal_bridges = [name for name, bridge in self.bridges_.items() if bridge.project != 'MAIN BRIDGE']
                        random_bridge_name = random.choice(non_portal_bridges)
                        bridge_instance = self.bridges_[random_bridge_name]
                    warmup_procees = self.process_warmup(wallet_data, bridge_type, random_chain, proceed=warmup_procees)
                    chain_balance = float(self.w3[random_chain].from_wei(self.w3[random_chain].eth.get_balance(wallet_data['address']), 'ether'))
                    value = random.uniform(self.settings['to_base_min'], self.settings['to_base_max']) if chain_balance >= self.settings['to_base_max'] else chain_balance
                    minus_fee = False if value != chain_balance else True
                    value = value * 0.99 if minus_fee else value

                    if value < 0.007 and bridge_instance.project == 'ORBITER':
                        continue
                    dest_chain_balance = self.w3['BASE'].eth.get_balance(wallet_data['address'])
                    res = bridge_instance.deposit(private_key=wallet_data, amount=value, from_chain=random_chain, to_chain='BASE', minus_fee=minus_fee, debug=self.settings['debug'])
                    if self.settings['debug']:
                        print(f"PROCESS BRIDGE ({bridge_instance.project}) RESULT: {res}")
                    if res and res not in error_codes:
                        res = wait_for_balance_change(self.w3['BASE'], wallet_data['address'], dest_chain_balance)
                        self.logger.log_success(f"{bridge_instance.project} | Успешно получил баланс ({round(res, 6)} ETH) в сети BASE", wallet=wallet_data['address'])
                        return True
                    else:
                        raise Exception
                else:
                    work_chains = self.okx.get_available_deposit_chains()
                    good_chains = [chain for chain in work_chains if chain not in self.settings['black_chains'] and chain not in ['BASE']]
                    chain_to = random.choice(good_chains)
                    if bridge_instance.project == 'MAIN BRIDGE':# and chain_to != 'ETH':
                        non_portal_bridges = [name for name, bridge in self.bridges_.items() if bridge.project != 'MAIN BRIDGE']
                        random_bridge_name = random.choice(non_portal_bridges)
                        bridge_instance = self.bridges_[random_bridge_name]
                    amount = wallet_data['tokens']['ETH']['balance'] * random.uniform(self.settings['okx_min_percent_wd']/100, self.settings['okx_max_percent_wd']/100)
                    minus_fee = True if amount == wallet_data['tokens']['ETH']['balance'] else False
                    amount = amount * 0.999 if minus_fee else amount
                    value = amount / (10 ** 18)
                    #print(f"BRIDGE OUT ({bridge_instance.project}) FOR {wallet_data['address']} | ACTUAL AMOUNT {wallet_data['tokens']['ETH']['amount']} | BRIDGE AMOUNT {value}")
                    if value < 0.007 and bridge_instance.project == 'ORBITER' or (bridge_instance.project == 'MAIN BRIDGE' and self.settings['ignore_main_bridge_withdraw']):
                        continue
                    dest_chain_balance = self.w3[chain_to].eth.get_balance(wallet_data['address'])
                    res = bridge_instance.withdraw(wallet_data, value, from_chain='BASE', to_chain=chain_to, minus_fee=minus_fee)
                    if self.settings['debug']:
                        print(f"PROCESS BRIDGE ({bridge_instance.project}) RESULT: {res}")
                    if res and res not in error_codes:
                        res = wait_for_balance_change(self.w3[chain_to], wallet_data['address'], dest_chain_balance)
                        self.logger.log_success(f"{bridge_instance.project} | Успешно получил баланс ({round(res, 6)} ETH) в сети {chain_to}", wallet=wallet_data['address'])
                        return chain_to
                    else:
                        raise Exception
            except Exception as e:
                if self.settings['debug']:
                    print(f"process_bridge_error ({bridge_instance.project} TYPE: {bridge_type}): {e}")
                random_bridge_name = random.choice(list(self.bridges_.keys()))
                bridge_instance = self.bridges_[random_bridge_name]
                time.sleep(10)
                continue
        self.logger.log_error(f"Действие BRIDGE неуспешно после {max(3, int(self.settings['attempts']))} попыток, пропускаю!",wallet=wallet_data['address'])
        return

    def generate_path(self, wallets):
        help_ = helper()

        wallets_data = {}

        for wallet in wallets:

            needed_tx = random.randint(self.settings['tx_min'], self.settings['tx_max'])

            actions = []  # ACTION NAME | WEIGHT | HALVING

            if len(self.swaps_) != 0:  # SWAPS
                actions.append({'action': 'SWAP', 'weight': 10, 'halving': 0.7})
            if len(self.liqs_) != 0:  # LIQS
                actions.append({'action': 'LIQUDITY', 'weight': 5, 'halving': 0.35})
            if len(self.nft_markets_) != 0:  # NFTS
                actions.append({'action': 'NFT MARKET', 'weight': 3, 'halving': 0.1})
            if len(self.name_services_) != 0:  # BNS
                actions.append({'action': 'NAMESERVICE', 'weight': 1, 'halving': 0})
            if len(self.lendings_) != 0:  # LENDINGS
                actions.append({'action': 'LENDING', 'weight': 6, 'halving': 0.4})
            if len(self.derives_) != 0:  # DERIVES
                actions.append({'action': 'DERIVATIVE', 'weight': 2.5, 'halving': 0.0001})
            if len(self.other_) != 0:  # MISC
                actions.append({'action': 'OTHER', 'weight': 3, 'halving': 0.1})

            path = []

            tokens = help_.get_user_tokens(wallet['address'], sleep_time=1)

            if tokens.get('ETH', {}).get('balance', 0) <= int(self.settings['min_eth_balance'] * 10 ** 18):
                path.append({'action': 'BRIDGE IN', 'status': 0})

            swap_added = False

            for _ in range(needed_tx):
                weights = [act['weight'] for act in actions]

                while True:
                    chosen_action = random.choices(actions, weights)[0]
                    if chosen_action['action'] == 'LIQUDITY' and not swap_added:
                        continue
                    else:
                        break

                if chosen_action['action'] == 'SWAP':
                    swap_added = True


                path.append({"action": chosen_action['action'], "status": 0})
                chosen_action['weight'] *= chosen_action['halving']

            if self.settings['okx']:
                path.append({'action': 'OKX DEPOSIT', 'status': 0})

            wallets_data[wallet['address']] = {"route": path, "tokens": tokens, "address": wallet['address'], "private_key": wallet['private_key'], "proxy": wallet.get('proxy', False)}

        return wallets_data

    def main(self, wallets_array):

        #RPC CHECK PART
        # chains_to_remove = [CHAIN for CHAIN in self.w3 if CHAIN in self.settings['black_chains']]
        # for CHAIN in chains_to_remove:
        #     self.w3.pop(CHAIN)

        for CHAIN, w3_ in self.w3.items():
            if CHAIN:
                try:
                    if not w3_.is_connected:
                        self.logger.log_error(f"Закончил работу, т.к. проблема с RPC для сети {CHAIN}, проверь!")
                        return
                except:
                    self.logger.log_error(f"Закончил работу, т.к. проблема с RPC для сети {CHAIN}, проверь!")
                    return

        #OKX CHECK PART
        if self.settings['okx']:
            res = self.okx.check_tfa()
            if not res:
                self.logger.log_error(f"Ошибка в данных OKX (2FA), проверь и запусти снова!")
                return
            res = self.okx.check_email()
            if not res:
                self.logger.log_error("Ошибка в данных OKX (EMAIL), проверь и запусти снова!")
                return
            res = self.okx.check_okx()
            if not res:
                self.logger.log_error("Ошибка в данных OKX (AUTH/DEVID), проверь и запусти снова!")
                return

        self.logger.log(f"Проверяю прокси для запросов...")
        if self.settings['requests_proxy']:
            is_proxy, country = self.helper.check_proxy()
            if is_proxy.lower() == 'yes':
                if country.lower() not in ['ru', 'blr']:
                    self.logger.log_success(f"Прокси страны '{country}' успешно проверены!")
                else:
                    self.logger.log_warning(f"Прокси России и Беларуси не подходят для полноценной работы, включи VPN или попробуй другие прокси")
            else:
                self.logger.log_warning(f"Прокси для запросов невалидны! Для полноценной работы включи VPN или попробуй другие прокси!")
        else:
            self.logger.log(f"Прокси для запросов в настройках не обнаружены!")

        #TODO OTHER SETTINGS CHECK PART
        wallets_data = []
        for wallet in wallets_array:
            try:
                p_key, proxy = wallet.split(';')
            except:
                p_key, proxy = wallet, False
            wallets_data.append({"address": self.w3['ETH'].eth.account.from_key(p_key).address, "private_key": p_key, "proxy": proxy})

        self.wallets_with_path = self.generate_path(wallets_data)
        self.wallet_to_procced = len(self.wallets_with_path)

        if self.settings['shuffle_wallets']:
            shuffled_keys = list(self.wallets_with_path.keys())
            random.shuffle(shuffled_keys)
            shuffled_wallets_with_path = {key: self.wallets_with_path[key] for key in shuffled_keys}
            self.wallets_with_path = shuffled_wallets_with_path

        if self.settings['okx']:
            self.logger.log(f"Начинаю стартовую работу с OKX...")
            self.okx_add_to_wl()

        self.logger.log(f"Начинаю работу для первой пачки из {min(self.wallet_to_procced, min(20, self.settings['max_batch_wallets']))}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(20, self.settings['max_batch_wallets'])) as executor:
            results = list(executor.map(self.process_wallet, self.wallets_with_path.values()))

        self.logger.log_success('SCRIPT VSE')


if __name__ == "__main__":

    data = {
        "swaps" : swaps_dict,
        "lendings" : lendings_dict,
        "nft_markets" : nft_markets_dict,
        "name_services" : name_services_dict,
        "liqs": liqs_dict,
        "bridges": bridges_dict,
        "derives": derivs_dict,
        "misc": misc_dict,
        "settings" : settings_dict,
    }

    logger = Logger()
    logger.log('Подготовка к работе... Может занять некоторое время...')

    if settings_dict['okx']:
        from modules.okx.okx import OKEX
    if settings_dict['warmup']:
        from modules.warmup import Warmup

    debug = False

    base_instanse = base_module(data, {w3: Web3(Web3.HTTPProvider(rpc)) for w3, rpc in w3_dict.items()}, logger, debug=debug)

    with open("wallets.txt", "r") as f:
        wallets = [row.strip() for row in f]

    base_instanse.main(wallets)