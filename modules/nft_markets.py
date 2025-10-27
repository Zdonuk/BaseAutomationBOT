import hmac, json, hashlib
from helpers.utils import *
from helpers.data import markets_data, NULL_ADDRESS
from eth_account.messages import encode_defunct, encode_structured_data
from eth_account import Account
from datetime import datetime, timedelta

class Element():

    def __init__(self, w3, logger, helper):
        self.help = helper
        self.session = self.help.get_tls_session()
        self.w3 = w3
        self.project = 'ELEMENT'
        self.logger = logger
        self.contract = w3.eth.contract(address=w3.to_checksum_address(markets_data[self.project]['contract']), abi=markets_data[self.project]['ABI'])

    def generate_xapi_signature(self, api_key='zQbYj7RhC1VHIBdWU63ki5AJKXloamDT', secret='UqCMpfGn3VyQEdsjLkzJv9tNlgbKFD7O'):
        random_number = random.randint(1000, 9999)
        timestamp = int(time.time())
        message = f"{api_key}{random_number}{timestamp}"
        signature = hmac.new(bytes(secret, 'latin-1'), msg=bytes(message, 'latin-1'), digestmod=hashlib.sha256).hexdigest()
        return f"{signature}.{random_number}.{timestamp}"

    def get_headers(self, auth=False):
        headers = {
            'authority': 'api.element.market',
            'accept': 'application/json',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://element.market',
            'referer': 'https://element.market/',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'x-api-key': 'zQbYj7RhC1VHIBdWU63ki5AJKXloamDT',
            'x-api-sign': str(self.generate_xapi_signature()),
            'x-viewer-chainmid': '1201',
        }
        if auth:
            headers['auth'] = auth
        return headers

    def get_nonce(self, account):
        for i in range(3):
            try:
                payload = {"query":"\n    query GetNonce($address: Address!, $chain: Chain!, $chainId: ChainId!) {\n        user(identity: { address: $address, blockChain: { chain: $chain, chainId: $chainId } }) {\n            nonce\n        }\n    }\n","variables":{"address":f"{account.address}","chain":"base","chainId":"0x2105"}}
                result = self.help.fetch_tls(session = self.session, url='https://api.element.market/graphql', type='post', payload=payload, headers=self.get_headers())
                return result['data']['user']['nonce']
            except:
                time.sleep((i + 1) * i)
        return None

    def get_auth(self, nonce, account):
        for i in range(3):
            message_ = f'Welcome to Element!\n   \nClick "Sign" to sign in. No password needed!\n   \nI accept the Element Terms of Service: \n https://element.market/tos\n   \nWallet address:\n{account.address.lower()}\n   \nNonce:\n{str(nonce)}'
            message = message_.encode()
            message_to_sign = encode_defunct(primitive=message)
            signed_message = self.w3.eth.account.sign_message(message_to_sign, private_key=account._private_key.hex())
            sig = signed_message.signature.hex()
            json_data = {
                'query': '\n    mutation LoginAuth($identity: IdentityInput!, $message: String!, $signature: String!) {\n        auth {\n            login(input: { identity: $identity, message: $message, signature: $signature }) {\n                token\n            }\n        }\n    }\n',
                'variables': {
                    'identity': {
                        'address': account.address.lower(),
                        'blockChain': {
                            'chain': 'base',
                            'chainId': '0x2105',
                        },
                    },
                    'message': f'Welcome to Element!\n   \nClick "Sign" to sign in. No password needed!\n   \nI accept the Element Terms of Service: \n https://element.market/tos\n   \nWallet address:\n{account.address.lower()}\n   \nNonce:\n{str(nonce)}',
                    'signature': sig,
                },
            }
            result = self.help.fetch_tls(session = self.session, url='https://api.element.market/graphql', type='post', payload=json_data, headers=self.get_headers())
            return result['data']['auth']['login']['token']

        return None

    def get_collection(self, auth):
        for i in range(3):
            try:
                json_data = {"operationName":"SearchCollectionListAll",
                             "variables":
                                 {"first":50,
                                  "verified":False,
                                  "sortBy":"SevenDayAmount",
                                  "blockChains":
                                      [{"chain":"base","chainId":"0x2105"}]},
                             "query":"query SearchCollectionListAll($before: String, $after: String, $first: Int, $last: Int, $querystring: String, $categorySlugs: [String!], $sortBy: CollectionSearchSortBy, $blockChains: [BlockChainInput!], $verified: Boolean) {\n  collectionSearch(\n    before: $before\n    after: $after\n    first: $first\n    last: $last\n    input: {querystring: $querystring, sortBy: $sortBy, categorySlugs: $categorySlugs, verified: $verified, blockChains: $blockChains}\n  ) {\n    edges {\n      cursor\n      node {\n        name\n        imageUrl\n        slug\n        isVerified\n        featuredImageUrl\n        bannerImageUrl\n        stats(realtime: true) {\n          stats1D {\n            saleCount\n            floorPrice\n            floorPriceRatio\n            volume\n            coin {\n              name\n              address\n              icon\n            }\n          }\n        }\n      }\n    }\n    pageInfo {\n      startCursor\n      endCursor\n      hasPreviousPage\n      hasNextPage\n    }\n  }\n}\n"}
                while True:
                    result = self.help.fetch_tls(session = self.session, url = 'https://api.element.market/graphql?args=SearchCollectionListAll', type='post', headers=self.get_headers(auth), payload=json_data)
                    eligeble_collections = []
                    for y in result['data']['collectionSearch']['edges']:
                        try:
                            if float(y["node"]['stats']['stats1D']['saleCount']) > 0 and float(y["node"]['stats']['stats1D']['floorPrice']) <= self.max_price:
                                eligeble_collections.append(y['node'])
                        except:
                            pass
                    if len(eligeble_collections) > 3:
                        return random.choice(eligeble_collections)
                    else:
                        json_data['variables']['after'] = result['data']['collectionSearch']['edges'][-1]['cursor']
            except Exception:
                time.sleep((i+1)*i)
        return None

    def get_item(self, slug, auth):
        for i in range(5):
            try:
                headers = self.get_headers(auth=auth)
                params = {
                    'args': 'AssetsListForCollectionV2',
                }
                json_data = {
                    'operationName': 'AssetsListForCollectionV2',
                    'variables': {
                        'realtime': False,
                        'thirdStandards': [],
                        'collectionSlugs': [
                            slug,
                        ],
                        'sortAscending': False,
                        'sortBy': 'PriceLowToHigh',
                        'toggles': [
                            'BUY_NOW',
                        ],
                        'first': 36,
                        'isPendingTx': True,
                        'isTraits': False,
                    },
                    'query': 'query AssetsListForCollectionV2($before: String, $after: String, $first: Int, $last: Int, $querystring: String, $categorySlugs: [String!], $collectionSlugs: [String!], $sortBy: SearchSortBy, $sortAscending: Boolean, $toggles: [SearchToggle!], $ownerAddress: Address, $creatorAddress: Address, $blockChains: [BlockChainInput!], $paymentTokens: [String!], $priceFilter: PriceFilterInput, $traitFilters: [AssetTraitFilterInput!], $contractAliases: [String!], $thirdStandards: [String!], $uiFlag: SearchUIFlag, $markets: [String!], $isTraits: Boolean!, $isPendingTx: Boolean!, $noPending: Boolean) {\n  search: searchV2(\n    \n    before: $before\n    after: $after\n    first: $first\n    last: $last\n    search: {querystring: $querystring, categorySlugs: $categorySlugs, collectionSlugs: $collectionSlugs, sortBy: $sortBy, sortAscending: $sortAscending, toggles: $toggles, ownerAddress: $ownerAddress, creatorAddress: $creatorAddress, blockChains: $blockChains, paymentTokens: $paymentTokens, priceFilter: $priceFilter, traitFilters: $traitFilters, contractAliases: $contractAliases, uiFlag: $uiFlag, markets: $markets, noPending: $noPending}\n  ) {\n    totalCount\n    edges {\n      cursor\n      node {\n        asset {\n          chain\n          chainId\n          contractAddress\n          tokenId\n          tokenType\n          name\n          imagePreviewUrl\n          animationUrl\n          rarityRank\n          assetOwners(first: 1) {\n            ...AssetOwnersEdges\n          }\n          orderData(standards: $thirdStandards) {\n            bestAsk {\n              ...BasicOrder\n            }\n            bestBid {\n              ...BasicOrder\n            }\n          }\n          assetEventData {\n            lastSale {\n              lastSalePrice\n              lastSalePriceUSD\n              lastSaleTokenContract {\n                name\n                address\n                icon\n                decimal\n                accuracy\n              }\n            }\n          }\n          pendingTx @include(if: $isPendingTx) {\n            time\n            hash\n            gasFeeMax\n            gasFeePrio\n            txFrom\n            txTo\n            market\n          }\n          traits @include(if: $isTraits) {\n            trait\n            numValue\n          }\n          collection {\n            slug\n            rarityEnable\n            categories {\n              slug\n            }\n          }\n          suspiciousStatus\n          uri\n        }\n      }\n    }\n    pageInfo {\n      hasPreviousPage\n      hasNextPage\n      startCursor\n      endCursor\n    }\n  }\n}\n\nfragment BasicOrder on OrderV3Type {\n  __typename\n  chain\n  chainId\n  chainMId\n  expirationTime\n  listingTime\n  maker\n  taker\n  side\n  saleKind\n  paymentToken\n  quantity\n  priceBase\n  priceUSD\n  price\n  standard\n  contractAddress\n  tokenId\n  schema\n  extra\n  paymentTokenCoin {\n    name\n    address\n    icon\n    chain\n    chainId\n    decimal\n    accuracy\n  }\n}\n\nfragment AssetOwnersEdges on AssetOwnershipTypeConnection {\n  __typename\n  edges {\n    cursor\n    node {\n      chain\n      chainId\n      owner\n      balance\n      account {\n        identity {\n          address\n          blockChain {\n            chain\n            chainId\n          }\n        }\n        user {\n          id\n          address\n          profileImageUrl\n          userName\n        }\n        info {\n          profileImageUrl\n          userName\n        }\n      }\n    }\n  }\n}\n',
                }
                result = self.help.fetch_tls(session = self.session, url = 'https://api.element.market/graphql', type='post', headers=headers, params=params, payload=json_data)
                for i in result['data']['search']['edges']:
                    return i['node']['asset']
            except:
                time.sleep((i + 1) * i)
        return None

    def get_buy_data(self, contract, token_id, type, auth, account):
        for i in range(5):
            try:
                type = 'buyERC721Ex' if type == 'ERC721' else 'buyERC1155Ex'
                headers = self.get_headers()
                json_data = {
                    'chainMId': 1201,
                    'buyer': account.address.lower(),
                    'data': [
                        {
                            'contractAddress': str(contract).lower(),
                            'tokenId': str(token_id),
                            'callFuncName': str(type),
                        },
                    ],
                    'standards': [],
                }
                result = self.help.fetch_tls(session = self.session,url='https://api.element.market/v3/orders/exSwapTradeDataByItem', type='post', headers=headers, payload=json_data)
                return result['data']['commonData'][0]
            except:
                time.sleep((i + 1) * i)
        return None

    def generate_trade_bytes(self, assets, trades = []):

        def generate_trade_data(trade, is_multiple_assets):
            trade_data = trade['tradeData'][2:] if trade['tradeData'].startswith("0x") else trade['tradeData']

            if len(trade_data) % 2 != 0:
                raise ValueError("Illegal tradeData: " + trade['tradeData'])

            market_id_bytes = int(trade['marketId']).to_bytes(16, byteorder='big').hex()
            value_bytes = int(trade['value']).to_bytes(168, byteorder='big').hex()
            length_bytes = (len(trade_data) // 2).to_bytes(32, byteorder='big').hex()

            return (
                    process_data(market_id_bytes, 16) +
                    process_data("0x1" if is_multiple_assets else "0x0", 8) +
                    process_data(value_bytes, 168) +
                    process_data(length_bytes, 32) +
                    trade_data
            )

        def process_data(data, required_length):
            processed = data[2:].lower() if data.startswith("0x") else data.lower()

            if len(processed) > required_length // 4:
                return processed[-required_length // 4:]

            padding = "".join("0" for _ in range(len(processed), required_length // 4))

            return padding + processed

        result = "0x"

        for trade in trades:
            result += generate_trade_data(trade, False)

        multiple_assets = len(assets) > 1

        for asset in assets:
            result += generate_trade_data(asset, multiple_assets)

        return result

    def buy_nft(self, private_key, max_price, attempt=0, auth=None):

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
        self.max_price = max_price

        nonce = self.get_nonce(account)
        if not nonce:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)
        auth = self.get_auth(nonce, account)
        if not auth:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        collection = self.get_collection(auth)
        if not collection:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        item = self.get_item(collection['slug'], auth)
        if not item:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        if item['tokenType'] != "ERC721":
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        order_data = self.get_buy_data(item['contractAddress'], item["tokenId"], item['tokenType'], auth, account)
        if not order_data:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        trade = [{'marketId': '1', 'value': order_data['value'], 'tradeData': order_data['data']}]
        try:
            trade_bytes = self.generate_trade_bytes(trade)
        except:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        func_ = getattr(self.contract.functions, 'batchBuyWithETH')
        tx = make_tx(new_w3, account, value=int(order_data['value']), func=func_, args=trade_bytes, args_positioning=False)

        if tx == "low_native" or not tx:
            return tx
        if tx == 'element_rerun':
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1)

        try:
            nft = f"{collection['name']} #{item['tokenId']}"
        except:
            nft = 'UNKNOWN'
        try:
            value = round(int(order_data['value']) / 10 ** 18, 6)
        except:
            value = 'UNKNOWN'
        self.logger.log_success(f"{self.project} | Успешно купил NFT ({nft}) за {value} ETH",wallet=account.address)
        return new_w3.to_hex(hash)

    def get_maker_nonce(self, auth, account):
        for i in range(3):
            try:
                payload = {"exchange": "0xa39a5f160a1952ddf38781bd76e402b0006912a9", "maker": account.address, "chain": "base", "schema": "erc721", "count": 1}
                res = self.help.fetch_tls(session = self.session,url= 'https://api.element.market/v3/orders/getMakerNonce', type='post', payload=payload, headers=self.get_headers(auth=auth))
                return res['data']
            except:
                time.sleep((i+1)*i)
        return None

    def get_fees(self, contract, auth, token_id='0'):
        for i in range(3):
            try:
                payload = {"chainMid": 1201, "standard": ["element-ex-v3"], "contracts": [{"contractAddress": contract, "tokenId": token_id}]}
                res = self.help.fetch_tls(session = self.session, url='https://api.element.market/bridge/v1/royalty', type='post', payload=payload, headers=self.get_headers(auth=auth))
                return res['data']
            except:
                time.sleep((i + 1) * i)
        return None

    def get_platform_fees(self, fees):
        platformFeeRecipient = None
        if 'protocolFeePoints' in fees:
            protocolFeeAddress = fees['protocolFeeAddress'].lower() if 'protocolFeeAddress' in fees else NULL_ADDRESS
            if platformFeeRecipient:
                pass
            else:
                platformFeeRecipient = protocolFeeAddress
        return platformFeeRecipient if platformFeeRecipient else NULL_ADDRESS

    def get_nft(self, auth, account):
        for i in range(3):
            try:
                payload = {"operationName": "AssetsListFromUser",
                           "variables": {"realtime": True, "thirdStandards": ["element-ex-v3"], "sortAscending": False,
                                         "sortBy": "RecentlyTransferred", "toggles": ["NOT_ON_SALE"],
                                         "ownerAddress": account.address, "first": 50, "uiFlag": "COLLECTED",
                                         "blockChains": [{"chain": "base", "chainId": "0x2105"}],
                                         "account": {"address": account.address,
                                                     "blockChain": {"chain": "base", "chainId": "0x2105"}},
                                         "constantWhenERC721": 1},
                           "query": "query AssetsListFromUser($before: String, $after: String, $first: Int, $last: Int, $querystring: String, $categorySlugs: [String!], $collectionSlugs: [String!], $sortBy: SearchSortBy, $sortAscending: Boolean, $toggles: [SearchToggle!], $ownerAddress: Address, $creatorAddress: Address, $blockChains: [BlockChainInput!], $paymentTokens: [String!], $priceFilter: PriceFilterInput, $stringTraits: [StringTraitInput!], $contractAliases: [String!], $thirdStandards: [String!], $uiFlag: SearchUIFlag, $account: IdentityInput, $constantWhenERC721: Int) {\n  search(\n    \n    before: $before\n    after: $after\n    first: $first\n    last: $last\n    search: {querystring: $querystring, categorySlugs: $categorySlugs, collectionSlugs: $collectionSlugs, sortBy: $sortBy, sortAscending: $sortAscending, toggles: $toggles, ownerAddress: $ownerAddress, creatorAddress: $creatorAddress, blockChains: $blockChains, paymentTokens: $paymentTokens, priceFilter: $priceFilter, stringTraits: $stringTraits, contractAliases: $contractAliases, uiFlag: $uiFlag}\n  ) {\n    totalCount\n    edges {\n      cursor\n      node {\n        asset {\n          chain\n          chainId\n          contractAddress\n          tokenId\n          tokenType\n          name\n          imagePreviewUrl\n          animationUrl\n          rarityRank\n          isFavorite\n          ownedQuantity(viewer: $account, constantWhenERC721: $constantWhenERC721)\n          orderData(standards: $thirdStandards) {\n            bestAsk {\n              ...BasicOrder\n            }\n            bestBid {\n              ...BasicOrder\n            }\n          }\n          assetEventData {\n            lastSale {\n              lastSaleDate\n              lastSalePrice\n              lastSalePriceUSD\n              lastSaleTokenContract {\n                name\n                address\n                icon\n                decimal\n                accuracy\n              }\n            }\n          }\n          marketStandards(account: $account) {\n            count\n            standard\n            floorPrice\n          }\n          collection {\n            name\n            isVerified\n            slug\n            imageUrl\n            royaltyFeeEnforced\n            contracts {\n              blockChain {\n                chain\n                chainId\n              }\n            }\n          }\n          suspiciousStatus\n          uri\n        }\n      }\n    }\n    pageInfo {\n      hasPreviousPage\n      hasNextPage\n      startCursor\n      endCursor\n    }\n  }\n}\n\nfragment BasicOrder on OrderV3Type {\n  __typename\n  chain\n  chainId\n  chainMId\n  expirationTime\n  listingTime\n  maker\n  taker\n  side\n  saleKind\n  paymentToken\n  quantity\n  priceBase\n  priceUSD\n  price\n  standard\n  contractAddress\n  tokenId\n  schema\n  extra\n  paymentTokenCoin {\n    name\n    address\n    icon\n    chain\n    chainId\n    decimal\n    accuracy\n  }\n}\n"}

                res = self.help.fetch_tls(session=self.session, url='https://api.element.market/graphql?args=AssetsListFromUser', type='post', payload=payload, headers=self.get_headers(auth=auth))
                items = []
                edges = res["data"]["search"]["edges"]
                for item in edges:
                    items.append(item['node']['asset'])
                return random.choice(items)
            except:
                time.sleep((i + 1) * i)
        return None

    def list_nft(self, private_key, attempt=0):

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

        nonce = self.get_nonce(account)
        if not nonce:
            return self.list_nft(private_key, attempt=attempt+1)
        auth = self.get_auth(nonce, account)
        if not auth:
            return self.list_nft(private_key, attempt=attempt+1)

        def to_standard_basic_collections(order):
            basic_collections = []
            if order.get('basicCollections') is not None:
                for collection in order['basicCollections']:
                    items = []
                    if collection.get('items'):
                        for item in collection['items']:
                            items.append(encode_bits([
                                [item['paymentTokenAmount'], 96],
                                [item['erc721TokenId'], 160]
                            ]))
                    fee = [
                        [0, 64],
                        [collection['platformFee'], 16],
                        [collection['royaltyFee'], 16],
                        [collection['royaltyFeeRecipient'], 160]
                    ]
                    basic_collections.append({
                        'nftAddress': collection['nftAddress'],
                        'fee': encode_bits(fee),
                        'items': items
                    })
            try:
                basic_collections[0]['fee'] = bytes.fromhex(basic_collections[0]['fee'][2:])
                basic_collections[0]['items'] = [bytes.fromhex(basic_collections[0]['items'][0][2:])]
            except:
                pass
            return basic_collections

        def to_standard_collections(order):
            collections = []
            if order.get('collections') is not None:
                for collection in order['collections']:
                    items = []
                    if collection.get('items'):
                        items.extend(collection['items'])
                    collections.append({
                        'nftAddress': collection['nftAddress'],
                        'fee': encode_bits([
                            [0, 64],
                            [collection['platformFee'], 16],
                            [collection['royaltyFee'], 16],
                            [collection['royaltyFeeRecipient'], 160]
                        ]),
                        'items': items
                    })
            try:
                collections[0]['fee'] = bytes.fromhex(collections[0]['fee'][2:])
                collections[0]['items'] = [bytes.fromhex(collections[0]['items'][0][2:])]
            except:
                pass
            return collections

        def encode_bits(args):
            data = '0x'
            for arg in args:
                if isinstance(arg[0], str) and arg[0].startswith('0x'):
                    arg_val = int(arg[0][2:], 16)
                else:
                    arg_val = int(arg[0])
                data += to_hex_bytes(hex(arg_val).lower(), arg[1])
            data = data.ljust(64, '0')
            return data

        def to_hex_bytes(hex_str, bit_count):
            count = bit_count // 4
            str_hex = hex_str[2:] if hex_str.lower().startswith('0x') else hex_str.lower()
            if len(str_hex) > count:
                return str_hex[-count:]
            return str_hex.rjust(count, '0')

        def to_standart_erc20_token(erc20Token):
            if erc20Token and erc20Token.lower() != '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee':
                return erc20Token.lower()
            return NULL_ADDRESS

        def get_order(item):
            collection = {
                'nftAddress': item['erc721TokenAddress'].lower(),
                'items': [],
                'isBasic': True
            }

            obj = {
                'erc20TokenAmount': int(item['paymentTokenAmount']),
                'nftId': int(item['erc721TokenId'])
            }
            collection['items'].append(obj)

            if collection['isBasic']:
                if 10 ** 50 < int(obj['erc20TokenAmount']) or 10 ** 18 < int(obj['nftId']):
                    collection['isBasic'] = False

            order = {
                'basicCollections': [],
                'collections': [],
                'itemCount': 0
            }

            collection_new = {
                'nftAddress': collection['nftAddress'],
                'platformFee': 0,
                'royaltyFeeRecipient': NULL_ADDRESS,
                'royaltyFee': 0,
                'items': []
            }

            if collection['isBasic']:
                order['basicCollections'].append(collection_new)
            else:
                order['collections'].append(collection_new)

            order['itemCount'] += 1

            if collection['isBasic']:
                collection_new['items'].append(item)
            else:
                collection_new['items'].append(obj)

            return order

        def set_collection_fees(collections, fee):
            for collection in collections:
                if fee:
                    if fee['protocolFeeAddress'] and fee['protocolFeeAddress'].lower() != NULL_ADDRESS:
                        collection['platformFee'] = fee.get('protocolFeePoints', 0)
                    if fee['royaltyFeeInfos'][0]['royaltyFeeAddress'] and fee['royaltyFeeInfos'][0][
                        'royaltyFeeAddress'].lower() != NULL_ADDRESS:
                        collection['royaltyFee'] = int(fee['royaltyFeeInfos'][0]['royaltyFeePoints'])
                        collection['royaltyFeeRecipient'] = fee['royaltyFeeInfos'][0]['royaltyFeeAddress'].lower()

        def create_order(params, account, counter=None):
            fees = self.get_fees(account.address, params['erc721TokenAddress'], params['erc721TokenId'])[0]
            platformFeeRecipient = self.get_platform_fees(fees)
            maker = account.address
            paymentToken = to_standart_erc20_token(params['paymentToken'])
            listingTime, expirationTime = int(time.time() - 60), int(time.time() + 60 * 60 * 24 * 30)

            #hashNonce = counter if counter is not None else self.contract.functions.getHashNonce(self.w3.to_checksum_address(maker)).call()
            order = get_order(params)
            nonce = self.get_maker_nonce(auth, account)
            set_collection_fees(order['basicCollections'], fees)
            set_collection_fees(order['collections'], fees)
            order_ = {
                'exchange': self.contract.address,
                'maker': maker,
                'listingTime': listingTime,
                'expirationTime': expirationTime,
                'startNonce': nonce,
                'paymentToken': paymentToken,
                'platformFeeRecipient': platformFeeRecipient,
                'basicCollections': order['basicCollections'],
                'collections': order['collections'],
                'hashNonce': str(0), #str(hashNonce)
                'chain': 8453
            }
            return order_

        def to_standard_order(order):
            return {
                "maker": order["maker"],
                "listingTime": order["listingTime"],
                "expiryTime": order["expirationTime"],
                "startNonce": int(order["startNonce"]),
                "erc20Token": '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
                "platformFeeRecipient": order["platformFeeRecipient"],
                "basicCollections": to_standard_basic_collections(order),
                "collections": to_standard_collections(order),
                "hashNonce": int(order["hashNonce"])
            }

        def post_order(order, signed_message, message, address, auth):
            basic_collection = order['basicCollections']
            collections = order['collections']
            if basic_collection:
                basic_collection[0]['items'] = [{"erc20TokenAmount": str(basic_collection[0]['items'][0]['paymentTokenAmount']),'nftId': str(basic_collection[0]['items'][0]['erc721TokenId'])}]
            if collections:
                collections[0]['items'] = [{"erc20TokenAmount": str(collections[0]['items'][0]['erc20TokenAmount']), "nftId": str(collections[0]['items'][0]['nftId'])}]
            payload = {"listingTime": message['message']['listingTime'],
                       "expirationTime": message['message']['expiryTime'],
                       "paymentToken": "0x0000000000000000000000000000000000000000",
                       "platformFeeRecipient": order['platformFeeRecipient'],
                       "basicCollections": basic_collection, "collections": collections, "chain": "base",
                       "maker": address,
                       "exchange": "0xa39a5f160a1952ddf38781bd76e402b0006912a9", "startNonce": int(order["startNonce"]),
                       "hashNonce": order["hashNonce"], "hash": signed_message['messageHash'].hex(),
                       "v": signed_message['v'],
                       "r": self.w3.to_hex(signed_message['r']), "s": self.w3.to_hex(signed_message['s'])}
            res = self.help.fetch_tls(session=self.session, url='https://api.element.market/v3/orders/postBatch', type='post', payload=payload, headers=self.get_headers(auth=auth))
            return res

        item = self.get_nft(auth, account)
        if not item:
            return self.list_nft(private_key, attempt=attempt + 4)

        try:
            price = float(item['assetEventData']['lastSale']['lastSalePrice'])
            price = round(price * random.uniform(2, 5), 6)
        except:
            price = round(random.uniform(1.5, 5) * 0.1, 6)
        contract = item['contractAddress']
        token_id = item['tokenId']
        type = item['tokenType']

        if type.lower() != "ERC721".lower():
            return self.list_nft(private_key, attempt=attempt+2)

        price = self.w3.to_wei(price, 'ether')

        params = {
            'erc721TokenAddress': contract,
            'erc721TokenId': token_id,
            'paymentTokenAmount': price,
            'paymentToken': NULL_ADDRESS,
        }

        approve = check_approve(new_w3, account, contract, markets_data[self.project]['approve_contract'], nft=True)
        if not approve:
            make_approve(new_w3, account, contract, markets_data[self.project]['approve_contract'], nft=True)

        order = create_order(params, account)
        message = {
            'types': markets_data['ELEMENT']['listing']['types'],
            'domain': markets_data['ELEMENT']['listing']['domain'],
            'primaryType': markets_data['ELEMENT']['listing']['primaryType'],
            'message': to_standard_order(order)
        }

        encoded_message = encode_structured_data(message)
        signed_message = Account.sign_message(encoded_message, account._private_key.hex())

        result = post_order(order, signed_message, message, account.address, auth)
        try:
            if result['data']['successList'] is not None:
                self.logger.log_success(f"{self.project} | Успешно залистил NFT ({item['collection']['name']} #{item['tokenId']}) за {round(price / 10 ** 18, 6)} ETH", wallet=account.address)
                return True
            elif result['data']['successList'] is None and result['data']['failList'] is None:
                return 'error'
            else:
                return 'error'
        except:
            return 'error'

class Opensea():

    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'OPENSEA'
        self.logger = logger
        self.os_codes = {
            "authLoginMutation": '856ed51d371b833d93a6d0dcf69be76ffc010d88dc7d2980466f178a77a8c28b',
            "challengeLoginMessageQuery": '05649d324b3f3db988d5065ea33599bca390adf00e3f46952dd59ff5cc61e1e0',
            "RankingsPageTrendingQuery": '82e3e1549c27ae11258aecbe7ca0144fa9c7f4c793f2efb02e113b1f165d5fb9',
            "CollectionAssetSearchListQuery": '642c6474ecd06e22676ea678fa721c85bb1e9feb9dfc7e691a8300183f25b647',
            "FulfillActionModalQuery": 'f06d6357e2c153142ccd8e0d3ad35872522bfe9d1fa818137208e01b22f7602b',
            "useHandleBlockchainActionsCreateOrderMutation": '18153293ebaa96627ccfdf9b29fbaa92539438162b8b61add8feef6f0eb321d5',
            "AssetSellPageQuery": '373428b700e52dea14d194d667673e430ba62c8b1922a5687cecaff70789b29c',
            "AccountCollectedAssetSearchListQuery": '487ab8a857d60b3e546c98612a657cbb35e67db054e59b58d2deaa9326b53e69',
            "CreateListingActionModalQuery": 'd2434da5e36eafbc126f332a59e09568b7f66b1a28adddf6bcca76267f1424ac',
        }

    def get_headers(self, account, operation=None, auth=None):
        headers = {
            'authority': 'opensea.io',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://opensea.io',
            'referer': 'https://opensea.io/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'x-app-id': 'opensea-web',
            'x-build-id': 'b82583d5d20f76d6f591fb08e369371931819542',
            'x-signed-query': self.os_codes[operation],
            'x-viewer-address': account.address,
        }
        if auth:
            headers['authorization'] = f'JWT {auth}'
        return headers

    def get_auth(self, account, session):
        for i in range(5):
            try:
                json_data = {
                    'id': 'challengeLoginMessageQuery',
                    'query': 'query challengeLoginMessageQuery(\n  $address: AddressScalar!\n) {\n  auth {\n    loginMessage(address: $address)\n  }\n}\n',
                    'variables': {
                        'address': account.address,
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id']), payload=json_data, session=session)
                message_ = response['data']['auth']['loginMessage']
                message = message_.encode()
                message_to_sign = encode_defunct(primitive=message)
                signed_message = self.w3.eth.account.sign_message(message_to_sign, private_key=account._private_key.hex())
                sig = signed_message.signature.hex()

                json_data = {
                    'id': 'authLoginMutation',
                    'query': 'mutation authLoginMutation(\n  $address: AddressScalar!\n  $message: String!\n  $signature: String!\n  $chain: ChainScalar\n) {\n  auth {\n    webLogin(address: $address, message: $message, signature: $signature, chain: $chain) {\n      token\n      account {\n        address\n        isEmployee\n        moonpayKycStatus\n        moonpayKycRejectType\n        id\n      }\n    }\n  }\n}\n',
                    'variables': {
                        'address': account.address.lower(),
                        'message': message_,
                        'signature': sig,
                        'chain': 'BASE',
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id']), payload=json_data, session=session)

                return response['data']['auth']['webLogin']['token']
            except:
                time.sleep(i*1)
        return None

    def get_collections(self, account, auth, session):
        for i in range(5):
            try:
                json_data = {
                    'id': 'RankingsPageTrendingQuery',
                    'query': 'query RankingsPageTrendingQuery(\n  $chain: [ChainScalar!]\n  $count: Int!\n  $cursor: String\n  $categories: [CategoryV2Slug!]!\n  $eligibleCount: Int!\n  $trendingCollectionsSortBy: TrendingCollectionSort\n  $timeWindow: StatsTimeWindow\n) {\n  ...RankingsPageTrending_data\n}\n\nfragment RankingsPageTrending_data on Query {\n  trendingCollectionsByCategory(after: $cursor, chains: $chain, first: $count, sortBy: $trendingCollectionsSortBy, categories: $categories, topCollectionLimit: $eligibleCount) {\n    edges {\n      node {\n        createdDate\n        name\n        slug\n        logo\n        isVerified\n        relayId\n        ...StatsCollectionCell_collection\n        ...collection_url\n        statsV2 {\n          totalQuantity\n        }\n        windowCollectionStats(statsTimeWindow: $timeWindow) {\n          floorPrice {\n            unit\n            eth\n            symbol\n          }\n          numOwners\n          totalSupply\n          totalListed\n          numOfSales\n          volumeChange\n          volume {\n            unit\n            eth\n            symbol\n          }\n        }\n        id\n        __typename\n      }\n      cursor\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nfragment StatsCollectionCell_collection on CollectionType {\n  name\n  imageUrl\n  isVerified\n  slug\n}\n\nfragment collection_url on CollectionType {\n  slug\n  isCategory\n}\n',
                    'variables': {
                        'chain': [
                            'BASE',
                        ],
                        'count': 250,
                        'cursor': None,
                        'categories': [],
                        'eligibleCount': 500,
                        'trendingCollectionsSortBy': 'ONE_DAY_SALES',
                        'timeWindow': 'ONE_DAY',
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id'], auth=auth), payload=json_data,  session=session)
                collections = []
                for col in response['data']['trendingCollectionsByCategory']['edges']:
                    col = col['node']
                    if int(col['windowCollectionStats']['totalListed']) > 0 and float(col['windowCollectionStats']['floorPrice']['eth']) <= self.max_price:
                        collections.append(col)
                return collections
            except:
                time.sleep(i*1)
        return []

    def get_nfts(self, account, auth, session, collection):
        for i in range(5):
            try:
                json_data = {
                    'id': 'CollectionAssetSearchListQuery',
                    'query': 'query CollectionAssetSearchListQuery(\n  $collections: [CollectionSlug!]!\n  $count: Int!\n  $numericTraits: [TraitRangeType!]\n  $paymentAssets: [PaymentAssetSymbol]\n  $priceFilter: PriceFilterType\n  $query: String\n  $rarityFilter: RarityFilterType\n  $resultModel: SearchResultModel\n  $sortAscending: Boolean\n  $sortBy: SearchSortBy\n  $stringTraits: [TraitInputType!]\n  $toggles: [SearchToggle!]\n  $shouldShowBestBid: Boolean!\n  $owner: IdentityInputType\n  $filterOutListingsWithoutRequestedCreatorFees: Boolean\n) {\n  ...CollectionAssetSearchListPagination_data_1eC64m\n}\n\nfragment AccountLink_data on AccountType {\n  address\n  config\n  isCompromised\n  user {\n    publicUsername\n    id\n  }\n  displayName\n  ...ProfileImage_data\n  ...wallet_accountKey\n  ...accounts_url\n}\n\nfragment AddToCartAndQuickBuyButton_order on OrderV2Type {\n  ...useIsQuickBuyEnabled_order\n  ...ItemAddToCartButton_order\n  ...QuickBuyButton_order\n}\n\nfragment AssetContextMenu_data on AssetType {\n  relayId\n}\n\nfragment AssetMediaAnimation_asset on AssetType {\n  ...AssetMediaImage_asset\n  ...AssetMediaContainer_asset\n  ...AssetMediaPlaceholderImage_asset\n}\n\nfragment AssetMediaAudio_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaContainer_asset on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_1LNk0S on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_4a3mm5 on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  defaultRarityData {\n    ...RarityIndicator_data\n    id\n  }\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaEditions_asset_1mZMwQ on AssetType {\n  decimals\n}\n\nfragment AssetMediaImage_asset on AssetType {\n  backgroundColor\n  imageUrl\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaPlaceholderImage_asset on AssetType {\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaVideo_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaWebgl_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMedia_asset on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_1LNk0S\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetMedia_asset_1mZMwQ on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_1LNk0S\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetMedia_asset_5MxNd on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_4a3mm5\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetQuantity_data on AssetQuantityType {\n  asset {\n    ...Price_data\n    id\n  }\n  quantity\n}\n\nfragment AssetSearchListViewTableAssetInfo_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ...PortfolioTableItemCellTooltip_item\n}\n\nfragment AssetSearchListViewTableQuickBuy_order on OrderV2Type {\n  maker {\n    address\n    id\n  }\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    ...itemEvents_dataV2\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  openedAt\n  relayId\n}\n\nfragment AssetSearchList_data_4hkUTB on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ...ItemCard_data_1kHswz\n  ... on AssetType {\n    collection {\n      isVerified\n      relayId\n      id\n    }\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      isVerified\n      relayId\n      id\n    }\n  }\n  chain {\n    identifier\n  }\n  ...useAssetSelectionStorage_item_3j1bgC\n}\n\nfragment BulkPurchaseModal_orders on OrderV2Type {\n  relayId\n  item {\n    __typename\n    relayId\n    chain {\n      identifier\n    }\n    ... on AssetType {\n      collection {\n        slug\n        isSafelisted\n        id\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  payment {\n    relayId\n    symbol\n    id\n  }\n  ...useTotalPrice_orders\n  ...useFulfillingListingsWillReactivateOrders_orders\n}\n\nfragment CancelItemOrdersButton_items on ItemType {\n  __isItemType: __typename\n  __typename\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    relayId\n  }\n  ... on AssetBundleType {\n    relayId\n  }\n  ...CancelOrdersConfirmationModal_items\n}\n\nfragment CancelOrdersConfirmationModal_items on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...StackedAssetMedia_assets\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment CollectionAssetSearchListPagination_data_1eC64m on Query {\n  queriedAt\n  collectionItems(first: $count, collections: $collections, numericTraits: $numericTraits, paymentAssets: $paymentAssets, priceFilter: $priceFilter, querystring: $query, rarityFilter: $rarityFilter, resultType: $resultModel, sortAscending: $sortAscending, sortBy: $sortBy, stringTraits: $stringTraits, toggles: $toggles, owner: $owner, prioritizeBuyNow: true, filterOutListingsWithoutRequestedCreatorFees: $filterOutListingsWithoutRequestedCreatorFees) {\n    edges {\n      node {\n        __typename\n        ...readItemHasBestAsk_item\n        ...AssetSearchList_data_4hkUTB\n        ...useGetEligibleItemsForSweep_items\n        ... on Node {\n          __isNode: __typename\n          id\n        }\n      }\n      cursor\n    }\n    totalCount\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nfragment CollectionLink_assetContract on AssetContractType {\n  address\n  blockExplorerLink\n}\n\nfragment CollectionLink_collection on CollectionType {\n  name\n  slug\n  verificationStatus\n  ...collection_url\n}\n\nfragment CollectionTrackingContext_collection on CollectionType {\n  relayId\n  slug\n  isVerified\n  isCollectionOffersEnabled\n  defaultChain {\n    identifier\n  }\n}\n\nfragment CreateListingButton_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...CreateQuickSingleListingFlowModal_asset\n  }\n  ...itemEvents_dataV2\n  ...item_sellUrl\n}\n\nfragment CreateQuickSingleListingFlowModal_asset on AssetType {\n  relayId\n  chain {\n    identifier\n  }\n  ...itemEvents_dataV2\n}\n\nfragment EditListingButton_item on ItemType {\n  __isItemType: __typename\n  chain {\n    identifier\n  }\n  ...EditListingModal_item\n  ...itemEvents_dataV2\n}\n\nfragment EditListingButton_listing on OrderV2Type {\n  ...EditListingModal_listing\n}\n\nfragment EditListingModal_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    tokenId\n    assetContract {\n      address\n      id\n    }\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment EditListingModal_listing on OrderV2Type {\n  relayId\n}\n\nfragment ItemAddToCartButton_order on OrderV2Type {\n  maker {\n    address\n    id\n  }\n  taker {\n    address\n    id\n  }\n  item {\n    __typename\n    ... on AssetType {\n      isCurrentlyFungible\n    }\n    ...itemEvents_dataV2\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  openedAt\n  ...ShoppingCartContextProvider_inline_order\n}\n\nfragment ItemCardContent on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    relayId\n    name\n    ...AssetMedia_asset_1mZMwQ\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            relayId\n            ...AssetMedia_asset\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment ItemCardContent_1mZMwQ on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    relayId\n    name\n    ...AssetMedia_asset_1mZMwQ\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            relayId\n            ...AssetMedia_asset\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment ItemCardCta_item_2qvZ6X on ItemType {\n  __isItemType: __typename\n  __typename\n  orderData {\n    bestAskV2 {\n      ...AddToCartAndQuickBuyButton_order\n      ...EditListingButton_listing\n      ...QuickBuyButton_order\n      id\n    }\n  }\n  ...useItemCardCta_item_2qvZ6X\n  ...itemEvents_dataV2\n  ...CreateListingButton_item\n  ...EditListingButton_item\n}\n\nfragment ItemCardFooter_EmmWh on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  name\n  orderData {\n    bestBidV2 {\n      orderType\n      priceType {\n        unit\n      }\n      ...ItemCardPrice_data\n      id\n    }\n    bestAskV2 {\n      ...ItemCardFooter_bestAskV2\n      id\n    }\n  }\n  ...ItemMetadata_4xFTFU\n  ... on AssetType {\n    tokenId\n    isDelisted\n    defaultRarityData {\n      ...RarityIndicator_data\n      id\n    }\n    collection {\n      slug\n      name\n      isVerified\n      ...collection_url\n      ...useIsRarityEnabled_collection\n      id\n    }\n    largestOwner {\n      owner {\n        ...AccountLink_data\n        id\n      }\n      id\n    }\n    ...AssetSearchListViewTableAssetInfo_item\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      slug\n      name\n      isVerified\n      ...collection_url\n      ...useIsRarityEnabled_collection\n      id\n    }\n  }\n  ...useItemCardCta_item_2qvZ6X\n  ...item_url\n  ...ItemCardContent\n}\n\nfragment ItemCardFooter_bestAskV2 on OrderV2Type {\n  orderType\n  priceType {\n    unit\n  }\n  maker {\n    address\n    id\n  }\n  ...ItemCardPrice_data\n  ...ItemAddToCartButton_order\n  ...AssetSearchListViewTableQuickBuy_order\n  ...useIsQuickBuyEnabled_order\n}\n\nfragment ItemCardPrice_data on OrderV2Type {\n  perUnitPriceType {\n    unit\n  }\n  payment {\n    symbol\n    id\n  }\n  ...useIsQuickBuyEnabled_order\n}\n\nfragment ItemCard_data_1kHswz on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  chain {\n    identifier\n  }\n  orderData {\n    bestAskV2 {\n      priceType {\n        eth\n      }\n      id\n    }\n  }\n  ... on AssetType {\n    isDelisted\n    totalQuantity\n    collection {\n      slug\n      ...CollectionTrackingContext_collection\n      id\n    }\n    ...itemEvents_data\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      slug\n      ...CollectionTrackingContext_collection\n      id\n    }\n  }\n  ...ItemCardContent_1mZMwQ\n  ...ItemCardFooter_EmmWh\n  ...ItemCardCta_item_2qvZ6X\n  ...item_url\n  ...ItemTrackingContext_item\n}\n\nfragment ItemMetadata_4xFTFU on ItemType {\n  __isItemType: __typename\n  __typename\n  orderData {\n    bestAskV2 {\n      openedAt\n      createdDate\n      closedAt\n      id\n    }\n  }\n  assetEventData {\n    lastSale {\n      unitPriceQuantity {\n        ...AssetQuantity_data\n        quantity\n        asset {\n          symbol\n          decimals\n          id\n        }\n        id\n      }\n    }\n  }\n  ... on AssetType {\n    bestAllTypeBid @include(if: $shouldShowBestBid) {\n      perUnitPriceType {\n        unit\n        symbol\n      }\n      id\n    }\n    mintEvent @include(if: $shouldShowBestBid) {\n      perUnitPrice {\n        unit\n        symbol\n      }\n      id\n    }\n  }\n}\n\nfragment ItemTrackingContext_item on ItemType {\n  __isItemType: __typename\n  relayId\n  verificationStatus\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    tokenId\n    isReportedSuspicious\n    assetContract {\n      address\n      id\n    }\n  }\n  ... on AssetBundleType {\n    slug\n  }\n}\n\nfragment OrderListItem_order on OrderV2Type {\n  relayId\n  makerOwnedQuantity\n  item {\n    __typename\n    displayName\n    ... on AssetType {\n      assetContract {\n        ...CollectionLink_assetContract\n        id\n      }\n      collection {\n        ...CollectionLink_collection\n        id\n      }\n      ...AssetMedia_asset\n      ...asset_url\n      ...useItemFees_item\n    }\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              displayName\n              relayId\n              assetContract {\n                ...CollectionLink_assetContract\n                id\n              }\n              collection {\n                ...CollectionLink_collection\n                id\n              }\n              ...StackedAssetMedia_assets\n              ...AssetMedia_asset\n              ...asset_url\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ...itemEvents_dataV2\n    ...useIsItemSafelisted_item\n    ...ItemTrackingContext_item\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  remainingQuantityType\n  ...OrderPrice\n}\n\nfragment OrderList_orders on OrderV2Type {\n  item {\n    __typename\n    ... on AssetType {\n      __typename\n      relayId\n    }\n    ... on AssetBundleType {\n      __typename\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  relayId\n  ...OrderListItem_order\n  ...useFulfillingListingsWillReactivateOrders_orders\n}\n\nfragment OrderPrice on OrderV2Type {\n  priceType {\n    unit\n  }\n  perUnitPriceType {\n    unit\n  }\n  payment {\n    ...TokenPricePayment\n    id\n  }\n}\n\nfragment PortfolioTableItemCellTooltip_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ...AssetMedia_asset_5MxNd\n  ...PortfolioTableTraitTable_asset\n  ...asset_url\n}\n\nfragment PortfolioTableTraitTable_asset on AssetType {\n  assetContract {\n    address\n    chain\n    id\n  }\n  isCurrentlyFungible\n  tokenId\n}\n\nfragment Price_data on AssetType {\n  decimals\n  symbol\n  usdSpotPrice\n}\n\nfragment ProfileImage_data on AccountType {\n  imageUrl\n}\n\nfragment QuickBuyButton_order on OrderV2Type {\n  maker {\n    address\n    id\n  }\n  taker {\n    address\n    ...wallet_accountKey\n    id\n  }\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    ...itemEvents_dataV2\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  openedAt\n  relayId\n}\n\nfragment RarityIndicator_data on RarityDataType {\n  rank\n  rankPercentile\n  rankCount\n  maxRank\n}\n\nfragment ShoppingCartContextProvider_inline_order on OrderV2Type {\n  relayId\n  makerOwnedQuantity\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    relayId\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  maker {\n    relayId\n    id\n  }\n  taker {\n    address\n    ...wallet_accountKey\n    id\n  }\n  priceType {\n    usd\n  }\n  payment {\n    relayId\n    id\n  }\n  remainingQuantityType\n  ...useTotalItems_orders\n  ...ShoppingCart_orders\n}\n\nfragment ShoppingCartDetailedView_orders on OrderV2Type {\n  relayId\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  supportsGiftingOnPurchase\n  ...useTotalPrice_orders\n  ...OrderList_orders\n}\n\nfragment ShoppingCart_orders on OrderV2Type {\n  ...ShoppingCartDetailedView_orders\n  ...BulkPurchaseModal_orders\n}\n\nfragment StackedAssetMedia_assets on AssetType {\n  relayId\n  ...AssetMedia_asset\n  collection {\n    logo\n    id\n  }\n}\n\nfragment SweepContextProvider_items on ItemType {\n  __isItemType: __typename\n  relayId\n  orderData {\n    bestAskV2 {\n      relayId\n      payment {\n        symbol\n        id\n      }\n      perUnitPriceType {\n        unit\n      }\n      ...BulkPurchaseModal_orders\n      ...useTotalPrice_orders\n      id\n    }\n  }\n}\n\nfragment TokenPricePayment on PaymentAssetType {\n  symbol\n}\n\nfragment accounts_url on AccountType {\n  address\n  user {\n    publicUsername\n    id\n  }\n}\n\nfragment asset_url on AssetType {\n  assetContract {\n    address\n    id\n  }\n  tokenId\n  chain {\n    identifier\n  }\n}\n\nfragment bundle_url on AssetBundleType {\n  slug\n  chain {\n    identifier\n  }\n}\n\nfragment collection_url on CollectionType {\n  slug\n  isCategory\n}\n\nfragment itemEvents_data on AssetType {\n  relayId\n  assetContract {\n    address\n    id\n  }\n  tokenId\n  chain {\n    identifier\n  }\n}\n\nfragment itemEvents_dataV2 on ItemType {\n  __isItemType: __typename\n  relayId\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    tokenId\n    assetContract {\n      address\n      id\n    }\n  }\n}\n\nfragment item_sellUrl on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...asset_url\n  }\n  ... on AssetBundleType {\n    slug\n    chain {\n      identifier\n    }\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            relayId\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment item_url on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...asset_url\n  }\n  ... on AssetBundleType {\n    ...bundle_url\n  }\n}\n\nfragment readItemHasBestAsk_item on ItemType {\n  __isItemType: __typename\n  orderData {\n    bestAskV2 {\n      __typename\n      id\n    }\n  }\n}\n\nfragment useAssetSelectionStorage_item_3j1bgC on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  chain {\n    identifier\n    isTradingEnabled\n  }\n  ... on AssetType {\n    bestAllTypeBid @include(if: $shouldShowBestBid) {\n      relayId\n      id\n    }\n    ...asset_url\n    isCompromised\n  }\n  ... on AssetBundleType {\n    orderData {\n      bestBidV2 @include(if: $shouldShowBestBid) {\n        relayId\n        id\n      }\n    }\n  }\n  ...item_sellUrl\n  ...AssetContextMenu_data\n  ...CancelItemOrdersButton_items\n}\n\nfragment useFulfillingListingsWillReactivateOrders_orders on OrderV2Type {\n  ...useTotalItems_orders\n}\n\nfragment useGetEligibleItemsForSweep_items on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  chain {\n    identifier\n  }\n  orderData {\n    bestAskV2 {\n      relayId\n      orderType\n      maker {\n        address\n        id\n      }\n      perUnitPriceType {\n        usd\n        unit\n        symbol\n      }\n      payment {\n        relayId\n        symbol\n        usdPrice\n        id\n      }\n      id\n    }\n  }\n  ...SweepContextProvider_items\n}\n\nfragment useIsItemSafelisted_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    collection {\n      slug\n      verificationStatus\n      id\n    }\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 30) {\n      edges {\n        node {\n          asset {\n            collection {\n              slug\n              verificationStatus\n              id\n            }\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment useIsQuickBuyEnabled_order on OrderV2Type {\n  orderType\n  item {\n    __typename\n    ... on AssetType {\n      isCurrentlyFungible\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment useIsRarityEnabled_collection on CollectionType {\n  slug\n  enabledRarities\n}\n\nfragment useItemCardCta_item_2qvZ6X on ItemType {\n  __isItemType: __typename\n  __typename\n  chain {\n    identifier\n    isTradingEnabled\n  }\n  orderData {\n    bestAskV2 {\n      orderType\n      maker {\n        address\n        id\n      }\n      id\n    }\n  }\n  ... on AssetType {\n    isDelisted\n    isListable\n    isCurrentlyFungible\n  }\n}\n\nfragment useItemFees_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    totalCreatorFee\n    collection {\n      openseaSellerFeeBasisPoints\n      isCreatorFeesEnforced\n      id\n    }\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      openseaSellerFeeBasisPoints\n      totalCreatorFeeBasisPoints\n      isCreatorFeesEnforced\n      id\n    }\n  }\n}\n\nfragment useTotalItems_orders on OrderV2Type {\n  item {\n    __typename\n    relayId\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment useTotalPrice_orders on OrderV2Type {\n  relayId\n  perUnitPriceType {\n    usd\n    unit\n  }\n  payment {\n    symbol\n    ...TokenPricePayment\n    id\n  }\n}\n\nfragment wallet_accountKey on AccountType {\n  address\n}\n',
                    'variables': {
                        'collections': [
                            collection,
                        ],
                        'count': 10,
                        'numericTraits': None,
                        'paymentAssets': None,
                        'priceFilter': None,
                        'query': None,
                        'rarityFilter': None,
                        'resultModel': 'ASSETS',
                        'sortAscending': True,
                        'sortBy': 'UNIT_PRICE',
                        'stringTraits': None,
                        'toggles': [
                            'IS_LISTED',
                        ],
                        'shouldShowBestBid': False,
                        'owner': None,
                        'filterOutListingsWithoutRequestedCreatorFees': None,
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id'], auth=auth), payload=json_data, session=session)
                nfts = []
                for nft in response['data']['collectionItems']['edges']:
                    nft = nft['node']
                    if float(nft['orderData']['bestAskV2']['priceType']['eth']) <= self.max_price:
                        nfts.append(nft)
                return random.choice(nfts)
            except:
                time.sleep(i * 1)
        return None

    def get_buy_data(self, account, auth, session, nft_order):

        for i in range(5):
            try:
                json_data = {
                    'id': 'FulfillActionModalQuery',
                    'query': 'query FulfillActionModalQuery(\n  $orderId: OrderRelayID!\n  $itemFillAmount: BigNumberScalar!\n  $takerAssetsForCriteria: ArchetypeInputType\n  $giftRecipientAddress: AddressScalar\n  $optionalCreatorFeeBasisPoints: Int\n) {\n  order(order: $orderId) {\n    relayId\n    side\n    fulfill(itemFillAmount: $itemFillAmount, takerAssetsForCriteria: $takerAssetsForCriteria, giftRecipientAddress: $giftRecipientAddress, optionalCreatorFeeBasisPoints: $optionalCreatorFeeBasisPoints) {\n      actions {\n        __typename\n        ... on FulfillOrderActionType {\n          giftRecipientAddress\n        }\n        ...BlockchainActionList_data\n      }\n    }\n    id\n  }\n}\n\nfragment AskForDepositAction_data on AskForDepositType {\n  asset {\n    chain {\n      identifier\n    }\n    decimals\n    symbol\n    usdSpotPrice\n    id\n  }\n  minQuantity\n}\n\nfragment AskForSwapAction_data on AskForSwapType {\n  __typename\n  fromAsset {\n    chain {\n      identifier\n    }\n    decimals\n    symbol\n    id\n  }\n  toAsset {\n    chain {\n      identifier\n    }\n    symbol\n    id\n  }\n  minQuantity\n  maxQuantity\n  ...useHandleBlockchainActions_ask_for_asset_swap\n}\n\nfragment AssetApprovalAction_data on AssetApprovalActionType {\n  __typename\n  asset {\n    chain {\n      identifier\n    }\n    ...StackedAssetMedia_assets\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    collection {\n      __typename\n      ...CollectionLink_collection\n      id\n    }\n    id\n  }\n  ...useHandleBlockchainActions_approve_asset\n}\n\nfragment AssetBurnToRedeemAction_data on AssetBurnToRedeemActionType {\n  __typename\n  ...useHandleBlockchainActions_burnToRedeem\n  asset {\n    chain {\n      identifier\n    }\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    collection {\n      __typename\n      ...CollectionLink_collection\n      id\n    }\n    displayName\n    ...StackedAssetMedia_assets\n    id\n  }\n}\n\nfragment AssetFreezeMetadataAction_data on AssetFreezeMetadataActionType {\n  __typename\n  ...useHandleBlockchainActions_freeze_asset_metadata\n}\n\nfragment AssetItem_asset on AssetType {\n  chain {\n    identifier\n  }\n  displayName\n  relayId\n  collection {\n    name\n    id\n  }\n  ...StackedAssetMedia_assets\n}\n\nfragment AssetMediaAnimation_asset on AssetType {\n  ...AssetMediaImage_asset\n  ...AssetMediaContainer_asset\n  ...AssetMediaPlaceholderImage_asset\n}\n\nfragment AssetMediaAudio_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaContainer_asset on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_1LNk0S on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaEditions_asset_1mZMwQ on AssetType {\n  decimals\n}\n\nfragment AssetMediaImage_asset on AssetType {\n  backgroundColor\n  imageUrl\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaPlaceholderImage_asset on AssetType {\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaVideo_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaWebgl_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMedia_asset on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_1LNk0S\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetSwapAction_data on AssetSwapActionType {\n  __typename\n  ...useHandleBlockchainActions_swap_asset\n}\n\nfragment AssetTransferAction_data on AssetTransferActionType {\n  __typename\n  ...useHandleBlockchainActions_transfer_asset\n}\n\nfragment BlockchainActionList_data on BlockchainActionType {\n  __isBlockchainActionType: __typename\n  __typename\n  ... on AssetApprovalActionType {\n    ...AssetApprovalAction_data\n  }\n  ... on AskForDepositType {\n    __typename\n    ...AskForDepositAction_data\n  }\n  ... on AskForSwapType {\n    __typename\n    ...AskForSwapAction_data\n  }\n  ... on AssetFreezeMetadataActionType {\n    __typename\n    ...AssetFreezeMetadataAction_data\n  }\n  ... on AssetSwapActionType {\n    __typename\n    ...AssetSwapAction_data\n  }\n  ... on AssetTransferActionType {\n    __typename\n    ...AssetTransferAction_data\n  }\n  ... on CreateOrderActionType {\n    __typename\n    ...CreateOrderAction_data\n  }\n  ... on CreateBulkOrderActionType {\n    __typename\n    ...CreateBulkOrderAction_data\n  }\n  ... on CreateSwapOrderActionType {\n    __typename\n    ...CreateSwapOrderAction_data\n  }\n  ... on CancelOrderActionType {\n    __typename\n    ...CancelOrderAction_data\n  }\n  ... on CancelSwapOrdersActionType {\n    __typename\n    ...CancelSwapOrdersAction_data\n  }\n  ... on FulfillOrderActionType {\n    __typename\n    ...FulfillOrderAction_data\n  }\n  ... on FulfillSwapOrderActionType {\n    __typename\n    ...FulfillSwapOrderAction_data\n  }\n  ... on BulkAcceptOffersActionType {\n    __typename\n    ...BulkAcceptOffersAction_data\n  }\n  ... on BulkFulfillOrdersActionType {\n    __typename\n    ...BulkFulfillOrdersAction_data\n  }\n  ... on PaymentAssetApprovalActionType {\n    __typename\n    ...PaymentAssetApprovalAction_data\n  }\n  ... on MintActionType {\n    __typename\n    ...MintAction_data\n  }\n  ... on DropContractDeployActionType {\n    __typename\n    ...DeployContractAction_data\n  }\n  ... on DropMechanicsUpdateActionType {\n    __typename\n    ...UpdateDropMechanicsAction_data\n  }\n  ... on SetCreatorFeesActionType {\n    __typename\n    ...SetCreatorFeesAction_data\n  }\n  ... on CollectionTokenMetadataUpdateActionType {\n    __typename\n    ...UpdatePreRevealAction_data\n  }\n  ... on AssetBurnToRedeemActionType {\n    __typename\n    ...AssetBurnToRedeemAction_data\n  }\n  ... on MintYourOwnCollectionActionType {\n    __typename\n    ...MintYourOwnCollectionAction_data\n  }\n}\n\nfragment BulkAcceptOffersAction_data on BulkAcceptOffersActionType {\n  __typename\n  maxQuantityToFill\n  offersToAccept {\n    itemFillAmount\n    orderData {\n      chain {\n        identifier\n      }\n      item {\n        __typename\n        ... on AssetQuantityDataType {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n        }\n        ... on AssetBundleType {\n          assetQuantities(first: 30) {\n            edges {\n              node {\n                asset {\n                  ...StackedAssetMedia_assets\n                  id\n                }\n                id\n              }\n            }\n          }\n        }\n        ... on Node {\n          __isNode: __typename\n          id\n        }\n      }\n      ...useTotalItems_ordersData\n    }\n    criteriaAsset {\n      relayId\n      ...StackedAssetMedia_assets\n      id\n    }\n    ...useTotalPriceOfferDataToAccept_offersToAccept\n    ...readOfferDataToAcceptPrice_offerToAccept\n  }\n  ...useHandleBlockchainActions_bulk_accept_offers\n}\n\nfragment BulkFulfillOrdersAction_data on BulkFulfillOrdersActionType {\n  __typename\n  maxOrdersToFill\n  ordersToFill {\n    itemFillAmount\n    orderData {\n      chain {\n        identifier\n      }\n      item {\n        __typename\n        ... on AssetQuantityDataType {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n        }\n        ... on AssetBundleType {\n          assetQuantities(first: 30) {\n            edges {\n              node {\n                asset {\n                  ...StackedAssetMedia_assets\n                  id\n                }\n                id\n              }\n            }\n          }\n        }\n        ... on Node {\n          __isNode: __typename\n          id\n        }\n      }\n      ...useTotalItems_ordersData\n    }\n    ...useTotalPriceOrderDataToFill_ordersToFill\n    ...readOrderDataToFillPrices_orderDataToFill\n  }\n  ...useHandleBlockchainActions_bulk_fulfill_orders\n}\n\nfragment CancelOrderActionGaslessContent_action on CancelOrderActionType {\n  ordersData {\n    side\n    orderType\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        asset {\n          displayName\n          ...StackedAssetMedia_assets\n          id\n        }\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    price {\n      unit\n      symbol\n    }\n    orderCriteria {\n      collection {\n        name\n        representativeAsset {\n          ...StackedAssetMedia_assets\n          id\n        }\n        id\n      }\n    }\n  }\n}\n\nfragment CancelOrderActionOnChainContent_action on CancelOrderActionType {\n  ordersData {\n    side\n    orderType\n    ...OrderDataHeader_order\n    ...OrdersHeaderData_orders\n  }\n}\n\nfragment CancelOrderAction_data on CancelOrderActionType {\n  __typename\n  ordersData {\n    orderType\n    side\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        asset {\n          ...GaslessCancellationProcessingModal_items\n          ...GaslessCancellationFailedModal_items\n          id\n        }\n        quantity\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    orderCriteria {\n      collection {\n        representativeAsset {\n          ...GaslessCancellationProcessingModal_items\n          ...GaslessCancellationFailedModal_items\n          id\n        }\n        id\n      }\n      quantity\n    }\n  }\n  method {\n    __typename\n  }\n  ...CancelOrderActionOnChainContent_action\n  ...useHandleBlockchainActions_cancel_orders\n  ...CancelOrderActionGaslessContent_action\n}\n\nfragment CancelSwapOrdersAction_data on CancelSwapOrdersActionType {\n  __typename\n  swapsData {\n    ...SwapDataHeader_swap\n  }\n  ...useHandleBlockchainActions_cancel_swap_orders\n}\n\nfragment CollectionLink_assetContract on AssetContractType {\n  address\n  blockExplorerLink\n}\n\nfragment CollectionLink_collection on CollectionType {\n  name\n  slug\n  verificationStatus\n  ...collection_url\n}\n\nfragment CollectionOfferDetails_collection on CollectionType {\n  representativeAsset {\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    ...StackedAssetMedia_assets\n    id\n  }\n  ...CollectionLink_collection\n}\n\nfragment ConfirmationItem_asset on AssetType {\n  chain {\n    displayName\n  }\n  ...AssetItem_asset\n}\n\nfragment ConfirmationItem_asset_item_payment_asset on PaymentAssetType {\n  ...ConfirmationItem_extra_payment_asset\n}\n\nfragment ConfirmationItem_assets on AssetType {\n  ...ConfirmationItem_asset\n}\n\nfragment ConfirmationItem_extra_payment_asset on PaymentAssetType {\n  symbol\n  usdSpotPrice\n}\n\nfragment ConfirmationItem_payment_asset on PaymentAssetType {\n  ...ConfirmationItem_asset_item_payment_asset\n}\n\nfragment CreateBulkOrderAction_data on CreateBulkOrderActionType {\n  __typename\n  orderDatas {\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        asset {\n          ...StackedAssetMedia_assets\n          id\n        }\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    ...useTotalItems_ordersData\n    ...useTotalPriceOrderData_orderData\n  }\n  ...useHandleBlockchainActions_create_bulk_order\n}\n\nfragment CreateOrderAction_data on CreateOrderActionType {\n  __typename\n  orderData {\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        quantity\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    side\n    isCounterOrder\n    perUnitPrice {\n      unit\n      symbol\n    }\n    ...OrderDataHeader_order\n  }\n  ...useHandleBlockchainActions_create_order\n}\n\nfragment CreateSwapOrderAction_data on CreateSwapOrderActionType {\n  __typename\n  swapData {\n    ...SwapDataHeader_swap\n  }\n  ...useHandleBlockchainActions_create_swap_order\n}\n\nfragment DeployContractAction_data on DropContractDeployActionType {\n  __typename\n  ...useHandleBlockchainActions_deploy_contract\n}\n\nfragment FulfillOrderAction_data on FulfillOrderActionType {\n  __typename\n  orderData {\n    side\n    ...OrderDataHeader_order\n  }\n  itemFillAmount\n  criteriaAsset {\n    ...OrderDataHeader_criteriaAsset\n    id\n  }\n  ...useHandleBlockchainActions_fulfill_order\n}\n\nfragment FulfillSwapOrderAction_data on FulfillSwapOrderActionType {\n  __typename\n  swapData {\n    ...SwapDataHeader_swap\n  }\n  ...useHandleBlockchainActions_fulfill_swap_order\n}\n\nfragment GaslessCancellationFailedModal_items on ItemType {\n  __isItemType: __typename\n  ...StackedAssetMedia_assets\n}\n\nfragment GaslessCancellationProcessingModal_items on ItemType {\n  __isItemType: __typename\n  ...StackedAssetMedia_assets\n}\n\nfragment MintAction_data on MintActionType {\n  __typename\n  ...useHandleBlockchainActions_mint_asset\n}\n\nfragment MintYourOwnCollectionAction_data on MintYourOwnCollectionActionType {\n  __typename\n  ...useHandleBlockchainActions_mint_your_own_collection\n}\n\nfragment OrderDataHeader_criteriaAsset on AssetType {\n  ...ConfirmationItem_assets\n}\n\nfragment OrderDataHeader_order on OrderDataType {\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      asset {\n        ...ConfirmationItem_assets\n        id\n      }\n      quantity\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  recipient {\n    address\n    id\n  }\n  side\n  openedAt\n  closedAt\n  perUnitPrice {\n    unit\n  }\n  price {\n    unit\n    symbol\n    usd\n  }\n  payment {\n    ...ConfirmationItem_payment_asset\n    id\n  }\n  englishAuctionReservePrice {\n    unit\n  }\n  isCounterOrder\n  orderCriteria {\n    collection {\n      ...CollectionOfferDetails_collection\n      id\n    }\n    trait {\n      traitType\n      value\n      id\n    }\n    quantity\n  }\n}\n\nfragment OrdersHeaderData_orders on OrderDataType {\n  chain {\n    identifier\n  }\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      asset {\n        ...StackedAssetMedia_assets\n        id\n      }\n    }\n    ... on AssetBundleType {\n      assetQuantities(first: 20) {\n        edges {\n          node {\n            asset {\n              ...StackedAssetMedia_assets\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on AssetBundleToBeCreatedType {\n      assetQuantitiesToBeCreated: assetQuantities {\n        asset {\n          ...StackedAssetMedia_assets\n          id\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  orderCriteria {\n    collection {\n      representativeAsset {\n        ...StackedAssetMedia_assets\n        id\n      }\n      id\n    }\n  }\n  orderType\n  side\n}\n\nfragment PaymentAssetApprovalAction_data on PaymentAssetApprovalActionType {\n  __typename\n  asset {\n    chain {\n      identifier\n    }\n    symbol\n    ...StackedAssetMedia_assets\n    id\n  }\n  ...useHandleBlockchainActions_approve_payment_asset\n}\n\nfragment SetCreatorFeesAction_data on SetCreatorFeesActionType {\n  __typename\n  ...useHandleBlockchainActions_set_creator_fees\n}\n\nfragment StackedAssetMedia_assets on AssetType {\n  relayId\n  ...AssetMedia_asset\n  collection {\n    logo\n    id\n  }\n}\n\nfragment SwapDataHeader_swap on SwapDataType {\n  maker {\n    address\n    displayName\n    id\n  }\n  taker {\n    address\n    displayName\n    id\n  }\n  makerAssets {\n    asset {\n      chain {\n        identifier\n      }\n      id\n    }\n    ...SwapDataSide_assets\n  }\n  takerAssets {\n    ...SwapDataSide_assets\n  }\n}\n\nfragment SwapDataSide_assets on AssetQuantityDataType {\n  asset {\n    relayId\n    displayName\n    symbol\n    assetContract {\n      tokenStandard\n      id\n    }\n    ...StackedAssetMedia_assets\n    id\n  }\n  quantity\n}\n\nfragment TokenPricePayment on PaymentAssetType {\n  symbol\n}\n\nfragment UpdateDropMechanicsAction_data on DropMechanicsUpdateActionType {\n  __typename\n  ...useHandleBlockchainActions_update_drop_mechanics\n}\n\nfragment UpdatePreRevealAction_data on CollectionTokenMetadataUpdateActionType {\n  __typename\n  ...useHandleBlockchainActions_update_drop_pre_reveal\n}\n\nfragment collection_url on CollectionType {\n  slug\n  isCategory\n}\n\nfragment readOfferDataToAcceptPerUnitPrice_offerToAccept on OfferToAcceptType {\n  orderData {\n    perUnitPrice {\n      usd\n      unit\n    }\n    payment {\n      ...TokenPricePayment\n      id\n    }\n  }\n}\n\nfragment readOfferDataToAcceptPrice_offerToAccept on OfferToAcceptType {\n  orderData {\n    perUnitPrice {\n      usd\n      unit\n    }\n    payment {\n      ...TokenPricePayment\n      id\n    }\n  }\n  itemFillAmount\n}\n\nfragment readOrderDataPrices on OrderDataType {\n  perUnitPrice {\n    usd\n    unit\n  }\n  payment {\n    ...TokenPricePayment\n    id\n  }\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      quantity\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment readOrderDataToFillPrices_orderDataToFill on OrderToFillType {\n  orderData {\n    perUnitPrice {\n      usd\n      unit\n    }\n    payment {\n      ...TokenPricePayment\n      id\n    }\n  }\n  itemFillAmount\n}\n\nfragment useHandleBlockchainActions_approve_asset on AssetApprovalActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_approve_payment_asset on PaymentAssetApprovalActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_ask_for_asset_swap on AskForSwapType {\n  fromAsset {\n    decimals\n    relayId\n    id\n  }\n  toAsset {\n    relayId\n    id\n  }\n}\n\nfragment useHandleBlockchainActions_bulk_accept_offers on BulkAcceptOffersActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  offersToAccept {\n    orderData {\n      openedAt\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_bulk_fulfill_orders on BulkFulfillOrdersActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  ordersToFill {\n    orderData {\n      openedAt\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_burnToRedeem on AssetBurnToRedeemActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_cancel_orders on CancelOrderActionType {\n  method {\n    __typename\n    ... on TransactionSubmissionDataType {\n      ...useHandleBlockchainActions_transaction\n    }\n    ... on SignAndPostOrderCancelType {\n      cancelOrderData: data {\n        payload\n        message\n      }\n      serverSignature\n      clientSignatureStandard\n    }\n    ... on GaslessCancelType {\n      orderRelayIds\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_cancel_swap_orders on CancelSwapOrdersActionType {\n  method {\n    __typename\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_create_bulk_order on CreateBulkOrderActionType {\n  method {\n    clientMessage\n    clientSignatureStandard\n    serverSignature\n    orderDatas\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_create_order on CreateOrderActionType {\n  method {\n    clientMessage\n    clientSignatureStandard\n    serverSignature\n    orderData\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_create_swap_order on CreateSwapOrderActionType {\n  method {\n    clientMessage\n    clientSignatureStandard\n    serverSignature\n    swapData\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_deploy_contract on DropContractDeployActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_freeze_asset_metadata on AssetFreezeMetadataActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_fulfill_order on FulfillOrderActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  orderData {\n    openedAt\n  }\n}\n\nfragment useHandleBlockchainActions_fulfill_swap_order on FulfillSwapOrderActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  swapData {\n    openedAt\n  }\n}\n\nfragment useHandleBlockchainActions_mint_asset on MintActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  startTime\n}\n\nfragment useHandleBlockchainActions_mint_your_own_collection on MintYourOwnCollectionActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_set_creator_fees on SetCreatorFeesActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_swap_asset on AssetSwapActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_transaction on TransactionSubmissionDataType {\n  chain {\n    identifier\n  }\n  ...useTransaction_transaction\n}\n\nfragment useHandleBlockchainActions_transfer_asset on AssetTransferActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_update_drop_mechanics on DropMechanicsUpdateActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_update_drop_pre_reveal on CollectionTokenMetadataUpdateActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useIsRarityEnabled_collection on CollectionType {\n  slug\n  enabledRarities\n}\n\nfragment useTotalItems_ordersData on OrderDataType {\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      asset {\n        relayId\n        id\n      }\n    }\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment useTotalPriceOfferDataToAccept_offersToAccept on OfferToAcceptType {\n  itemFillAmount\n  ...readOfferDataToAcceptPerUnitPrice_offerToAccept\n}\n\nfragment useTotalPriceOrderDataToFill_ordersToFill on OrderToFillType {\n  ...readOrderDataToFillPrices_orderDataToFill\n}\n\nfragment useTotalPriceOrderData_orderData on OrderDataType {\n  ...readOrderDataPrices\n}\n\nfragment useTransaction_transaction on TransactionSubmissionDataType {\n  chain {\n    identifier\n  }\n  source {\n    value\n  }\n  destination {\n    value\n  }\n  value\n  data\n}\n',
                    'variables': {
                        'orderId': nft_order,
                        'itemFillAmount': '1',
                        'takerAssetsForCriteria': None,
                        'giftRecipientAddress': None,
                        'optionalCreatorFeeBasisPoints': None,
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id'], auth=auth), payload=json_data, session=session)
                return response['data']['order']['fulfill']['actions'][0]['method']
            except:
                time.sleep(i * 1)
        return None

    def buy_nft(self, private_key, max_price, attempt = 0, auth=None, session=None):

        if attempt > 10:
            return 'error'
        elif attempt != 0:
            time.sleep(1)

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        self.max_price = max_price

        # if session is None:
        session = self.help.get_tls_session()

        if auth is None:
            auth = self.get_auth(account, session)
            if not auth:
                return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)

        collections = self.get_collections(account, auth, session)
        if not collections:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)

        collection = random.choice(collections)
        nft = self.get_nfts(account, auth, session, collection['slug'])
        if not nft:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)


        order_data = self.get_buy_data(account, auth, session, nft['orderData']['bestAskV2']['relayId'])
        if not order_data:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)


        tx = make_tx(new_w3, account, value=int(order_data['value']), to=order_data['destination']['value'], data=order_data['data'])
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)

        self.logger.log_success(f"{self.project} | Успешно купил NFT ({collection['name']}) за {nft['orderData']['bestAskV2']['priceType']['eth']} ETH",wallet=account.address)
        return new_w3.to_hex(hash)

    def get_users_nfts(self, account, auth, session, chain='BASE'):

        for i in range(5):
            try:
                json_data = {
                    'id': 'AccountCollectedAssetSearchListQuery',
                    'query': 'query AccountCollectedAssetSearchListQuery(\n  $chains: [ChainScalar!]\n  $collections: [CollectionSlug!]\n  $count: Int!\n  $cursor: String\n  $identity: IdentityInputType!\n  $numericTraits: [TraitRangeType!]\n  $paymentAssets: [PaymentAssetSymbol]\n  $priceFilter: PriceFilterType\n  $query: String\n  $resultModel: SearchResultModel\n  $sortAscending: Boolean\n  $sortBy: SearchSortBy\n  $stringTraits: [TraitInputType!]\n  $toggles: [SearchToggle!]\n  $showContextMenu: Boolean!\n) {\n  ...AccountCollectedAssetSearchListPagination_data_1CyApM\n}\n\nfragment AcceptOfferButton_asset_3StDC7 on AssetType {\n  relayId\n  acceptOfferDisabled {\n    __typename\n  }\n  ownedQuantity(identity: $identity)\n  ...AcceptOfferModalContent_criteriaAsset_3StDC7\n  ...itemEvents_dataV2\n}\n\nfragment AcceptOfferButton_order_3StDC7 on OrderV2Type {\n  relayId\n  side\n  orderType\n  item {\n    __typename\n    ... on AssetType {\n      acceptOfferDisabled {\n        __typename\n      }\n      collection {\n        statsV2 {\n          floorPrice {\n            eth\n          }\n        }\n        id\n      }\n      chain {\n        identifier\n      }\n      ownedQuantity(identity: $identity)\n      ...itemEvents_dataV2\n    }\n    ... on AssetBundleType {\n      bundleCollection: collection {\n        statsV2 {\n          floorPrice {\n            eth\n          }\n        }\n        id\n      }\n      chain {\n        identifier\n      }\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              ownedQuantity(identity: $identity)\n              id\n            }\n            id\n          }\n        }\n      }\n      ...itemEvents_dataV2\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  maker {\n    address\n    id\n  }\n  perUnitPriceType {\n    eth\n  }\n}\n\nfragment AcceptOfferModalContent_criteriaAsset_3StDC7 on AssetType {\n  __typename\n  assetContract {\n    address\n    id\n  }\n  chain {\n    identifier\n  }\n  tokenId\n  relayId\n  ownedQuantity(identity: $identity)\n  isCurrentlyFungible\n  defaultRarityData {\n    rank\n    id\n  }\n  ...ItemOfferDetails_item\n  ...FloorPriceDifference_item\n  ...readOptionalCreatorFees_item\n}\n\nfragment AccountCollectedAssetSearchListPagination_data_1CyApM on Query {\n  queriedAt\n  searchItems(first: $count, after: $cursor, chains: $chains, collections: $collections, identity: $identity, numericTraits: $numericTraits, paymentAssets: $paymentAssets, priceFilter: $priceFilter, querystring: $query, resultType: $resultModel, sortAscending: $sortAscending, sortBy: $sortBy, stringTraits: $stringTraits, toggles: $toggles) {\n    edges {\n      node {\n        __typename\n        relayId\n        ...readItemHasBestAsk_item\n        ...AssetSearchList_data_155Sn1\n        ...useAssetSelectionStorage_item_3NSiLP\n        ...PortfolioTable_items_1TFcTQ\n        ... on Node {\n          __isNode: __typename\n          id\n        }\n      }\n      cursor\n    }\n    totalCount\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}\n\nfragment AccountLink_data on AccountType {\n  address\n  config\n  isCompromised\n  user {\n    publicUsername\n    id\n  }\n  displayName\n  ...ProfileImage_data\n  ...wallet_accountKey\n  ...accounts_url\n}\n\nfragment AddToCartAndQuickBuyButton_order on OrderV2Type {\n  ...useIsQuickBuyEnabled_order\n  ...ItemAddToCartButton_order\n  ...QuickBuyButton_order\n}\n\nfragment AssetContextMenu_data on AssetType {\n  relayId\n}\n\nfragment AssetMediaAnimation_asset on AssetType {\n  ...AssetMediaImage_asset\n  ...AssetMediaContainer_asset\n  ...AssetMediaPlaceholderImage_asset\n}\n\nfragment AssetMediaAudio_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaContainer_asset on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_1LNk0S on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_23BBEz on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_4uIQ9K\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_2OUs0D on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_4uIQ9K\n  defaultRarityData {\n    ...RarityIndicator_data\n    id\n  }\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_4a3mm5 on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  defaultRarityData {\n    ...RarityIndicator_data\n    id\n  }\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaEditions_asset_1mZMwQ on AssetType {\n  decimals\n}\n\nfragment AssetMediaEditions_asset_4uIQ9K on AssetType {\n  decimals\n  ownedQuantity(identity: $identity)\n}\n\nfragment AssetMediaImage_asset on AssetType {\n  backgroundColor\n  imageUrl\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaPlaceholderImage_asset on AssetType {\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaVideo_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaWebgl_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMedia_asset on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_1LNk0S\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetMedia_asset_1mZMwQ on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_1LNk0S\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetMedia_asset_2OUs0D on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_2OUs0D\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetMedia_asset_4uIQ9K on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_23BBEz\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetMedia_asset_5MxNd on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_4a3mm5\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetOfferModal_asset on AssetType {\n  relayId\n  chain {\n    identifier\n  }\n}\n\nfragment AssetQuantity_data on AssetQuantityType {\n  asset {\n    ...Price_data\n    id\n  }\n  quantity\n}\n\nfragment AssetSearchListViewTableAssetInfo_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ...PortfolioTableItemCellTooltip_item\n}\n\nfragment AssetSearchListViewTableQuickBuy_order on OrderV2Type {\n  maker {\n    address\n    id\n  }\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    ...itemEvents_dataV2\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  openedAt\n  relayId\n}\n\nfragment AssetSearchList_data_155Sn1 on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ...ItemCard_data_155Sn1\n  ... on AssetType {\n    collection {\n      isVerified\n      relayId\n      id\n    }\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      isVerified\n      relayId\n      id\n    }\n  }\n  chain {\n    identifier\n  }\n  ...useAssetSelectionStorage_item_3NSiLP\n}\n\nfragment BulkPurchaseModal_orders on OrderV2Type {\n  relayId\n  item {\n    __typename\n    relayId\n    chain {\n      identifier\n    }\n    ... on AssetType {\n      collection {\n        slug\n        isSafelisted\n        id\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  payment {\n    relayId\n    symbol\n    id\n  }\n  ...useTotalPrice_orders\n  ...useFulfillingListingsWillReactivateOrders_orders\n}\n\nfragment CancelItemOrdersButton_items on ItemType {\n  __isItemType: __typename\n  __typename\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    relayId\n  }\n  ... on AssetBundleType {\n    relayId\n  }\n  ...CancelOrdersConfirmationModal_items\n}\n\nfragment CancelOrdersConfirmationModal_items on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...StackedAssetMedia_assets\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment CollectionLink_assetContract on AssetContractType {\n  address\n  blockExplorerLink\n}\n\nfragment CollectionLink_collection on CollectionType {\n  name\n  slug\n  verificationStatus\n  ...collection_url\n}\n\nfragment CollectionTrackingContext_collection on CollectionType {\n  relayId\n  slug\n  isVerified\n  isCollectionOffersEnabled\n  defaultChain {\n    identifier\n  }\n}\n\nfragment CreateListingButton_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...CreateQuickSingleListingFlowModal_asset\n  }\n  ...itemEvents_dataV2\n  ...item_sellUrl\n}\n\nfragment CreateQuickSingleListingFlowModal_asset on AssetType {\n  relayId\n  chain {\n    identifier\n  }\n  ...itemEvents_dataV2\n}\n\nfragment EditListingButton_item on ItemType {\n  __isItemType: __typename\n  chain {\n    identifier\n  }\n  ...EditListingModal_item\n  ...itemEvents_dataV2\n}\n\nfragment EditListingButton_listing on OrderV2Type {\n  ...EditListingModal_listing\n}\n\nfragment EditListingModal_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    tokenId\n    assetContract {\n      address\n      id\n    }\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment EditListingModal_listing on OrderV2Type {\n  relayId\n}\n\nfragment FloorPriceDifference_item on ItemType {\n  __isItemType: __typename\n  ... on AssetType {\n    collection {\n      statsV2 {\n        floorPrice {\n          eth\n        }\n      }\n      id\n    }\n  }\n}\n\nfragment ItemAddToCartButton_order on OrderV2Type {\n  maker {\n    address\n    id\n  }\n  taker {\n    address\n    id\n  }\n  item {\n    __typename\n    ... on AssetType {\n      isCurrentlyFungible\n    }\n    ...itemEvents_dataV2\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  openedAt\n  ...ShoppingCartContextProvider_inline_order\n}\n\nfragment ItemCardContent on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    relayId\n    name\n    ...AssetMedia_asset_1mZMwQ\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            relayId\n            ...AssetMedia_asset\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment ItemCardContent_4uIQ9K on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    relayId\n    name\n    ...AssetMedia_asset_4uIQ9K\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            relayId\n            ...AssetMedia_asset\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment ItemCardCta_item_20mRwh on ItemType {\n  __isItemType: __typename\n  __typename\n  orderData {\n    bestAskV2 {\n      ...AddToCartAndQuickBuyButton_order\n      ...EditListingButton_listing\n      ...QuickBuyButton_order\n      id\n    }\n  }\n  ...AssetContextMenu_data @include(if: $showContextMenu)\n  ...useItemCardCta_item_20mRwh\n  ...itemEvents_dataV2\n  ...CreateListingButton_item\n  ...EditListingButton_item\n}\n\nfragment ItemCardFooter_3puo6e on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  name\n  orderData {\n    bestBidV2 {\n      orderType\n      priceType {\n        unit\n      }\n      ...ItemCardPrice_data\n      id\n    }\n    bestAskV2 {\n      ...ItemCardFooter_bestAskV2\n      id\n    }\n    bestAskForOwnerItemCard: bestAskV2(byAddress: $identity) {\n      ...ItemCardFooter_bestAskV2\n      id\n    }\n  }\n  ...ItemMetadata_3klarN\n  ... on AssetType {\n    tokenId\n    isDelisted\n    defaultRarityData {\n      ...RarityIndicator_data\n      id\n    }\n    collection {\n      slug\n      name\n      isVerified\n      ...collection_url\n      ...useIsRarityEnabled_collection\n      id\n    }\n    largestOwner {\n      owner {\n        ...AccountLink_data\n        id\n      }\n      id\n    }\n    ...AssetSearchListViewTableAssetInfo_item\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      slug\n      name\n      isVerified\n      ...collection_url\n      ...useIsRarityEnabled_collection\n      id\n    }\n  }\n  ...useItemCardCta_item_20mRwh\n  ...item_url\n  ...ItemCardContent\n}\n\nfragment ItemCardFooter_bestAskV2 on OrderV2Type {\n  orderType\n  priceType {\n    unit\n  }\n  maker {\n    address\n    id\n  }\n  ...ItemCardPrice_data\n  ...ItemAddToCartButton_order\n  ...AssetSearchListViewTableQuickBuy_order\n  ...useIsQuickBuyEnabled_order\n}\n\nfragment ItemCardPrice_data on OrderV2Type {\n  perUnitPriceType {\n    unit\n  }\n  payment {\n    symbol\n    id\n  }\n  ...useIsQuickBuyEnabled_order\n}\n\nfragment ItemCard_data_155Sn1 on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  chain {\n    identifier\n  }\n  orderData {\n    bestAskV2 {\n      priceType {\n        eth\n      }\n      id\n    }\n  }\n  ... on AssetType {\n    isDelisted\n    totalQuantity\n    collection {\n      slug\n      ...CollectionTrackingContext_collection\n      id\n    }\n    ...itemEvents_data\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      slug\n      ...CollectionTrackingContext_collection\n      id\n    }\n  }\n  ...ItemCardContent_4uIQ9K\n  ...ItemCardFooter_3puo6e\n  ...ItemCardCta_item_20mRwh\n  ...item_url\n  ...ItemTrackingContext_item\n}\n\nfragment ItemMetadata_3klarN on ItemType {\n  __isItemType: __typename\n  __typename\n  orderData {\n    bestAskV2 {\n      openedAt\n      createdDate\n      closedAt\n      id\n    }\n    bestAskForOwnerItemCard: bestAskV2(byAddress: $identity) {\n      openedAt\n      createdDate\n      closedAt\n      id\n    }\n  }\n  assetEventData {\n    lastSale {\n      unitPriceQuantity {\n        ...AssetQuantity_data\n        quantity\n        asset {\n          symbol\n          decimals\n          id\n        }\n        id\n      }\n    }\n  }\n  ... on AssetType {\n    bestAllTypeBid {\n      perUnitPriceType {\n        unit\n        symbol\n      }\n      id\n    }\n    mintEvent {\n      perUnitPrice {\n        unit\n        symbol\n      }\n      id\n    }\n  }\n}\n\nfragment ItemOfferDetails_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    displayName\n    collection {\n      ...CollectionLink_collection\n      id\n    }\n    ...StackedAssetMedia_assets\n  }\n  ... on AssetBundleType {\n    displayName\n    bundleCollection: collection {\n      ...CollectionLink_collection\n      id\n    }\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment ItemTrackingContext_item on ItemType {\n  __isItemType: __typename\n  relayId\n  verificationStatus\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    tokenId\n    isReportedSuspicious\n    assetContract {\n      address\n      id\n    }\n  }\n  ... on AssetBundleType {\n    slug\n  }\n}\n\nfragment MakeAssetOfferButton_asset on AssetType {\n  relayId\n  verificationStatus\n  isBiddingEnabled {\n    value\n    reason\n  }\n  chain {\n    identifier\n  }\n  ...AssetOfferModal_asset\n}\n\nfragment OrderListItem_order on OrderV2Type {\n  relayId\n  makerOwnedQuantity\n  item {\n    __typename\n    displayName\n    ... on AssetType {\n      assetContract {\n        ...CollectionLink_assetContract\n        id\n      }\n      collection {\n        ...CollectionLink_collection\n        id\n      }\n      ...AssetMedia_asset\n      ...asset_url\n      ...useItemFees_item\n    }\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              displayName\n              relayId\n              assetContract {\n                ...CollectionLink_assetContract\n                id\n              }\n              collection {\n                ...CollectionLink_collection\n                id\n              }\n              ...StackedAssetMedia_assets\n              ...AssetMedia_asset\n              ...asset_url\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ...itemEvents_dataV2\n    ...useIsItemSafelisted_item\n    ...ItemTrackingContext_item\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  remainingQuantityType\n  ...OrderPrice\n}\n\nfragment OrderList_orders on OrderV2Type {\n  item {\n    __typename\n    ... on AssetType {\n      __typename\n      relayId\n    }\n    ... on AssetBundleType {\n      __typename\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  relayId\n  ...OrderListItem_order\n  ...useFulfillingListingsWillReactivateOrders_orders\n}\n\nfragment OrderPrice on OrderV2Type {\n  priceType {\n    unit\n  }\n  perUnitPriceType {\n    unit\n  }\n  payment {\n    ...TokenPricePayment\n    id\n  }\n}\n\nfragment PortfolioTableAcceptOfferButton_item_3StDC7 on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    bestAllTypeBid {\n      ...AcceptOfferButton_order_3StDC7\n      id\n    }\n    ...AcceptOfferButton_asset_3StDC7\n  }\n  ... on AssetBundleType {\n    orderData {\n      bestBidV2 {\n        ...AcceptOfferButton_order_3StDC7\n        id\n      }\n    }\n  }\n}\n\nfragment PortfolioTableBestOfferCell_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    bestAllTypeBid {\n      perUnitPriceType {\n        unit\n        symbol\n      }\n      id\n    }\n  }\n  ... on AssetBundleType {\n    orderData {\n      bestBidV2 {\n        priceType {\n          unit\n          symbol\n        }\n        id\n      }\n    }\n  }\n}\n\nfragment PortfolioTableBuyButton_asset_3ioucg on AssetType {\n  orderData {\n    bestAskV2 {\n      ...ItemAddToCartButton_order @skip(if: $showContextMenu)\n      id\n    }\n  }\n}\n\nfragment PortfolioTableCostCell_item on ItemType {\n  __isItemType: __typename\n  __typename\n  lastCostEvent {\n    transaction {\n      blockExplorerLink\n      id\n    }\n    id\n  }\n  pnl {\n    costPrice {\n      unit\n      symbol\n    }\n  }\n}\n\nfragment PortfolioTableDifferenceCell_item_3StDC7 on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    orderData {\n      bestAskV2 {\n        __typename\n        id\n      }\n      bestAskForOwner: bestAskV2(byAddress: $identity) {\n        __typename\n        id\n      }\n    }\n    pnl {\n      pnlPrice {\n        unit\n        symbol\n      }\n    }\n  }\n}\n\nfragment PortfolioTableExpandedRow_item_1TFcTQ on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    isCompromised\n    isCurrentlyFungible\n    ...asset_url\n    ...AssetMedia_asset_2OUs0D\n    ...PortfolioTableBuyButton_asset_3ioucg\n    ...PortfolioTableMakeOfferButton_asset_3ioucg\n    ...PortfolioTableTraitTable_asset\n  }\n  ...PortfolioTableAcceptOfferButton_item_3StDC7\n  ...PortfolioTableListButton_item_1TFcTQ\n  ...PortfolioTableMakeOfferButton_asset_3ioucg\n  ...PortfolioTableTraitTable_asset\n  ...PortfolioTableListingsTable_asset\n}\n\nfragment PortfolioTableFloorPriceCell_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    assetCollection: collection {\n      statsV2 {\n        floorPrice {\n          unit\n          symbol\n        }\n      }\n      id\n    }\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      statsV2 {\n        floorPrice {\n          unit\n          symbol\n        }\n      }\n      id\n    }\n  }\n}\n\nfragment PortfolioTableItemCellTooltip_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ...AssetMedia_asset_5MxNd\n  ...PortfolioTableTraitTable_asset\n  ...asset_url\n}\n\nfragment PortfolioTableItemCell_item_3StDC7 on ItemType {\n  __isItemType: __typename\n  __typename\n  chain {\n    displayName\n    identifier\n  }\n  ...PortfolioTableItemCellTooltip_item\n  ... on AssetType {\n    ownedQuantity(identity: $identity)\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    assetCollection: collection {\n      ...CollectionLink_collection\n      id\n    }\n    ...AssetMedia_asset\n    ...asset_display_name\n  }\n  ... on AssetBundleType {\n    displayName\n    bundleCollection: collection {\n      ...CollectionLink_collection\n      id\n    }\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n  ...item_url\n}\n\nfragment PortfolioTableListButton_bestAskV2_3ioucg on OrderV2Type {\n  ...EditListingButton_listing @include(if: $showContextMenu)\n  maker {\n    address\n    id\n  }\n  orderType\n}\n\nfragment PortfolioTableListButton_item_1TFcTQ on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  chain {\n    isTradingEnabled\n  }\n  orderData {\n    bestAskV2 {\n      ...PortfolioTableListButton_bestAskV2_3ioucg\n      id\n    }\n    bestAskForOwner: bestAskV2(byAddress: $identity) {\n      ...PortfolioTableListButton_bestAskV2_3ioucg\n      id\n    }\n  }\n  ... on AssetType {\n    isCurrentlyFungible\n    isListable\n  }\n  ...itemEvents_data\n  ...CreateListingButton_item\n  ...EditListingButton_item @include(if: $showContextMenu)\n}\n\nfragment PortfolioTableListingCell_bestAskV2 on OrderV2Type {\n  perUnitPriceType {\n    unit\n    symbol\n  }\n  closedAt\n}\n\nfragment PortfolioTableListingCell_item_3StDC7 on ItemType {\n  __isItemType: __typename\n  relayId\n  orderData {\n    bestAskV2 {\n      ...PortfolioTableListingCell_bestAskV2\n      id\n    }\n    bestAskForOwner: bestAskV2(byAddress: $identity) {\n      ...PortfolioTableListingCell_bestAskV2\n      id\n    }\n  }\n  ...PortfolioTableListingTooltip_item_3StDC7\n}\n\nfragment PortfolioTableListingTooltipContent_item on AssetType {\n  collection {\n    statsV2 {\n      floorPrice {\n        eth\n      }\n    }\n    id\n  }\n}\n\nfragment PortfolioTableListingTooltip_item_3StDC7 on ItemType {\n  __isItemType: __typename\n  __typename\n  orderData {\n    bestAskV2 {\n      relayId\n      id\n    }\n    bestAskForOwner: bestAskV2(byAddress: $identity) {\n      relayId\n      id\n    }\n  }\n  ... on AssetType {\n    ...PortfolioTableListingTooltipContent_item\n  }\n}\n\nfragment PortfolioTableListingsTable_asset on AssetType {\n  ...EditListingButton_item\n  relayId\n  chain {\n    identifier\n  }\n  assetContract {\n    address\n    id\n  }\n  isCurrentlyFungible\n  tokenId\n}\n\nfragment PortfolioTableMakeOfferButton_asset_3ioucg on AssetType {\n  ...MakeAssetOfferButton_asset @skip(if: $showContextMenu)\n}\n\nfragment PortfolioTableOptionsCell_item_1TFcTQ on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...AssetContextMenu_data @include(if: $showContextMenu)\n  }\n  ...PortfolioTableAcceptOfferButton_item_3StDC7\n  ...PortfolioTableListButton_item_1TFcTQ\n  ...itemEvents_dataV2\n}\n\nfragment PortfolioTableRow_item_1TFcTQ on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ...PortfolioTableItemCell_item_3StDC7\n  ...PortfolioTableFloorPriceCell_item\n  ...PortfolioTableBestOfferCell_item\n  ...PortfolioTableListingCell_item_3StDC7\n  ...PortfolioTableCostCell_item\n  ...PortfolioTableDifferenceCell_item_3StDC7\n  ...PortfolioTableOptionsCell_item_1TFcTQ\n  ...PortfolioTableExpandedRow_item_1TFcTQ\n}\n\nfragment PortfolioTableTraitTable_asset on AssetType {\n  assetContract {\n    address\n    chain\n    id\n  }\n  isCurrentlyFungible\n  tokenId\n}\n\nfragment PortfolioTable_items_1TFcTQ on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  ... on AssetType {\n    ownership(identity: $identity) {\n      isPrivate\n      quantity\n    }\n  }\n  ...PortfolioTableRow_item_1TFcTQ\n  ...useAssetSelectionStorage_item_3NSiLP\n  ...itemEvents_dataV2\n}\n\nfragment Price_data on AssetType {\n  decimals\n  symbol\n  usdSpotPrice\n}\n\nfragment ProfileImage_data on AccountType {\n  imageUrl\n}\n\nfragment QuickBuyButton_order on OrderV2Type {\n  maker {\n    address\n    id\n  }\n  taker {\n    address\n    ...wallet_accountKey\n    id\n  }\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    ...itemEvents_dataV2\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  openedAt\n  relayId\n}\n\nfragment RarityIndicator_data on RarityDataType {\n  rank\n  rankPercentile\n  rankCount\n  maxRank\n}\n\nfragment ShoppingCartContextProvider_inline_order on OrderV2Type {\n  relayId\n  makerOwnedQuantity\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    relayId\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  maker {\n    relayId\n    id\n  }\n  taker {\n    address\n    ...wallet_accountKey\n    id\n  }\n  priceType {\n    usd\n  }\n  payment {\n    relayId\n    id\n  }\n  remainingQuantityType\n  ...useTotalItems_orders\n  ...ShoppingCart_orders\n}\n\nfragment ShoppingCartDetailedView_orders on OrderV2Type {\n  relayId\n  item {\n    __typename\n    chain {\n      identifier\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  supportsGiftingOnPurchase\n  ...useTotalPrice_orders\n  ...OrderList_orders\n}\n\nfragment ShoppingCart_orders on OrderV2Type {\n  ...ShoppingCartDetailedView_orders\n  ...BulkPurchaseModal_orders\n}\n\nfragment StackedAssetMedia_assets on AssetType {\n  relayId\n  ...AssetMedia_asset\n  collection {\n    logo\n    id\n  }\n}\n\nfragment TokenPricePayment on PaymentAssetType {\n  symbol\n}\n\nfragment accounts_url on AccountType {\n  address\n  user {\n    publicUsername\n    id\n  }\n}\n\nfragment asset_display_name on AssetType {\n  tokenId\n  name\n}\n\nfragment asset_url on AssetType {\n  assetContract {\n    address\n    id\n  }\n  tokenId\n  chain {\n    identifier\n  }\n}\n\nfragment bundle_url on AssetBundleType {\n  slug\n  chain {\n    identifier\n  }\n}\n\nfragment collection_url on CollectionType {\n  slug\n  isCategory\n}\n\nfragment itemEvents_data on AssetType {\n  relayId\n  assetContract {\n    address\n    id\n  }\n  tokenId\n  chain {\n    identifier\n  }\n}\n\nfragment itemEvents_dataV2 on ItemType {\n  __isItemType: __typename\n  relayId\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    tokenId\n    assetContract {\n      address\n      id\n    }\n  }\n}\n\nfragment item_sellUrl on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...asset_url\n  }\n  ... on AssetBundleType {\n    slug\n    chain {\n      identifier\n    }\n    assetQuantities(first: 18) {\n      edges {\n        node {\n          asset {\n            relayId\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment item_url on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    ...asset_url\n  }\n  ... on AssetBundleType {\n    ...bundle_url\n  }\n}\n\nfragment readItemHasBestAsk_item on ItemType {\n  __isItemType: __typename\n  orderData {\n    bestAskV2 {\n      __typename\n      id\n    }\n  }\n}\n\nfragment readOptionalCreatorFees_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    collection {\n      isCreatorFeesEnforced\n      totalCreatorFeeBasisPoints\n      id\n    }\n  }\n}\n\nfragment useAssetSelectionStorage_item_3NSiLP on ItemType {\n  __isItemType: __typename\n  __typename\n  relayId\n  chain {\n    identifier\n    isTradingEnabled\n  }\n  ... on AssetType {\n    bestAllTypeBid {\n      relayId\n      id\n    }\n    orderData {\n      bestAskV2 {\n        relayId\n        maker {\n          address\n          id\n        }\n        id\n      }\n      bestAskForOwner: bestAskV2(byAddress: $identity) {\n        relayId\n        maker {\n          address\n          id\n        }\n        id\n      }\n    }\n    ...asset_url\n    isCompromised\n  }\n  ... on AssetBundleType {\n    orderData {\n      bestAskV2 {\n        relayId\n        maker {\n          address\n          id\n        }\n        id\n      }\n      bestBidV2 {\n        relayId\n        id\n      }\n    }\n  }\n  ...item_sellUrl\n  ...AssetContextMenu_data\n  ...CancelItemOrdersButton_items\n}\n\nfragment useFulfillingListingsWillReactivateOrders_orders on OrderV2Type {\n  ...useTotalItems_orders\n}\n\nfragment useIsItemSafelisted_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    collection {\n      slug\n      verificationStatus\n      id\n    }\n  }\n  ... on AssetBundleType {\n    assetQuantities(first: 30) {\n      edges {\n        node {\n          asset {\n            collection {\n              slug\n              verificationStatus\n              id\n            }\n            id\n          }\n          id\n        }\n      }\n    }\n  }\n}\n\nfragment useIsQuickBuyEnabled_order on OrderV2Type {\n  orderType\n  item {\n    __typename\n    ... on AssetType {\n      isCurrentlyFungible\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment useIsRarityEnabled_collection on CollectionType {\n  slug\n  enabledRarities\n}\n\nfragment useItemCardCta_item_20mRwh on ItemType {\n  __isItemType: __typename\n  __typename\n  chain {\n    identifier\n    isTradingEnabled\n  }\n  orderData {\n    bestAskV2 {\n      orderType\n      maker {\n        address\n        id\n      }\n      id\n    }\n  }\n  ... on AssetType {\n    isDelisted\n    isListable\n    isCurrentlyFungible\n    ownedQuantity(identity: $identity) @include(if: $showContextMenu)\n  }\n}\n\nfragment useItemFees_item on ItemType {\n  __isItemType: __typename\n  __typename\n  ... on AssetType {\n    totalCreatorFee\n    collection {\n      openseaSellerFeeBasisPoints\n      isCreatorFeesEnforced\n      id\n    }\n  }\n  ... on AssetBundleType {\n    bundleCollection: collection {\n      openseaSellerFeeBasisPoints\n      totalCreatorFeeBasisPoints\n      isCreatorFeesEnforced\n      id\n    }\n  }\n}\n\nfragment useTotalItems_orders on OrderV2Type {\n  item {\n    __typename\n    relayId\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment useTotalPrice_orders on OrderV2Type {\n  relayId\n  perUnitPriceType {\n    usd\n    unit\n  }\n  payment {\n    symbol\n    ...TokenPricePayment\n    id\n  }\n}\n\nfragment wallet_accountKey on AccountType {\n  address\n}\n',
                    'variables': {
                        'chains': [
                            chain,
                        ],
                        'collections': None,
                        'count': 32,
                        'cursor': None,
                        'identity': {
                            'address': account.address,
                        },
                        'numericTraits': None,
                        'paymentAssets': None,
                        'priceFilter': None,
                        'query': None,
                        'resultModel': 'ASSETS',
                        'sortAscending': None,
                        'sortBy': 'LAST_TRANSFER_DATE',
                        'stringTraits': None,
                        'toggles': None,
                        'showContextMenu': True,
                    },
                }

                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id'], auth=auth), payload=json_data, session=session)
                nfts = []
                for nft in response['data']['searchItems']['edges']:
                   nft = nft['node']
                   if nft['orderData']['bestAskV2'] is None:
                       nfts.append(nft)
                return nfts
            except:
                time.sleep(i * 1)
        return None

    def fix_data_types(self, original_message):
        _message = original_message.copy()
        _message['domain']['chainId'] = int(_message['domain']['chainId'])
        message = _message['message']
        message['zoneHash'] = self.w3.to_bytes(hexstr=message['zoneHash'][2:])
        message['salt'] = int(message['salt'])
        message['conduitKey'] = self.w3.to_bytes(hexstr=message['conduitKey'][2:])
        message['startTime'] = int(message['startTime'])
        message['endTime'] = int(message['endTime'])
        message['orderType'] = int(message['orderType'])
        message['counter'] = int(message['counter'])
        message['totalOriginalConsiderationItems'] = int(message['totalOriginalConsiderationItems'])

        for offer in message['offer']:
            offer['itemType'] = int(offer['itemType'])
            offer['identifierOrCriteria'] = int(offer['identifierOrCriteria'])
            offer['startAmount'] = int(offer['startAmount'])
            offer['endAmount'] = int(offer['endAmount'])

        for consideration in message['consideration']:
            consideration['itemType'] = int(consideration['itemType'])
            consideration['identifierOrCriteria'] = int(consideration['identifierOrCriteria'])
            consideration['startAmount'] = int(consideration['startAmount'])
            consideration['endAmount'] = int(consideration['endAmount'])

        return _message

    def get_sell_order(self, account, auth, session, nft, price):

        for i in range(5):
            try:
                current_time = datetime.utcnow()
                three_months = timedelta(days=90)
                end_time = current_time + three_months
                json_data = {
                    'id': 'CreateListingActionModalQuery',
                    'query': 'query CreateListingActionModalQuery(\n  $item: AssetQuantityInputType!\n  $price: PaymentAssetQuantityInputType!\n  $recipient: AddressScalar\n  $openedAt: DateTime!\n  $closedAt: DateTime!\n  $englishAuctionReservePrice: BigNumberScalar\n  $optionalCreatorFeeBasisPoints: Int\n) {\n  blockchain {\n    createListingActions(item: $item, price: $price, recipient: $recipient, openedAt: $openedAt, closedAt: $closedAt, englishAuctionReservePrice: $englishAuctionReservePrice, optionalCreatorFeeBasisPoints: $optionalCreatorFeeBasisPoints) {\n      __typename\n      ...BlockchainActionList_data\n    }\n  }\n}\n\nfragment AskForDepositAction_data on AskForDepositType {\n  asset {\n    chain {\n      identifier\n    }\n    decimals\n    symbol\n    usdSpotPrice\n    id\n  }\n  minQuantity\n}\n\nfragment AskForSwapAction_data on AskForSwapType {\n  __typename\n  fromAsset {\n    chain {\n      identifier\n    }\n    decimals\n    symbol\n    id\n  }\n  toAsset {\n    chain {\n      identifier\n    }\n    symbol\n    id\n  }\n  minQuantity\n  maxQuantity\n  ...useHandleBlockchainActions_ask_for_asset_swap\n}\n\nfragment AssetApprovalAction_data on AssetApprovalActionType {\n  __typename\n  asset {\n    chain {\n      identifier\n    }\n    ...StackedAssetMedia_assets\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    collection {\n      __typename\n      ...CollectionLink_collection\n      id\n    }\n    id\n  }\n  ...useHandleBlockchainActions_approve_asset\n}\n\nfragment AssetBurnToRedeemAction_data on AssetBurnToRedeemActionType {\n  __typename\n  ...useHandleBlockchainActions_burnToRedeem\n  asset {\n    chain {\n      identifier\n    }\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    collection {\n      __typename\n      ...CollectionLink_collection\n      id\n    }\n    displayName\n    ...StackedAssetMedia_assets\n    id\n  }\n}\n\nfragment AssetFreezeMetadataAction_data on AssetFreezeMetadataActionType {\n  __typename\n  ...useHandleBlockchainActions_freeze_asset_metadata\n}\n\nfragment AssetItem_asset on AssetType {\n  chain {\n    identifier\n  }\n  displayName\n  relayId\n  collection {\n    name\n    id\n  }\n  ...StackedAssetMedia_assets\n}\n\nfragment AssetMediaAnimation_asset on AssetType {\n  ...AssetMediaImage_asset\n  ...AssetMediaContainer_asset\n  ...AssetMediaPlaceholderImage_asset\n}\n\nfragment AssetMediaAudio_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaContainer_asset on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaContainer_asset_1LNk0S on AssetType {\n  backgroundColor\n  ...AssetMediaEditions_asset_1mZMwQ\n  collection {\n    ...useIsRarityEnabled_collection\n    id\n  }\n}\n\nfragment AssetMediaEditions_asset_1mZMwQ on AssetType {\n  decimals\n}\n\nfragment AssetMediaImage_asset on AssetType {\n  backgroundColor\n  imageUrl\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaPlaceholderImage_asset on AssetType {\n  collection {\n    displayData {\n      cardDisplayStyle\n    }\n    id\n  }\n}\n\nfragment AssetMediaVideo_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMediaWebgl_asset on AssetType {\n  backgroundColor\n  ...AssetMediaImage_asset\n}\n\nfragment AssetMedia_asset on AssetType {\n  animationUrl\n  displayImageUrl\n  imageUrl\n  isDelisted\n  ...AssetMediaAnimation_asset\n  ...AssetMediaAudio_asset\n  ...AssetMediaContainer_asset_1LNk0S\n  ...AssetMediaImage_asset\n  ...AssetMediaPlaceholderImage_asset\n  ...AssetMediaVideo_asset\n  ...AssetMediaWebgl_asset\n}\n\nfragment AssetSwapAction_data on AssetSwapActionType {\n  __typename\n  ...useHandleBlockchainActions_swap_asset\n}\n\nfragment AssetTransferAction_data on AssetTransferActionType {\n  __typename\n  ...useHandleBlockchainActions_transfer_asset\n}\n\nfragment BlockchainActionList_data on BlockchainActionType {\n  __isBlockchainActionType: __typename\n  __typename\n  ... on AssetApprovalActionType {\n    ...AssetApprovalAction_data\n  }\n  ... on AskForDepositType {\n    __typename\n    ...AskForDepositAction_data\n  }\n  ... on AskForSwapType {\n    __typename\n    ...AskForSwapAction_data\n  }\n  ... on AssetFreezeMetadataActionType {\n    __typename\n    ...AssetFreezeMetadataAction_data\n  }\n  ... on AssetSwapActionType {\n    __typename\n    ...AssetSwapAction_data\n  }\n  ... on AssetTransferActionType {\n    __typename\n    ...AssetTransferAction_data\n  }\n  ... on CreateOrderActionType {\n    __typename\n    ...CreateOrderAction_data\n  }\n  ... on CreateBulkOrderActionType {\n    __typename\n    ...CreateBulkOrderAction_data\n  }\n  ... on CreateSwapOrderActionType {\n    __typename\n    ...CreateSwapOrderAction_data\n  }\n  ... on CancelOrderActionType {\n    __typename\n    ...CancelOrderAction_data\n  }\n  ... on CancelSwapOrdersActionType {\n    __typename\n    ...CancelSwapOrdersAction_data\n  }\n  ... on FulfillOrderActionType {\n    __typename\n    ...FulfillOrderAction_data\n  }\n  ... on FulfillSwapOrderActionType {\n    __typename\n    ...FulfillSwapOrderAction_data\n  }\n  ... on BulkAcceptOffersActionType {\n    __typename\n    ...BulkAcceptOffersAction_data\n  }\n  ... on BulkFulfillOrdersActionType {\n    __typename\n    ...BulkFulfillOrdersAction_data\n  }\n  ... on PaymentAssetApprovalActionType {\n    __typename\n    ...PaymentAssetApprovalAction_data\n  }\n  ... on MintActionType {\n    __typename\n    ...MintAction_data\n  }\n  ... on DropContractDeployActionType {\n    __typename\n    ...DeployContractAction_data\n  }\n  ... on DropMechanicsUpdateActionType {\n    __typename\n    ...UpdateDropMechanicsAction_data\n  }\n  ... on SetCreatorFeesActionType {\n    __typename\n    ...SetCreatorFeesAction_data\n  }\n  ... on CollectionTokenMetadataUpdateActionType {\n    __typename\n    ...UpdatePreRevealAction_data\n  }\n  ... on AssetBurnToRedeemActionType {\n    __typename\n    ...AssetBurnToRedeemAction_data\n  }\n  ... on MintYourOwnCollectionActionType {\n    __typename\n    ...MintYourOwnCollectionAction_data\n  }\n}\n\nfragment BulkAcceptOffersAction_data on BulkAcceptOffersActionType {\n  __typename\n  maxQuantityToFill\n  offersToAccept {\n    itemFillAmount\n    orderData {\n      chain {\n        identifier\n      }\n      item {\n        __typename\n        ... on AssetQuantityDataType {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n        }\n        ... on AssetBundleType {\n          assetQuantities(first: 30) {\n            edges {\n              node {\n                asset {\n                  ...StackedAssetMedia_assets\n                  id\n                }\n                id\n              }\n            }\n          }\n        }\n        ... on Node {\n          __isNode: __typename\n          id\n        }\n      }\n      ...useTotalItems_ordersData\n    }\n    criteriaAsset {\n      relayId\n      ...StackedAssetMedia_assets\n      id\n    }\n    ...useTotalPriceOfferDataToAccept_offersToAccept\n    ...readOfferDataToAcceptPrice_offerToAccept\n  }\n  ...useHandleBlockchainActions_bulk_accept_offers\n}\n\nfragment BulkFulfillOrdersAction_data on BulkFulfillOrdersActionType {\n  __typename\n  maxOrdersToFill\n  ordersToFill {\n    itemFillAmount\n    orderData {\n      chain {\n        identifier\n      }\n      item {\n        __typename\n        ... on AssetQuantityDataType {\n          asset {\n            ...StackedAssetMedia_assets\n            id\n          }\n        }\n        ... on AssetBundleType {\n          assetQuantities(first: 30) {\n            edges {\n              node {\n                asset {\n                  ...StackedAssetMedia_assets\n                  id\n                }\n                id\n              }\n            }\n          }\n        }\n        ... on Node {\n          __isNode: __typename\n          id\n        }\n      }\n      ...useTotalItems_ordersData\n    }\n    ...useTotalPriceOrderDataToFill_ordersToFill\n    ...readOrderDataToFillPrices_orderDataToFill\n  }\n  ...useHandleBlockchainActions_bulk_fulfill_orders\n}\n\nfragment CancelOrderActionGaslessContent_action on CancelOrderActionType {\n  ordersData {\n    side\n    orderType\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        asset {\n          displayName\n          ...StackedAssetMedia_assets\n          id\n        }\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    price {\n      unit\n      symbol\n    }\n    orderCriteria {\n      collection {\n        name\n        representativeAsset {\n          ...StackedAssetMedia_assets\n          id\n        }\n        id\n      }\n    }\n  }\n}\n\nfragment CancelOrderActionOnChainContent_action on CancelOrderActionType {\n  ordersData {\n    side\n    orderType\n    ...OrderDataHeader_order\n    ...OrdersHeaderData_orders\n  }\n}\n\nfragment CancelOrderAction_data on CancelOrderActionType {\n  __typename\n  ordersData {\n    orderType\n    side\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        asset {\n          ...GaslessCancellationProcessingModal_items\n          ...GaslessCancellationFailedModal_items\n          id\n        }\n        quantity\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    orderCriteria {\n      collection {\n        representativeAsset {\n          ...GaslessCancellationProcessingModal_items\n          ...GaslessCancellationFailedModal_items\n          id\n        }\n        id\n      }\n      quantity\n    }\n  }\n  method {\n    __typename\n  }\n  ...CancelOrderActionOnChainContent_action\n  ...useHandleBlockchainActions_cancel_orders\n  ...CancelOrderActionGaslessContent_action\n}\n\nfragment CancelSwapOrdersAction_data on CancelSwapOrdersActionType {\n  __typename\n  swapsData {\n    ...SwapDataHeader_swap\n  }\n  ...useHandleBlockchainActions_cancel_swap_orders\n}\n\nfragment CollectionLink_assetContract on AssetContractType {\n  address\n  blockExplorerLink\n}\n\nfragment CollectionLink_collection on CollectionType {\n  name\n  slug\n  verificationStatus\n  ...collection_url\n}\n\nfragment CollectionOfferDetails_collection on CollectionType {\n  representativeAsset {\n    assetContract {\n      ...CollectionLink_assetContract\n      id\n    }\n    ...StackedAssetMedia_assets\n    id\n  }\n  ...CollectionLink_collection\n}\n\nfragment ConfirmationItem_asset on AssetType {\n  chain {\n    displayName\n  }\n  ...AssetItem_asset\n}\n\nfragment ConfirmationItem_asset_item_payment_asset on PaymentAssetType {\n  ...ConfirmationItem_extra_payment_asset\n}\n\nfragment ConfirmationItem_assets on AssetType {\n  ...ConfirmationItem_asset\n}\n\nfragment ConfirmationItem_extra_payment_asset on PaymentAssetType {\n  symbol\n  usdSpotPrice\n}\n\nfragment ConfirmationItem_payment_asset on PaymentAssetType {\n  ...ConfirmationItem_asset_item_payment_asset\n}\n\nfragment CreateBulkOrderAction_data on CreateBulkOrderActionType {\n  __typename\n  orderDatas {\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        asset {\n          ...StackedAssetMedia_assets\n          id\n        }\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    ...useTotalItems_ordersData\n    ...useTotalPriceOrderData_orderData\n  }\n  ...useHandleBlockchainActions_create_bulk_order\n}\n\nfragment CreateOrderAction_data on CreateOrderActionType {\n  __typename\n  orderData {\n    item {\n      __typename\n      ... on AssetQuantityDataType {\n        quantity\n      }\n      ... on Node {\n        __isNode: __typename\n        id\n      }\n    }\n    side\n    isCounterOrder\n    perUnitPrice {\n      unit\n      symbol\n    }\n    ...OrderDataHeader_order\n  }\n  ...useHandleBlockchainActions_create_order\n}\n\nfragment CreateSwapOrderAction_data on CreateSwapOrderActionType {\n  __typename\n  swapData {\n    ...SwapDataHeader_swap\n  }\n  ...useHandleBlockchainActions_create_swap_order\n}\n\nfragment DeployContractAction_data on DropContractDeployActionType {\n  __typename\n  ...useHandleBlockchainActions_deploy_contract\n}\n\nfragment FulfillOrderAction_data on FulfillOrderActionType {\n  __typename\n  orderData {\n    side\n    ...OrderDataHeader_order\n  }\n  itemFillAmount\n  criteriaAsset {\n    ...OrderDataHeader_criteriaAsset\n    id\n  }\n  ...useHandleBlockchainActions_fulfill_order\n}\n\nfragment FulfillSwapOrderAction_data on FulfillSwapOrderActionType {\n  __typename\n  swapData {\n    ...SwapDataHeader_swap\n  }\n  ...useHandleBlockchainActions_fulfill_swap_order\n}\n\nfragment GaslessCancellationFailedModal_items on ItemType {\n  __isItemType: __typename\n  ...StackedAssetMedia_assets\n}\n\nfragment GaslessCancellationProcessingModal_items on ItemType {\n  __isItemType: __typename\n  ...StackedAssetMedia_assets\n}\n\nfragment MintAction_data on MintActionType {\n  __typename\n  ...useHandleBlockchainActions_mint_asset\n}\n\nfragment MintYourOwnCollectionAction_data on MintYourOwnCollectionActionType {\n  __typename\n  ...useHandleBlockchainActions_mint_your_own_collection\n}\n\nfragment OrderDataHeader_criteriaAsset on AssetType {\n  ...ConfirmationItem_assets\n}\n\nfragment OrderDataHeader_order on OrderDataType {\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      asset {\n        ...ConfirmationItem_assets\n        id\n      }\n      quantity\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  recipient {\n    address\n    id\n  }\n  side\n  openedAt\n  closedAt\n  perUnitPrice {\n    unit\n  }\n  price {\n    unit\n    symbol\n    usd\n  }\n  payment {\n    ...ConfirmationItem_payment_asset\n    id\n  }\n  englishAuctionReservePrice {\n    unit\n  }\n  isCounterOrder\n  orderCriteria {\n    collection {\n      ...CollectionOfferDetails_collection\n      id\n    }\n    trait {\n      traitType\n      value\n      id\n    }\n    quantity\n  }\n}\n\nfragment OrdersHeaderData_orders on OrderDataType {\n  chain {\n    identifier\n  }\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      asset {\n        ...StackedAssetMedia_assets\n        id\n      }\n    }\n    ... on AssetBundleType {\n      assetQuantities(first: 20) {\n        edges {\n          node {\n            asset {\n              ...StackedAssetMedia_assets\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on AssetBundleToBeCreatedType {\n      assetQuantitiesToBeCreated: assetQuantities {\n        asset {\n          ...StackedAssetMedia_assets\n          id\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n  orderCriteria {\n    collection {\n      representativeAsset {\n        ...StackedAssetMedia_assets\n        id\n      }\n      id\n    }\n  }\n  orderType\n  side\n}\n\nfragment PaymentAssetApprovalAction_data on PaymentAssetApprovalActionType {\n  __typename\n  asset {\n    chain {\n      identifier\n    }\n    symbol\n    ...StackedAssetMedia_assets\n    id\n  }\n  ...useHandleBlockchainActions_approve_payment_asset\n}\n\nfragment SetCreatorFeesAction_data on SetCreatorFeesActionType {\n  __typename\n  ...useHandleBlockchainActions_set_creator_fees\n}\n\nfragment StackedAssetMedia_assets on AssetType {\n  relayId\n  ...AssetMedia_asset\n  collection {\n    logo\n    id\n  }\n}\n\nfragment SwapDataHeader_swap on SwapDataType {\n  maker {\n    address\n    displayName\n    id\n  }\n  taker {\n    address\n    displayName\n    id\n  }\n  makerAssets {\n    asset {\n      chain {\n        identifier\n      }\n      id\n    }\n    ...SwapDataSide_assets\n  }\n  takerAssets {\n    ...SwapDataSide_assets\n  }\n}\n\nfragment SwapDataSide_assets on AssetQuantityDataType {\n  asset {\n    relayId\n    displayName\n    symbol\n    assetContract {\n      tokenStandard\n      id\n    }\n    ...StackedAssetMedia_assets\n    id\n  }\n  quantity\n}\n\nfragment TokenPricePayment on PaymentAssetType {\n  symbol\n}\n\nfragment UpdateDropMechanicsAction_data on DropMechanicsUpdateActionType {\n  __typename\n  ...useHandleBlockchainActions_update_drop_mechanics\n}\n\nfragment UpdatePreRevealAction_data on CollectionTokenMetadataUpdateActionType {\n  __typename\n  ...useHandleBlockchainActions_update_drop_pre_reveal\n}\n\nfragment collection_url on CollectionType {\n  slug\n  isCategory\n}\n\nfragment readOfferDataToAcceptPerUnitPrice_offerToAccept on OfferToAcceptType {\n  orderData {\n    perUnitPrice {\n      usd\n      unit\n    }\n    payment {\n      ...TokenPricePayment\n      id\n    }\n  }\n}\n\nfragment readOfferDataToAcceptPrice_offerToAccept on OfferToAcceptType {\n  orderData {\n    perUnitPrice {\n      usd\n      unit\n    }\n    payment {\n      ...TokenPricePayment\n      id\n    }\n  }\n  itemFillAmount\n}\n\nfragment readOrderDataPrices on OrderDataType {\n  perUnitPrice {\n    usd\n    unit\n  }\n  payment {\n    ...TokenPricePayment\n    id\n  }\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      quantity\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment readOrderDataToFillPrices_orderDataToFill on OrderToFillType {\n  orderData {\n    perUnitPrice {\n      usd\n      unit\n    }\n    payment {\n      ...TokenPricePayment\n      id\n    }\n  }\n  itemFillAmount\n}\n\nfragment useHandleBlockchainActions_approve_asset on AssetApprovalActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_approve_payment_asset on PaymentAssetApprovalActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_ask_for_asset_swap on AskForSwapType {\n  fromAsset {\n    decimals\n    relayId\n    id\n  }\n  toAsset {\n    relayId\n    id\n  }\n}\n\nfragment useHandleBlockchainActions_bulk_accept_offers on BulkAcceptOffersActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  offersToAccept {\n    orderData {\n      openedAt\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_bulk_fulfill_orders on BulkFulfillOrdersActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  ordersToFill {\n    orderData {\n      openedAt\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_burnToRedeem on AssetBurnToRedeemActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_cancel_orders on CancelOrderActionType {\n  method {\n    __typename\n    ... on TransactionSubmissionDataType {\n      ...useHandleBlockchainActions_transaction\n    }\n    ... on SignAndPostOrderCancelType {\n      cancelOrderData: data {\n        payload\n        message\n      }\n      serverSignature\n      clientSignatureStandard\n    }\n    ... on GaslessCancelType {\n      orderRelayIds\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_cancel_swap_orders on CancelSwapOrdersActionType {\n  method {\n    __typename\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_create_bulk_order on CreateBulkOrderActionType {\n  method {\n    clientMessage\n    clientSignatureStandard\n    serverSignature\n    orderDatas\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_create_order on CreateOrderActionType {\n  method {\n    clientMessage\n    clientSignatureStandard\n    serverSignature\n    orderData\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_create_swap_order on CreateSwapOrderActionType {\n  method {\n    clientMessage\n    clientSignatureStandard\n    serverSignature\n    swapData\n    chain {\n      identifier\n    }\n  }\n}\n\nfragment useHandleBlockchainActions_deploy_contract on DropContractDeployActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_freeze_asset_metadata on AssetFreezeMetadataActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_fulfill_order on FulfillOrderActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  orderData {\n    openedAt\n  }\n}\n\nfragment useHandleBlockchainActions_fulfill_swap_order on FulfillSwapOrderActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  swapData {\n    openedAt\n  }\n}\n\nfragment useHandleBlockchainActions_mint_asset on MintActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n  startTime\n}\n\nfragment useHandleBlockchainActions_mint_your_own_collection on MintYourOwnCollectionActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_set_creator_fees on SetCreatorFeesActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_swap_asset on AssetSwapActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_transaction on TransactionSubmissionDataType {\n  chain {\n    identifier\n  }\n  ...useTransaction_transaction\n}\n\nfragment useHandleBlockchainActions_transfer_asset on AssetTransferActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_update_drop_mechanics on DropMechanicsUpdateActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useHandleBlockchainActions_update_drop_pre_reveal on CollectionTokenMetadataUpdateActionType {\n  method {\n    ...useHandleBlockchainActions_transaction\n  }\n}\n\nfragment useIsRarityEnabled_collection on CollectionType {\n  slug\n  enabledRarities\n}\n\nfragment useTotalItems_ordersData on OrderDataType {\n  item {\n    __typename\n    ... on AssetQuantityDataType {\n      asset {\n        relayId\n        id\n      }\n    }\n    ... on AssetBundleType {\n      assetQuantities(first: 30) {\n        edges {\n          node {\n            asset {\n              relayId\n              id\n            }\n            id\n          }\n        }\n      }\n    }\n    ... on Node {\n      __isNode: __typename\n      id\n    }\n  }\n}\n\nfragment useTotalPriceOfferDataToAccept_offersToAccept on OfferToAcceptType {\n  itemFillAmount\n  ...readOfferDataToAcceptPerUnitPrice_offerToAccept\n}\n\nfragment useTotalPriceOrderDataToFill_ordersToFill on OrderToFillType {\n  ...readOrderDataToFillPrices_orderDataToFill\n}\n\nfragment useTotalPriceOrderData_orderData on OrderDataType {\n  ...readOrderDataPrices\n}\n\nfragment useTransaction_transaction on TransactionSubmissionDataType {\n  chain {\n    identifier\n  }\n  source {\n    value\n  }\n  destination {\n    value\n  }\n  value\n  data\n}\n',
                    'variables': {
                        'item': {
                            'asset': nft,
                            'quantity': '1',
                        },
                        'price': {
                            'paymentAsset': 'UGF5bWVudEFzc2V0VHlwZTo2NDQ=',
                            'amount': str(price),
                        },
                        'recipient': None,
                        'openedAt': current_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        'closedAt': end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        'englishAuctionReservePrice': None,
                        'optionalCreatorFeeBasisPoints': None,
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id'], auth=auth), payload=json_data, session=session)
                return response['data']['blockchain']['createListingActions'][0]
            except:
                time.sleep(i * 1)
        return None

    def post_order(self, account, auth, session, signature, server_signature, order_data):
        for i in range(5):
            try:
                json_data = {
                    'id': 'useHandleBlockchainActionsCreateOrderMutation',
                    'query': 'mutation useHandleBlockchainActionsCreateOrderMutation(\n  $orderData: JSONString!\n  $clientSignature: String!\n  $serverSignature: String!\n) {\n  orders {\n    create(orderData: $orderData, clientSignature: $clientSignature, serverSignature: $serverSignature) {\n      counterOrder {\n        relayId\n        id\n      }\n      order {\n        relayId\n        orderType\n        side\n        item {\n          __typename\n          relayId\n          displayName\n          tradeSummary {\n            bestAsk {\n              relayId\n              createdDate\n              orderType\n              openedAt\n              closedAt\n              isCancelled\n              isFilled\n              isOpen\n              isValid\n              side\n              priceFnEndedAt\n              perUnitPriceType {\n                unit\n                usd\n                symbol\n              }\n              priceType {\n                unit\n                usd\n                symbol\n              }\n              englishAuctionReservePriceType {\n                unit\n                usd\n                symbol\n              }\n              maker {\n                address\n                id\n              }\n              taker {\n                address\n                id\n              }\n              payment {\n                symbol\n                id\n              }\n              id\n            }\n          }\n          ... on AssetBundleType {\n            ...bundle_url\n          }\n          ...itemEvents_dataV2\n          ... on Node {\n            __isNode: __typename\n            id\n          }\n        }\n        id\n      }\n      transaction {\n        blockExplorerLink\n        chain {\n          identifier\n        }\n        transactionHash\n        id\n      }\n    }\n  }\n}\n\nfragment bundle_url on AssetBundleType {\n  slug\n  chain {\n    identifier\n  }\n}\n\nfragment itemEvents_dataV2 on ItemType {\n  __isItemType: __typename\n  relayId\n  chain {\n    identifier\n  }\n  ... on AssetType {\n    tokenId\n    assetContract {\n      address\n      id\n    }\n  }\n}\n',
                    'variables': {
                        'orderData': order_data,
                        'clientSignature': signature,
                        'serverSignature': server_signature,
                    },
                }
                response = self.help.fetch_tls(url='https://opensea.io/__api/graphql/', type='post', headers=self.get_headers(account, operation=json_data['id'], auth=auth), payload=json_data, session=session)
                if response['data']:
                    return True
            except:
                time.sleep(i * 1)
        return None

    def list_nft(self, private_key, attempt = 0, auth=None, session=None):

        if attempt > 10:
            return 'error'
        elif attempt != 0:
            time.sleep(1)

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        #if session is None:
        session = self.help.get_tls_session()

        if auth is None:
            auth = self.get_auth(account, session)
            if not auth:
                return self.list_nft(private_key=private_key, attempt=attempt+1, auth=auth, session=session)

        nfts = self.get_users_nfts(account, auth, session)
        if not nfts:
            return 'no_nft'
        nft = random.choice(nfts)

        res = check_approve(new_w3, account, nft['assetContract']['address'], markets_data[self.project]['contract'], nft=True)
        if not res:
            make_approve(new_w3, account, nft['assetContract']['address'], markets_data[self.project]['contract'], nft=True)

        try:
            price = float(nft['assetCollection']['statsV2']['floorPrice']['unit']) * random.uniform(1.5, 5)
        except:
            price = random.uniform(0.1, 0.5)

        sell_data = self.get_sell_order(account, auth, session, nft['relayId'], price)
        if not sell_data:
            return self.list_nft(private_key=private_key, attempt=attempt + 1, auth=auth, session=session)

        eip712_message_str = sell_data['method']['clientMessage']
        eip712_message = json.loads(eip712_message_str)

        message = self.fix_data_types(eip712_message)
        encoded_message = encode_structured_data(message)
        signed_message = Account.sign_message(encoded_message, private_key['private_key'])

        post = self.post_order(account, auth, session, signed_message.signature.hex(), sell_data['method']['serverSignature'], sell_data['method']['orderData'])
        if not post:
            return self.list_nft(private_key=private_key, attempt=attempt + 1, auth=auth, session=session)
        else:
            self.logger.log_success(f"{self.project} | Успешно залистил NFT ({nft['name']} #{nft['tokenId']}) за {round(price, 6)} ETH", wallet=account.address)
            return True

class Alienswap():

    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'ALIENSWAP'
        self.logger = logger

    def get_headers(self, auth=None):
        headers = {
            'authority': 'alienswap.xyz',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'expires': '0',
            'pragma': 'no-cache',
            'referer': 'https://alienswap.xyz',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }
        if auth:
            headers['authorization'] = f"Bearer {auth}"
        return headers

    def get_auth(self, account, session):
        for i in range(3):
            try:
                message_ = 'Welcome to AlienSwap!\nClick to sign in and accept the AlienSwap Terms of Service.\nThis request will not trigger a blockchain transaction or cost any gas fees.'
                message = message_.encode()
                message_to_sign = encode_defunct(primitive=message)
                signed_message = self.w3.eth.account.sign_message(message_to_sign, private_key=account._private_key.hex())
                sig = signed_message.signature.hex()
                json_data = {
                    'address': account.address,
                    'signature': sig,
                    'nonce': 'Welcome to AlienSwap!\nClick to sign in and accept the AlienSwap Terms of Service.\nThis request will not trigger a blockchain transaction or cost any gas fees.',
                    'src': 4,
                    'network': 'base',
                    'inviter': 'z47xmV',
                }
                response = self.help.fetch_tls(url='https://alienswap.xyz/alien-api/api/v1/public/user/signin', type='post', headers=self.get_headers(), payload=json_data, session=session)
                return response['data']['access_token']
            except:
                time.sleep(i*1)
        return None

    def get_collections(self, auth, session):
        for i in range(3):
            try:
                response = self.help.fetch_tls(url='https://alienswap.xyz/api/statistics/ranking/collection?sort_field=market_cap&sort_direction=desc&limit=1000&chainId=8453', type='get', headers=self.get_headers(auth=auth), session=session)
                collections = []
                for col in response['data']:
                    try:
                        if float(col['floor_price']) <= self.max_price:
                            collections.append(col)
                    except:
                        pass
                return collections
            except:
                time.sleep(i*1)
        return []

    def get_nfts(self, auth, session, collection):
        for i in range(3):
            try:
                url = 'https://alienswap.xyz/api/market/base/tokens/v6'
                params = {
                    'collection': str(collection).lower(),
                    'includeAttributes': 'true',
                    'includeLastSale': 'true',
                    'includeTopBid': 'true',
                    'includeDynamicPricing': 'true',
                    'limit': '50',
                    'flagStatus': '0',
                }
                response = self.help.fetch_tls(url=url, type='get', headers=self.get_headers(), session=self.help.get_tls_session(), params=params)
                nfts = []
                for nft in response['tokens']:
                    try:
                        if float(nft['market']['floorAsk']['price']['amount']['native']) <= self.max_price:
                            nfts.append(nft)
                    except:
                        pass
                return random.choice(nfts)
            except:
                time.sleep(i*1)
        return None

    def get_buy_data(self, auth, session, account, token):
        for i in range(3):
            try:
                payload = {"items":[{"token":f"{token['token']['contract']}:{token['token']['tokenId']}"}],"taker":account.address,"source":"alienswap.xyz"}
                response = self.help.fetch_tls(url='https://alienswap.xyz/api/market/base/execute/buy/v7', type='post', headers=self.get_headers(auth=auth), session=session, payload=payload)
                try:
                    return response['steps'][0]['items'][0]['data']
                except:
                    return response['steps'][-1]['items'][0]['data']
            except:
                time.sleep(i*1)
        return []

    def buy_nft(self, private_key, max_price, attempt = 0, auth=None, session=None):

        if attempt > 10:
            return 'error'
        elif attempt != 0:
            time.sleep(1)

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        self.max_price = max_price

        #if session is None:
        session = self.help.get_tls_session()

        if auth is None:
            auth = self.get_auth(account, session)
            if not auth:
                return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)

        collections = self.get_collections(auth, session)
        if not collections:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1, auth=auth, session=session)

        collection = random.choice(collections)

        nft = self.get_nfts(auth, session, collection['contract_address'])
        if not nft:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1, auth=auth, session=session)

        buy_data = self.get_buy_data(auth, session, account, nft)
        if not buy_data:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1, auth=auth, session=session)

        tx = make_tx(new_w3, account, value=int(buy_data['value'], 16), to=buy_data['to'], data=buy_data['data'])
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt+1, auth=auth, session=session)

        self.logger.log_success( f"{self.project} | Успешно купил NFT ({nft['token']['name']}) за {nft['market']['floorAsk']['price']['amount']['native']} ETH", wallet=account.address)
        return new_w3.to_hex(hash)

    def get_user_nfts(self, auth, session, account):
        for i in range(3):
            try:
                params = {
                    'limit': '200',
                    'includeTopBid': 'true',
                    'includeLastSale': 'true',
                }
                response = self.help.fetch_tls(url=f'https://alienswap.xyz/api/market/base/users/{account.address.lower()}/tokens/v7', type='get', headers=self.get_headers(), session=self.help.get_tls_session(), params=params)
                eligable = []
                for token in response['tokens']:
                    if int(token['ownership']['onSaleCount']) == 0:
                        eligable.append(token)
                return eligable
            except:
                time.sleep(i*1)
        return None

    def get_sell_data(self, auth, session, account, price, token):
        for i in range(3):
            try:
                payload = {"maker":account.address.lower(),"source":"alienswap.xyz","params":[{"token":f"{token['token']['contract']}:{token['token']['tokenId']}","weiPrice":str(price),"orderKind":"alienswap","orderbook":"reservoir","expirationTime":str(int(time.time())+ 60*60*24*90),"options":{"alienswap":{"useOffChainCancellation":True}},"automatedRoyalties":False}]}
                response = self.help.fetch_tls(url=f'https://alienswap.xyz/api/market/base/execute/list/v5', type='post', headers=self.get_headers(), session=self.help.get_tls_session(), payload=payload)
                return response['steps']
            except:
                time.sleep(i*1)
        return None

    def fix_data_types(self, original_message):
        _message = original_message.copy()
        _message['domain']['chainId'] = int(_message['domain']['chainId'])
        message = _message['message']
        message['zoneHash'] = self.w3.to_bytes(hexstr=message['zoneHash'][2:])
        message['salt'] = int(message['salt'])
        message['conduitKey'] = self.w3.to_bytes(hexstr=message['conduitKey'][2:])
        message['startTime'] = int(message['startTime'])
        message['endTime'] = int(message['endTime'])
        message['orderType'] = int(message['orderType'])
        message['counter'] = int(message['counter'])
        #message['totalOriginalConsiderationItems'] = int(message['totalOriginalConsiderationItems'])

        for offer in message['offer']:
            offer['itemType'] = int(offer['itemType'])
            offer['identifierOrCriteria'] = int(offer['identifierOrCriteria'])
            offer['startAmount'] = int(offer['startAmount'])
            offer['endAmount'] = int(offer['endAmount'])

        for consideration in message['consideration']:
            consideration['itemType'] = int(consideration['itemType'])
            consideration['identifierOrCriteria'] = int(consideration['identifierOrCriteria'])
            consideration['startAmount'] = int(consideration['startAmount'])
            consideration['endAmount'] = int(consideration['endAmount'])

        return _message

    def post_order(self, auth, session, signarute, post):
        for i in range(3):
            try:
                url = f"https://alienswap.xyz/api/market/base/order/v3?signature={signarute}"
                payload = post
                response = self.help.fetch_tls(url=url, type='post', headers=self.get_headers(auth), session=self.help.get_tls_session(), payload=payload)
                if response.get('message', 'bad') == 'Success':
                    return True
            except:
                time.sleep(i*1)
        return None

    def list_nft(self, private_key, attempt=0, auth=None, session=None):

        if attempt > 10:
            return 'error'
        elif attempt != 0:
            time.sleep(1)

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        #if session is None:
        session = self.help.get_tls_session()

        if auth is None:
            auth = self.get_auth(account, session)
            if not auth:
                return self.list_nft(private_key=private_key, attempt=attempt + 1, auth=auth, session=session)

        nfts = self.get_user_nfts(auth, session, account)
        if not nfts:
            return self.list_nft(private_key, attempt=attempt+6)
        nft = random.choice(nfts)

        try:
            price = int(int(nft['collection']['floorAskPrice']['amount']['raw']) * random.uniform(1.5, 5))
        except:
            price = int(random.uniform(0.1, 0.5) * 10 ** 18)

        sell_data = self.get_sell_data(auth, session, account, price, nft)
        if not sell_data:
            return self.list_nft(private_key=private_key, attempt=attempt + 1, auth=auth, session=session)

        if sell_data[0]['items'][0]['status'] != 'complete':
            res = check_approve(new_w3, account, nft['token']['contract'], markets_data[self.project]['contract'], nft=True)
            if not res:
                make_approve(new_w3, account, nft['token']['contract'], markets_data[self.project]['contract'], nft=True)

        sign_data = sell_data[1]['items'][0]['data']

        message = sign_data['sign']
        message['types']['EIP712Domain'] = [
            {
                "name": "name",
                "type": "string"
            },
            {
                "name": "version",
                "type": "string"
            },
            {
                "name": "chainId",
                "type": "uint256"
            },
            {
                "name": "verifyingContract",
                "type": "address"
            }
        ]
        message_to_sign = {
            'domain': message['domain'],
            'types': message['types'],
            'message': message['value'],
            'primaryType': message['primaryType']
        }
        message_fixed = self.fix_data_types(message_to_sign)
        encoded_message = encode_structured_data(message_fixed)
        signed_message = Account.sign_message(encoded_message, private_key['private_key'])

        post = self.post_order(auth, session, signed_message.signature.hex(), sign_data['post']['body'])
        if not post:
            return self.list_nft(private_key=private_key, attempt=attempt + 1, auth=auth, session=session)
        else:
            self.logger.log_success( f"{self.project} | Успешно залистил NFT ({nft['token']['name']} #{nft['token']['tokenId']}) за {round(price/(10**18), 6)} ETH", wallet=account.address)
            return True

class Zonic():

    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'ZONIC'
        self.logger = logger
        self.contract = w3.eth.contract(address=w3.to_checksum_address(markets_data[self.project]['contract']), abi=markets_data[self.project]['ABI'])

    def get_collections(self):
        for i in range(3):
            try:
                payload = {"item_per_page": 250, "page": 0, "chain_id": 8453}
                collections = self.help.fetch_url(url='https://api.nftnest.io/v1/explore/get_collections', type='post', payload=payload)
                eligble_collections = []
                for col in collections['contracts']:
                    try:
                        if int(col['collection_info']['listed_count']) > 0 and int(col['floor_price'], 16) <= self.max_price * 10 ** 18:
                            eligble_collections.append(col)
                    except:
                        pass
                collection = random.choice(eligble_collections)
                return collection
            except:
                time.sleep((i+i)*1)
        return None

    def get_items(self, contract):
        for i in range(3):
            try:
                payload = {"contract_address": contract, "chain": "base", "sort_by": "price_lowest", "page": 0, "attributes": [], "name": ""}
                items = self.help.fetch_url(url ='https://api.nftnest.io/v1/collection/get_nfts', type='post', payload=payload)
                items = items["tokens"]
                for i in items['8453']:
                    return i['contract_address'], str(int(i['token_id'], 16))
            except:
                time.sleep((i + i) * 1)
        return None, None

    def get_data(self, token_id, contract):
        for i in range(3):
            try:
                payload = {"contract_address": contract, "token_id": token_id, "chain_id": 8453}
                res = self.help.fetch_url(url ='https://api.nftnest.io/v1/marketplace/listing/get', type='post', payload=payload)
                sig_data = res['active_listing']['signature']
                sale_id = res['active_listing']['sale_id']
                list_price = int(res['active_listing']['list_price'], 16)
                listing = res['active_listing']['data']['message']
                payload = {"sale_id": sale_id, "chain_id": 8453}
                res_sig = self.help.fetch_url(url ='https://api.nftnest.io/v1/marketplace/listing/get_purchase_sig', type='post', payload=payload)
                expired_at = res_sig['expired_at']
                r = res_sig['r']
                s = res_sig['s']
                v = res_sig['v']
                return sig_data, expired_at, r, s, v, list_price, listing
            except:
                time.sleep((i + i) * 1)
        return None, None, None, None, None, None, None

    def buy_nft(self, private_key, max_price):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])
        self.max_price = max_price

        collection = self.get_collections()
        if not collection:
            return 'no_col'
        contract, token_id = self.get_items(collection['contract_address'])
        if not contract:
            return 'no_nft'

        sig_data, expired_at, r, s, v, list_price, message = self.get_data(token_id, contract)
        if not sig_data:
            return 'no_data'

        listing = [
            new_w3.to_checksum_address(message['offerer']),
            [
                [
                    offer['itemType'],
                    new_w3.to_checksum_address(offer['token']),
                    int(offer['identifier']),
                    offer['amount']
                ] for offer in message['offers']
            ],
            [
                message['offererPayout']['itemType'],
                new_w3.to_checksum_address(message['offererPayout']['token']),
                int(message['offererPayout']['identifier']),
                new_w3.to_checksum_address(message['offererPayout']['recipient']),
                int(message['offererPayout']['amount'])
            ],
            [
                [
                    payout['itemType'],
                    new_w3.to_checksum_address(payout['token']),
                    int(payout['identifier']),
                    new_w3.to_checksum_address(payout['recipient']),
                    int(payout['amount'])
                ] for payout in message['creatorPayouts']
            ],
            message['orderType'],
            message['listedAt'],
            message['expiredAt'],
            message['saleId'],
            message['version']
        ]
        signature = sig_data
        adminSignatureV = int(v)
        adminSignatureR = r
        adminSignatureS = s
        adminSigExpiredAt = int(expired_at)

        args = listing, signature, adminSignatureV, adminSignatureR, adminSignatureS, adminSigExpiredAt
        func_ = getattr(self.contract.functions, 'fulfillBasicOrder')

        tx = make_tx(new_w3, account, value=list_price, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        self.logger.log_success(f"{self.project} | Успешно купил NFT ({collection['collection_info']['name']}) за {round(int(list_price) / 10 ** 18, 6)} ETH", wallet=account.address)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.buy_nft(private_key=private_key, max_price=max_price)
        return new_w3.to_hex(hash)

    def get_price(self, contract_address):
        payload = {"contract_address": contract_address, "chain": "base"}
        res = self.help.fetch_url(url='https://api.nftnest.io/v1/collection/summary', type='post', payload=payload)
        try:
            price = int(res['summary']['floor_price'], 16)
        except:
            price = int(0.05 * 10 ** 18)
        return int(price * random.uniform(1.5, 5))

    def sign_and_post(self, contract_address, token_id, account, creator_payouts=["0xC353dE8af2eE32DA2eeaE58220D3c8251eE1aDcf", 250]):
        chainId = 8453
        types = { "OfferItem": [ { "name": "itemType", "type": "uint8" }, { "name": "token", "type": "address" }, { "name": "identifier", "type": "uint256" }, { "name": "amount", "type": "uint256" } ], "Payout": [ { "name": "itemType", "type": "uint8" }, { "name": "token", "type": "address" }, { "name": "identifier", "type": "uint256" }, { "name": "recipient", "type": "address" }, { "name": "amount", "type": "uint256" } ], "Listing": [ { "name": "offerer", "type": "address" }, { "name": "offers", "type": "OfferItem[]" }, { "name": "offererPayout", "type": "Payout" }, { "name": "creatorPayouts", "type": "Payout[]" }, { "name": "orderType", "type": "uint8" }, { "name": "listedAt", "type": "uint32" }, { "name": "expiredAt", "type": "uint32" }, { "name": "saleId", "type": "address" }, { "name": "version", "type": "uint8" } ], "EIP712Domain": [ { "name": "name", "type": "string" }, { "name": "version", "type": "string" }, { "name": "chainId", "type": "uint256" }, { "name": "verifyingContract", "type": "address" } ] }
        primary_type = "Listing"

        price = self.get_price(contract_address)

        def generate_message_for_listing(chain_id, connected_address, contract_address, token_id, price, creatorPayouts=None, listingInterval=60 * 60 * 24 * 30):
            wallet_address = self.w3.eth.account.create().address
            current_time = int(datetime.now().timestamp()) + int(listingInterval)

            price_decimal = ''
            for i in range(len(str(price))):
                price_decimal += str(price)[i] if i < 4 else '0'
            price_decimal = int(price_decimal)

            creator_payouts = []

            if creatorPayouts:
                creator_address, creator_fee = creatorPayouts

                if creator_fee > 10:
                    return {
                        'success': False,
                        'error': 'Creator Fee could not be more than 10%'
                    }

                creator_fee_amount = int((price_decimal * creator_fee * 100 / 10000))
                marketplace_fee_amount = int((price_decimal * 250 / 10000))
                offerer_payout_amount = int(price_decimal - (creator_fee_amount + marketplace_fee_amount))

                if offerer_payout_amount <= 0:
                    return {
                        'success': False,
                        'error': 'Unexpected Error'
                    }

                offerer_payout = {
                    'itemType': 0,
                    'token': '0x0000000000000000000000000000000000000000',
                    'identifier': 0,
                    'recipient': connected_address,
                    'amount': int(offerer_payout_amount)
                }

                creator_payouts.append({
                    'itemType': 0,
                    'token': '0x0000000000000000000000000000000000000000',
                    'identifier': 0,
                    'recipient': creator_address,
                    'amount': int(creator_fee_amount)
                })
            else:

                creator_fee_percentage = 250
                offerer_payout_amount = price_decimal - int((price_decimal * creator_fee_percentage / 10000))

                offerer_payout = {
                    'itemType': 0,
                    'token': '0x0000000000000000000000000000000000000000',
                    'identifier': 0,
                    'recipient': connected_address,
                    'amount': int(offerer_payout_amount)
                }

                creator_payouts.append({
                    'itemType': 0,
                    'token': '0x0000000000000000000000000000000000000000',
                    'identifier': 0,
                    'recipient': connected_address,
                    'amount': 0
                })

            domain = {
                'chainId': chain_id,
                'name': 'Zonic : NFT Marketplace for L2',
                'verifyingContract': '0xdc7d3F21132e7fa9df6602A6E87fcbD49183A728',
                'version': '1'
            }

            message = {
                'offerer': connected_address,
                'offers': [{
                    'itemType': 2,
                    'token': contract_address,
                    'identifier': token_id,
                    'amount': 1
                }],
                'offererPayout': offerer_payout,
                'creatorPayouts': creator_payouts,
                'orderType': 2,
                'listedAt': 0,
                'expiredAt': current_time,
                'saleId': wallet_address,
                'version': 1
            }

            return {
                'success': True,
                'domain': domain,
                'message': message
            }

        data = generate_message_for_listing(chainId, account.address, contract_address, token_id, price, creatorPayouts=creator_payouts)

        if not data['success']:
            return data, price

        domain = data['domain']
        message = data['message']

        structured_message = {
            'types': types,
            'primaryType': primary_type,
            'domain': domain,
            'message': message,
        }

        encoded_message = encode_structured_data(structured_message)
        signed_message = Account.sign_message(encoded_message, account._private_key.hex())
        signature = signed_message.signature.hex()

        domain = {
            "chainId": "0x2105",
            "name": "Zonic : NFT Marketplace for L2",
            "verifyingContract": "0xdc7d3F21132e7fa9df6602A6E87fcbD49183A728",
            "version": "1"
        }
        message['creatorPayouts'][0]['amount'] = str(message['creatorPayouts'][0]['amount'])
        message['offererPayout']['amount'] = str(message['offererPayout']['amount'])
        message['offers'][0]['identifier'] = str(message['offers'][0]['identifier'])
        payload = {"listing_type": "basic", "chain_id": 8453, "contract_address": contract_address,
                   "token_id": str(token_id), "data": {"types": types,
                "primaryType": primary_type, "domain": domain,
                "message": message}, "signature": signature}
        res = self.help.fetch_url(url='https://api.nftnest.io/v1/marketplace/listing/create', type='post', payload=payload)
        return res, price

    def get_nfts(self, account):
        for i in range(3):
            try:
                payload = {"address": account.address, "chain": "base", "page": 0, "sort_by": "listed_lowest_price", "contract_addresses": "", "name": ""}
                res = self.help.fetch_url(url='https://api.nftnest.io/v1/wallet/get_nfts', type='post', payload=payload)
                eligable_tokens = []
                for token in res['tokens']['8453']:
                    if not token.get('active_listing', False):
                        eligable_tokens.append(token)
                if eligable_tokens:
                    token = random.choice(eligable_tokens)
                else:
                    return False, False
                try:
                    creator_earnings = res.json()['contracts']['8453'][token["contract_address"]]['creator_earnings']
                except:
                    creator_earnings = []
                return token, creator_earnings
            except:
                time.sleep((i+1)*i)
        return None, None

    def list_nft(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.help.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        token, creator_earnings = self.get_nfts(account)
        if not token:
            return 'no_nft'

        if creator_earnings:
            creator_earnings = [creator_earnings[0]["payout_address"], int(creator_earnings[0]["percentage"])]
        else:
            creator_earnings = []


        res = check_approve(new_w3, account, token['contract_address'], markets_data[self.project]['contract'], nft=True)
        if not res:
            make_approve(new_w3, account, token['contract_address'], markets_data[self.project]['contract'], nft=True)

        result, price = self.sign_and_post(token['contract_address'], int(token['token_id'], 16), account, creator_payouts=creator_earnings)

        if result.get("success", False):
            try:
                token_name = token['token_info']['metadata']['name']
            except:
                token_name = 'UNKNOWN'
            self.logger.log_success(f"{self.project} | Успешно залистил NFT ({token_name}) за {round(int(price) / 10 ** 18, 6)} ETH", wallet=account.address)
            return True
        else:
            return

class Coinbase():

    def __init__(self, w3, logger, helper):
        self.help = helper
        self.w3 = w3
        self.project = 'COINBASE'
        self.logger = logger

class Kreatorland():

    def __init__(self, w3, logger, helper):
        self.w3 = w3
        self.helper = helper
        self.logger = logger
        self.project = 'KREATORLAND'
        self.contract = w3.eth.contract(address=w3.to_checksum_address(markets_data[self.project]['contract']), abi=markets_data[self.project]['ABI'])
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Authorization': 'Token',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': "basend.kreatorland.com",
            'Origin': 'https://kreatorland.com',
            'Referer': 'https://kreatorland.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        self.subheaders = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Referer': 'https://kreatorland.com/explore/zksync-era',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def get_collections(self):
        for i in range(5):
            try:
                url = 'https://basend.kreatorland.com/api/collection/?limit=4000&network=8453&offset=0'
                res = self.helper.fetch_url(url=url, type='get', headers=self.headers)
                collections = []
                for col in res['results']:
                    try:
                        if int(col['listed']) > 0 and self.w3.from_wei(int(col['floor']), 'gwei') <= self.max_price:
                            collections.append(col)
                    except:
                        pass
                return collections
            except:
                time.sleep(i*1)

        return None

    def get_nft(self, contract):
        for i in range(10):
            try:
                url = f'https://basend.kreatorland.com/api/collection/{contract}/tokens/?%20%20&&availability=forSale&sort=&query=&currency=all&?network=8453'
                #url = f'https://backend.kreatorland.com/api/collection/{contract}/activity/?event=SA&%20%20&activity_sort=timestamp:desc&&currency=all&?network=324'
                res = self.helper.fetch_url(url=url, type='get', headers=self.headers)
                nfts = []
                for nft in res['results']:
                    if self.w3.from_wei(int(nft['sell_order']['price']), 'gwei') <= self.max_price:
                        nfts.append(nft)
                return nfts
            except:
                time.sleep((i+1) * 1)
        return None

    def get_token_sale(self, order):
        for i in range(5):
            try:
                url = f'https://basend.kreatorland.com/api/sellorder/{order}/?network=8453'
                res = self.helper.fetch_url(url=url, type='get', headers=self.headers)
                return res
            except:
                time.sleep(i * 1)
        return None

    def extract_args_from_json(self, data):

        offer_parameters_ = json.loads(data["order_json"])
        offer_parameters = offer_parameters_["parameters"]

        offer_items = offer_parameters["offer"][0]

        considerations_list = []
        for consideration in offer_parameters["consideration"]:
            considerations_list.append([
                consideration["itemType"],
                consideration["token"],
                int(consideration["identifierOrCriteria"]),
                int(consideration["startAmount"]),
                int(consideration["endAmount"]),
                consideration["recipient"]
            ])

        data_ = [[
            [
                offer_parameters["offerer"],
                offer_parameters["zone"],
                [
                    [
                        offer_items["itemType"],
                        offer_items["token"],
                        int(offer_items["identifierOrCriteria"]),
                        int(offer_items["startAmount"]),
                        int(offer_items["endAmount"])
                    ]
                ],
                considerations_list,
                offer_parameters["counter"],
                int(offer_parameters["startTime"]),
                int(offer_parameters["endTime"]),
                offer_parameters["zoneHash"],
                int(offer_parameters["salt"], 16),
                offer_parameters["conduitKey"],
                offer_parameters["totalOriginalConsiderationItems"]
            ],
            offer_parameters_["signature"]
        ],
        offer_parameters["conduitKey"]]

        return data_

    def buy_nft(self, private_key, max_price, attempt = 0):

        if attempt > 5:
            return 'error'
        elif attempt != 0:
            time.sleep(10)

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        self.max_price = max_price
        account = new_w3.eth.account.from_key(private_key['private_key'])

        cols = self.get_collections()
        if not cols:
            return self.buy_nft(private_key, max_price, attempt=attempt + 1)

        col = random.choice(cols)

        nfts = self.get_nft(col['address'])
        if not nfts:
            return self.buy_nft(private_key, max_price, attempt=attempt + 1)

        nft = random.choice(nfts)

        id = nft['sell_order']['id']

        func_ = getattr(self.contract.functions, 'fulfillOrder')

        data = self.get_token_sale(id)
        if not data:
            return self.buy_nft(private_key, max_price, attempt=attempt + 1)

        args = self.extract_args_from_json(data)

        value = self.w3.to_wei(int(data['price']), 'gwei')
        tx = make_tx(self.w3, account, value=value, func=func_, args=args, args_positioning=True)

        if tx == "low_native" or not tx:
            return tx
        if tx == 'kreatora_rerun':
            return self.buy_nft(private_key, max_price, attempt=attempt + 1)
        if tx == 'order_filled':
            return self.buy_nft(private_key, max_price, attempt=attempt + 1)

        sign = account.sign_transaction(tx)
        hash = self.w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.buy_nft(private_key=private_key, max_price=max_price, attempt=attempt + 1)
        try:
            name = nft['collection']['name']
        except:
            name = 'UNKNOWN'

        self.logger.log_success(f"{self.project} | Успешно купил NFT ({name}) за {round(value / 10 ** 18, 6)} ETH", wallet=account.address)
        return self.w3.to_hex(hash)

    def get_build_id(self):
        for i in range(5):
            try:
                page = self.helper.fetch_url(url='https://kreatorland.com/', type='get', text=True)
                if page:
                    start_index = page.find('<script id="__NEXT_DATA__" type="application/json">') + len('<script id="__NEXT_DATA__" type="application/json">')
                    end_index = page.find('</script>', start_index)
                    json_data = page[start_index:end_index]
                    data = json.loads(json_data)
                    build_id = data.get('buildId')
                    return build_id
                else:
                    raise Exception
            except Exception:
                time.sleep(1)
        return None

    def get_royalies(self, id):
        for i in range(2):
            try:
                build_id = self.get_build_id()
                url = f'https://kreatorland.com/_next/data/{build_id}/collection/base/{id}.json'
                params = {
                    'collection': 'base',
                    'collectionId': id,
                }
                res = self.helper.fetch_url(url=url, type='get', params=params, retries=5, timeout=5)
                return res['pageProps']
            except:
                time.sleep(i * 1)
        return None

    def get_nfts(self, account):
        for i in range(5):
            try:
                url = f'https://basend.kreatorland.com/api/profile/{account.address.lower()}/erc721tokens/?&availability=notListed&sort=price:desc&&query=&currency=all&chain=[8453]'
                res = self.helper.fetch_url(url=url, type='get')
                return res['results']
            except:
                time.sleep(i * 1)
        return None

    def make_sell_order(self, token_address, token_id, price_amount, account, fees=[]):

        marketplace_fee_amount = int(price_amount * 0.01)  # 1% of the amount
        remainder_after_fee = price_amount - marketplace_fee_amount

        considerations_list = [
            {
                'itemType': 0,
                'token': '0x0000000000000000000000000000000000000000',
                'identifierOrCriteria': '0',
                'startAmount': str(marketplace_fee_amount),
                'endAmount': str(marketplace_fee_amount),
                'recipient': self.w3.to_checksum_address(markets_data[self.project]['fee_address']),
            },
            {
                'itemType': 0,
                'token': '0x0000000000000000000000000000000000000000',
                'identifierOrCriteria': '0',
                'startAmount': str(remainder_after_fee),
                'endAmount': str(remainder_after_fee),
                'recipient': account.address,
            },
        ]

        for fee in fees:
            amount_for_fee = int(price_amount * (fee["percentage"] / 100))
            considerations_list.append({
                'itemType': 0,
                'token': '0x0000000000000000000000000000000000000000',
                'identifierOrCriteria': '0',
                'startAmount': str(amount_for_fee),
                'endAmount': str(amount_for_fee),
                'recipient': self.w3.to_checksum_address(fee["address"]),
            })
            considerations_list[1]['startAmount'] = str(int(considerations_list[1]['startAmount'])-amount_for_fee)
            considerations_list[1]['endAmount'] = str(int(considerations_list[1]['endAmount']) - amount_for_fee)

        start_time = int(time.time())
        end_time = start_time + 60*60*24*30*6

        data = {
            'offerer': account.address,
            'zone': '0x0000000000000000000000000000000000000000',
            'zoneHash': '0x3000000000000000000000000000000000000000000000000000000000000000',
            'startTime': str(start_time),
            'endTime': str(end_time),
            'orderType': 0,
            'offer': [
                {
                    'itemType': 2,
                    'token': self.w3.to_checksum_address(token_address),
                    'identifierOrCriteria': str(token_id),
                    'startAmount': '1',
                    'endAmount': '1',
                },
            ],
            'consideration':considerations_list,
            'totalOriginalConsiderationItems': len(considerations_list),
            'salt': ''.join(random.choice('0123456789') for _ in range(64)),
            'conduitKey': '0x0000000000000000000000000000000000000000000000000000000000000000',
            'counter': 0,
        }

        return data

    def fix_data_types(self, original_message):
        message = original_message.copy()
        message['zoneHash'] = self.w3.to_bytes(hexstr=message['zoneHash'][2:])
        message['salt'] = self.w3.to_bytes(hexstr=message['salt'][2:])
        message['conduitKey'] = self.w3.to_bytes(hexstr=message['conduitKey'][2:])
        message['startTime'] = int(message['startTime'])
        message['endTime'] = int(message['endTime'])
        message['orderType'] = int(message['orderType'])
        message['counter'] = int(message['counter'])
        message['totalOriginalConsiderationItems'] = int(message['totalOriginalConsiderationItems'])

        for offer in message['offer']:
            offer['itemType'] = int(offer['itemType'])
            offer['identifierOrCriteria'] = int(offer['identifierOrCriteria'])
            offer['startAmount'] = int(offer['startAmount'])
            offer['endAmount'] = int(offer['endAmount'])

        for consideration in message['consideration']:
            consideration['itemType'] = int(consideration['itemType'])
            consideration['identifierOrCriteria'] = int(consideration['identifierOrCriteria'])
            consideration['startAmount'] = int(consideration['startAmount'])
            consideration['endAmount'] = int(consideration['endAmount'])

        return message

    def generate_sha256_hash(self, data='creatora'):
        sha256 = hashlib.sha256()
        sha256.update(data.encode('utf-8'))
        return sha256.hexdigest()

    def post_listing(self, message, signature):
        for i in range(3):
            try:
                json_data = {
                    'order': {
                        'parameters': message,
                        'signature': signature,
                    },
                    'orderHash': self.generate_sha256_hash(),
                    'network': 8453,
                }
                res = self.helper.fetch_url(url='https://basend.kreatorland.com/api/sellorder/', type='post', payload=json_data, retries=5)
                return res
            except:
                time.sleep(i * 1)
        return None

    def list_nft(self, private_key, attempt = 0):

        if attempt > 5:
            return 'error'
        elif attempt != 0:
            time.sleep(10)

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        nfts = self.get_nfts(account)
        if not nfts:
            return "no_route"
        nft = random.choice(nfts)

        fees_data = self.get_royalies(nft['collection']['slug'])
        if not fees_data:
            return self.list_nft(private_key, attempt = attempt+1)

        try:
            fees = [{"address": fees_data['collection']['payout_address'], "percentage": int(fees_data['collection']['royalty_per_mille'])}]
        except:
            fees = []

        try:
            price = int(fees_data['collection']['floor']) * random.uniform(1.5, 15)
            price = self.w3.to_wei(int(price), 'gwei')
        except:
            price = int(random.uniform(0.1, 0.5) * 10 ** 18)

        message = self.make_sell_order(fees_data['collection']['address'], nft['token_id'], price, account, fees=fees)
        message_to_sign = self.fix_data_types(message)

        domain = {
                'name': 'KreatorLand',
                'version': '1.0.0',
                'chainId': 324,
                'verifyingContract': markets_data[self.project]['contract'].lower()
                  }

        structured_message = {
            'types': markets_data[self.project]['listing_types'],
            'primaryType': 'Order',
            'domain': domain,
            'message': message_to_sign,
        }

        encoded_message = encode_structured_data(structured_message)
        signed_message = Account.sign_message(encoded_message, account._private_key.hex())
        signature = signed_message.signature.hex()

        res = check_approve(self.w3, account, fees_data['collection']['address'], markets_data[self.project]['contract'], nft=True)
        if not res:
            make_approve(self.w3, account, fees_data['collection']['address'], markets_data[self.project]['contract'], nft=True)

        res = self.post_listing(message, signature)
        if not res:
            return self.list_nft(private_key, attempt=attempt + 1)
        if res['active'] == True:
            try:
                name = nft['collection']['name']
            except:
                name = 'UNKNOWN'
            self.logger.log_success(f"{self.project} | Успешно залистил NFT ({name}) за {round(price / (10 ** 18), 6)} ETH", account.address)
            return True
        return

def initialize_nft_markets(classes_to_init, w3, logger, helper):
    available_swaps = {
        "Opensea": Opensea,
        "Element": Element,
        "Alienswap": Alienswap,
        "Zonic": Zonic,
        "Kreatorland": Kreatorland,
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, logger, helper)

    return initialized_objects

