from helpers.data import TOKEN_ABI, NFT_ABI, swaps_data, tokens_data_
import time, random, re

def check_for_status(w3, hash, retries = 15):
    for i in range(retries):
        try:
            tx_status = w3.eth.get_transaction_receipt(hash)['status']
            if tx_status == 1 or bool(tx_status) is True:
                return True
            else:
                raise Exception
        except Exception:
            time.sleep(10)
    return False

def check_approve(w3, account, token, spender, nft=False, attempt=0):
    if token.lower() == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'.lower():
        token = '0x4200000000000000000000000000000000000006'
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(token), abi=TOKEN_ABI if not nft else NFT_ABI)
        allowance = contract.functions.allowance(w3.to_checksum_address(account.address), w3.to_checksum_address(spender)).call() if not nft else contract.functions.isApprovedForAll(w3.to_checksum_address(account.address), w3.to_checksum_address(spender)).call()
        return allowance
    except Exception as e:
        print(f"check_approve_Exp: {e} with token {token}")
        if attempt > 25:
            return 0
        time.sleep(1)
        return check_approve(w3=w3, account=account, token=token, spender=spender, nft=nft, attempt=attempt+1)

def make_approve(w3, account, token, spender, nft=False, attempt = 0):
    if token.lower() == '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'.lower():
        token = '0x4200000000000000000000000000000000000006'
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(token), abi=TOKEN_ABI if not nft else NFT_ABI)
        func_ = getattr(contract.functions, 'approve' if not nft else 'setApprovalForAll')
        if not nft:
            args = w3.to_checksum_address(spender), 115792089237316195423570985008687907853269984665640564039457584007913129
        else:
            args = w3.to_checksum_address(spender), True
        tx = make_tx(w3, account, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx
        hash, _ = send_tx(w3, account, tx)
        status = check_for_status(w3, hash)
        if not status:
            return make_approve(w3, account, token, spender, nft=nft, attempt = attempt+1)
        time.sleep(random.uniform(1, 2))
        return w3.to_hex(hash)
    except Exception as e:
        print(f"approve_Exp: {e} with token {token}")
        if attempt > 3:
            return
        time.sleep(3)
        return make_approve(w3, account, token, spender, nft=nft, attempt = attempt+1)

def get_balance(w3, account, token, address=False, decimals=False):
    contract = w3.eth.contract(address=w3.to_checksum_address(token), abi=TOKEN_ABI)
    try:
        if not decimals:
            balance = contract.functions.balanceOf(account.address if not address else address).call()
            return int(balance)
        else:
            balance = contract.functions.balanceOf(account.address if not address else address).call()
            decimals = contract.functions.decimals().call()
            return int(balance), int(decimals)
    except Exception as e:
        print(f'get balance exp {e} with {token}')
        if 'reverted' in str(e).lower():
            return 0
        time.sleep(1)
        return get_balance(w3, account, token, address, decimals)

def eth_wrapper(amount, to, w3, private_key, attempt = 0, eip = True, in_decimals=True, debug=False):
    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(address=w3.to_checksum_address(swaps_data['wrapper']['contract']), abi=swaps_data['wrapper']['ABI'])
    try:
        encoded_amount = int(amount * 10 ** 18) if in_decimals else amount
        if to == 'ETH':
            encoded_amount = min(encoded_amount, get_balance(w3, account, '0x4200000000000000000000000000000000000006'))
            data = contract.encodeABI(fn_name='withdraw', args=[encoded_amount])
            transaction_value = 0
        elif to == 'WETH':
            data = contract.encodeABI(fn_name='deposit', args=[])
            transaction_value = encoded_amount
        else:
            return

        tx = make_tx(w3, account, to=swaps_data['wrapper']['contract'], value=transaction_value, data=data, func=None, args=None, eip=eip, attempt=0, args_positioning=False)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(w3, hash)
        if not tx_status:
            return eth_wrapper(amount=amount, to=to, w3=w3, private_key=private_key, attempt = attempt+1, eip=eip, in_decimals=in_decimals, debug=debug)

        return w3.to_hex(hash)

    except Exception as e:
        if debug:
            print(f"eth_wrapper_error: {e}")
        if attempt > 5:
            return
        time.sleep(2)
        return eth_wrapper(amount=amount, to=to, w3=w3, private_key=private_key, attempt=attempt+1, eip=eip, in_decimals=in_decimals, debug=debug)

def send_tx(w3, account, tx, attempt = 0, print_out=False):
    try:
        sign = account.sign_transaction(tx)
        hash = w3.eth.send_raw_transaction(sign.rawTransaction)
        return hash, 0
    except Exception as e:
        if print_out:
            print(f"send_tx_error: {e}")
        if "insufficient funds" in str(e).lower():
            balance_match = re.search(r"balance: (\d+)", str(e))
            fee_match = re.search(r"fee: (\d+)", str(e))

            if balance_match and fee_match:
                balance = int(balance_match.group(1))
                fee = int(fee_match.group(1))
                new_value = balance - int(fee*1.05)
            else:
                gas_price = tx.get('gasPrice', 0) + tx.get('maxFeePerGas', 0)
                total_fee = (tx['gas'] * gas_price) if w3.eth.chain_id not in [10, 8453] else 500000000000000
                new_value = tx['value'] - int(total_fee * 1.1)
            if new_value > 0:

                return False, float(w3.from_wei(new_value, 'ether'))

        return False, float(w3.from_wei(tx['value'] * 0.995, 'ether'))

def make_tx(w3, account, to = '', value = 0, data = '0x', func = None, args = None, eip = True, attempt = 0, args_positioning=True, gas_multiplier = 0.75, minus_fee=False, TEST_VALUE=1, gas=0, print_out=False):
    if print_out:
        print(f"WALLET: {account.address}")
        print(f"ARGS: {args}")
        print(f"DATA: {data}")
        print(f"FUNC: {func}")
        print(f"VALUE: {value}")
        print(f"TO: {to}")
    try:
        chain_id = w3.eth.chain_id
        nonce = w3.eth.get_transaction_count(account.address)
        if data != '0x':
            tx = {
                'from': account.address,
                'to': w3.to_checksum_address(to),
                'nonce': nonce,
                'value': value,
                'data': data,
                'chainId': chain_id,
                'gasPrice': 0
            }
        elif args or func:
            if args_positioning and args is not None:
                tx = func(*args).build_transaction({
                    'from': account.address,
                    'nonce': nonce,
                    'value': 0 if func.fn_name == 'depositTransaction' else value,
                    'chainId': chain_id,
                    'gasPrice': 0
                })
            elif not args_positioning and args is not None:
                tx = func(args).build_transaction({
                    'from': account.address,
                    'nonce': nonce,
                    'value': value,
                    'chainId': chain_id,
                    'gasPrice': 0
                })
            else:
                tx = func().build_transaction({
                    'from': account.address,
                    'nonce': nonce,
                    'value': value,
                    'chainId': chain_id,
                    'gasPrice': 0
                })
        else:
            tx = {
                'from': account.address,
                'nonce': nonce,
                'value': value,
                'to': to,
                'chainId': chain_id,
                'gasPrice': 0
            }
        gas = w3.eth.gas_price

        if eip:
            tx.pop('gasPrice')
            tx['maxFeePerGas'] = gas if chain_id != 1 else int(gas*1.05)
            tx['maxPriorityFeePerGas'] = int(gas * random.uniform(0.09, 0.1)) if chain_id != 8453 else int(gas * random.uniform(0.009, 0.01))
        else:
            tx['gasPrice'] = gas

        if tx['value'] != 0 and minus_fee:
            tx['value'] = int(TEST_VALUE)

        tx['gas'] = w3.eth.estimate_gas(tx)
        if func:
            if func.fn_name == 'depositTransaction':
                tx['value'] = value
                tx['gas'] = int(tx['gas'] * 1.1)

        if chain_id == 8453:
            tx['gas'] = int(tx['gas'] * 1.02)
        if chain_id == 1 and data and data.startswith('0xb1a1a882'):
            tx['gas'] = int(tx['gas'] * 1.5)
        if minus_fee:
            if eip:
                total_fee = (tx['maxFeePerGas'] * tx['gas']) if chain_id not in [10, 8453] else 500000000000000
            else:
                total_fee = tx['gasPrice'] * tx['gas']
            tx['value'] = value - int(total_fee)

        return tx

    except Exception as e:
        if print_out:
            print(f"make_tx error ({account.address}): {e}")
        if attempt > 11:
            return

        if '0xa61be9f000000000000000000000000000000000000000000000000000005af3107a4000' in str(e).lower():
            return 'element_rerun'

        if '0x6f7eac26'.lower() in str(e).lower():
            return 'kreatora_rerun'

        if '0xd81b2f2e0000000000000000000000000000000000000000000000000000000000000000' in str(e).lower():
            return 'uni_rerun'

        if 'execution reverted: callBytes failed: Error(ERR_LIMIT_OUT)'.lower() in str(e).lower(): #firebird bug ?
            time.sleep(1)
            return 'fire_rerun'

        if 'OpenOcean external call failed: Error(K)'.lower() in str(e).lower() or 'Return amount is not enough'.lower() in str(e).lower(): #openocean bug ?
            time.sleep(random.uniform(2, 4))
            return 'ocean_rerun'

        if "Incorrect ETH value sent".lower() in str(e).lower(): #mintfun
            return 'change_nft'

        if '0xde9b74a1' in str(e).lower() or 'ERR_INVALID_AMOUNT'.lower() in str(e).lower() or '0x47bc813a' in str(e):
            TEST_VALUE = value
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier + 0.05, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if "amount under threshold" in str(e).lower() or 'first swap failed' in str(e).lower():
            if attempt > 2 and minus_fee:
                value = float(w3.from_wei(value * 0.99, 'ether'))
                return f"newvalue_{value}"
            TEST_VALUE = 10**16
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier+0.05, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if '0xf4059071' in str(e):  #1INCH SafeTransferFromFailed error
            if attempt > 5:
                return 'error'
            return 'attempt'
            #return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier+0.05, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if '0x480f42470000000000000000000000000000000000000000000000000000000000000004' in str(e): #lending redeem more than could
            if attempt > 7:
                return 'error'
            time.sleep(1)
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=int(args * (0.9995 * 1 / (1+(attempt+1)/100))) , eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if '0x10fda3e1'.lower() in str(e).lower() or '0x6f7eac26' in str(e).lower():
            return "order_filled"

        if 'RouteProcessor: Minimal ouput balance violation'.lower() in str(e).lower():
            return 'factor'

        if 'exceeded limit' in str(e).lower(): #onchain trade error (random?)
            time.sleep(random.uniform(30, 60))
            if attempt > 3:
                return 'error'
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if 'position_not_exist' in str(e).lower():  #onchain trade already closed
            return 'already_closed'

        if 'nonce too low' in str(e).lower():
            time.sleep(1)
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if 'block base fee' in str(e).lower():
            time.sleep(10)
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if 'Bad Gateway'.lower() in str(e).lower():
            time.sleep(1)
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if '429 Client Error'.lower() in str(e).lower():
            time.sleep(random.uniform(3, 10))
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if 'Read timed out'.lower() in str(e).lower():
            if attempt > 2:
              return 'error'
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if 'gas required exceeds allowance' in str(e).lower():
            if minus_fee:
                value = float(w3.from_wei(value * 0.999, 'ether'))
                return f"newvalue_{value}"
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if 'insufficient funds'.lower() in str(e).lower():
            if minus_fee:
                value = float(w3.from_wei(value * 0.999, 'ether'))
                return f"newvalue_{value}"
            if attempt > 6:
                return "low_native"
            return make_tx(w3, account, to=to, value=int(value*0.9975), data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        if "execution reverted".lower() in str(e).lower():
            if attempt > 2:
                return 'error'
            if 'mv' in str(e).lower():
                return 'mv_error'
            time.sleep(3)
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

        else:
            if attempt > 3:
                return False
            return make_tx(w3, account, to=to, value=value, data=data, func=func, args=args, eip=eip, attempt=attempt + 1, args_positioning=args_positioning, gas_multiplier=gas_multiplier, minus_fee=minus_fee, TEST_VALUE=TEST_VALUE, print_out=print_out)

def check_slippage(prices, token_from, token_to, amount_from, amount_to, in_decimals=False, print_out=False, attempt=0):
    try:
        token_from = 'ETH' if token_from == 'WETH' else token_from
        token_to = 'ETH' if token_to == 'WETH' else token_to
        token_from = 'BUSD' if token_from == 'cBUSD' else token_from
        token_to = 'BUSD' if token_to == 'cBUSD' else token_to
        if not in_decimals:
            amount_from = amount_from / (10 ** tokens_data_[token_from]['decimal'])
            amount_to = amount_to / (10 ** tokens_data_[token_to]['decimal'])
        amount_from_usd = amount_from * prices[token_from]
        expected_amount = amount_from_usd / prices[token_to]
        slippage = ((expected_amount - amount_to) / expected_amount) * 100
        if print_out:
            print(f"TOKEN FROM | TOKEN TO | AMOUNT FROM | AMOUNT TO | SLIP: {token_from, token_to, amount_from, amount_to, slippage}")
            print(f"PRICE FROM | PRICE TO: {prices[token_from], prices[token_to]}")
        return slippage
    except:
        if attempt >= 3:
            return 100
        time.sleep(1)
        return check_slippage(prices=prices, token_from=token_from, token_to=token_to, amount_from=amount_from, amount_to=amount_to, in_decimals=in_decimals, print_out=print_out, attempt=attempt+1)

def wait_for_balance_change(w3, address, old_balance, token=False, decimals = 18):
    while True:
        try:
            if not token:
                new_balance = w3.eth.get_balance(w3.to_checksum_address(address))
            else:
                new_balance = 0
                pass #TODO ADD CHECKER FOR TOKEN ???
            if new_balance > old_balance:
                return (new_balance - old_balance) / 10 ** decimals
        except:
            time.sleep(60)
        time.sleep(random.uniform(30, 60))