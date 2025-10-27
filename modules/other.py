from modules.name_services import generate_name
from requests_toolbelt import MultipartEncoder
from helpers.data import other_data, NULL_ADDRESS
from helpers.utils import *
import random, string, json, uuid

def generate_collection_name():
    prefixes = ['Crypto', 'NFT', 'Digital', 'Art', 'Linea', 'Virtual', 'Collectible', 'Magic', 'Space', 'Galactic', 'Pixel', 'Dream',
                'Quantum', 'Rainbow', 'Kryptonite', 'Time', 'Cyber', 'Unicorn', 'Blockchain', 'Token', 'Ether', 'Decentralized', 'Tech', 'Smart', 'Solid',
                'Meta', 'Web', 'Mystic', 'Star', 'Future', 'Cyberpunk', 'Neo', 'Cosmic', 'Satoshi', 'Moon', 'HODL', 'FOMO', 'DeFi', 'Yield', 'NFTY',
                'Crystal', 'Dream', 'Future', 'Eon', 'Infinity', 'Fusion', 'Cosmos', 'Linea', 'Layer2', 'L2', 'Chain', 'Plasma', 'Stellar', 'Solaris']

    suffixes = ['Hub', 'Network', 'Platform', 'World', 'Base', 'Zone', 'Galaxy', 'Vortex', 'Dreams', 'Realm', 'Universe', 'Space', 'Void',
                'Vault', 'Wave', 'Port', 'Path', 'Forge', 'Protocol', 'Studio', 'Collective', 'Protocol', 'Labs', 'Craft', 'Works', 'Gems', 'Genesis',
                'Tech', 'Chain', 'Nexus', 'Digital', 'Sphere', 'Linea', 'Layer', 'Star', 'Solaris', 'Plasma', 'Stellar', 'Nebula', 'Horizon', 'Pulse', 'Orbit', 'Cosmos', 'Synchrony']

    names = ['Alpha', 'Omega', 'NFT', 'Genesis', 'Digital', 'Art', 'Mystic', 'Space', 'Cosmic', 'Galactic', 'Pixel', 'Quantum', 'Rainbow', 'Kryptonite', 'Cyber', 'Magic', 'Unicorn', 'Meta', 'Ether', 'Satoshi', 'Moon', 'HODL', 'FOMO', 'DeFi', 'Yield', 'NFTY',
            'Crystal', 'Dream', 'Future', 'Eon', 'Infinity', 'Fusion', 'Cosmos', 'Linea', 'Layer2', 'L2', 'Chain', 'Plasma', 'Stellar', 'Solaris', 'Horizon', 'Synchrony', 'Nova', 'Aurora', 'Aegis', 'Celestial', 'Nebula', 'Pulse', 'Orbit', 'Nexus']

    name = random.choice(prefixes) + ' ' + random.choice(names) + ' ' + random.choice(suffixes)
    return name

def generate_collection_symbol(name):
    symbol = name.replace(' ', '').upper()[:random.randint(3, 5)]
    return symbol

def generate_collection_description(name):
    descriptions = [name + ' Token', name + ' NFT', 'The ' + name + ' Collection', 'Explore the ' + name,
                    'Discover ' + name, name + ' Universe', name + ' Artwork', 'The Essence of ' + name,
                    name + ' Wonders', 'Journey through ' + name, name + ' Treasures', 'Unlock the power of ' + name,
                    'A world of ' + name, 'The magic of ' + name, 'Experience ' + name, 'Delve into ' + name,
                    name + ' Marvels', 'Adventures in ' + name, 'The Enchantment of ' + name, name + ' Dreams',
                    'Visions of ' + name, 'Echoes of ' + name, name + ' Fantasia', 'The Enigma of ' + name,
                    name + ' Chronicles', 'Whispers of ' + name, name + ' Odyssey', 'Tales from ' + name,
                    'The Legacy of ' + name, name + ' Legends', 'Myths of ' + name, name + ' Saga',
                    'In the realm of ' + name, 'A world beyond ' + name, name + ' Elegance', 'Infinite ' + name,
                    'The heart of ' + name, 'Celestial ' + name, 'Epic ' + name, name + ' Phenomenon',
                    'Legends of ' + name, name + ' Chronicle', 'Sculptures of ' + name, 'Symphony of ' + name,
                    'Rise of ' + name, 'Mysteries of ' + name, 'Whispers from ' + name, 'The Odyssey of ' + name,
                    'Realm of ' + name, 'Astral ' + name, 'Chronicles of ' + name, 'Sagas from ' + name,
                    'Tales of ' + name, 'Adventures of ' + name, 'Wonders of ' + name, 'Legends from ' + name,
                    'The Enchanted ' + name, 'Artistry of ' + name, name + ' Visions', 'Curiosities of ' + name,
                    'Symphonies from ' + name, 'The Myths of ' + name, 'Epic ' + name + ' Adventures',
                    'Whispers of ' + name + ' Tales', name + ' Fantasies', 'Odyssey through ' + name,
                    'Chronicles of ' + name + ' Lore', 'The Legacy ' + name + ' Holds',
                    'Myths and ' + name + ' Legends', name + ' Sagas of Wonder', 'Tales of ' + name + ' Chronicles',
                    'Adventures in ' + name + ' Realm', 'Exploring ' + name + ' Dreams',
                    'Unlocking ' + name + ' Mysteries', 'Discover the ' + name + ' Odyssey',
                    name + ' Chronicles of Destiny', 'Echoes from ' + name + ' Visions', name + ' Odyssey into Fantasy',
                    'The ' + name + ' Artistic Journey', 'Mystical ' + name + ' Quest',
                    'Wonders of ' + name + ' Realms', 'Enchanted ' + name + ' Tales', name + ' Dreams and Legends',
                    'Exploring the ' + name + ' Universe', 'Embark on a ' + name + ' Adventure',
                    name + ' Odyssey Beyond Imagination', 'Legends and Myths of ' + name,
                    'A ' + name + ' Fantasy Adventure', 'Chronicles of ' + name + ' Legends',
                    'The ' + name + ' Legacy Unveiled', 'Mythical ' + name + ' Odyssey', name + ' Journeys of Wonder',
                    'Uncover ' + name + ' Chronicles', 'Enter the World of ' + name,
                    'Tales from the ' + name + ' Realm', name + ' Chronicles of Imagination',
                    'The ' + name + ' Saga Begins', 'A ' + name + ' Fantasy Realm', 'Legendary ' + name + ' Odyssey',
                    'Mysteries of ' + name + ' Legends', 'Venture into ' + name + ' Realms',
                    'Adventures in ' + name + ' Lore', 'Discover ' + name + ' Visions',
                    name + ' Odyssey of Enchantment', 'Epic ' + name + ' Chronicles', 'Whispers of ' + name + ' Myths',
                    'Journey through ' + name + ' Fantasy', name + ' Chronicles of Magic',
                    'Unlocking ' + name + ' Wonders', 'Embark on a ' + name + ' Quest', name + ' Odyssey into Legends',
                    'Realm of ' + name + ' Fantasy', 'The ' + name + ' Enchanted Journey',
                    'Explore the ' + name + ' Chronicles', name + ' Odyssey Beyond Dreams',
                    'Legends and Myths of ' + name + ' Realm', 'A ' + name + ' Adventure Awaits',
                    'Chronicles of ' + name + ' Destiny', 'The ' + name + ' Legacy Revealed',
                    'Mythical ' + name + ' Adventures', name + ' Journeys into Fantasy',
                    'Unveiling ' + name + ' Chronicles', 'Discover ' + name + ' Realms',
                    'Tales from the ' + name + ' Odyssey', name + ' Chronicles of Wonder',
                    'The ' + name + ' Saga Continues', 'A ' + name + ' Fantasy Adventure Beckons',
                    'Legendary ' + name + ' Chronicles', 'Mysteries of ' + name + ' Visions',
                    'Venture into ' + name + ' Lore', 'Adventures in ' + name + ' Imagination',
                    name + ' Odyssey of Magic', 'Epic ' + name + ' Myths', 'Whispers of ' + name + ' Legends',
                    'Journey through ' + name + ' Enchantment']
    description = random.choice(descriptions)
    return description

#DAO
class Aragon():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'ARAGON'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])

    def get_headers(self, multipart=None):
        headers = {
            'authority': 'prod.ipfs.aragon.network',
            'accept': '*/*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://app.aragon.org',
            'referer': 'https://app.aragon.org/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'x-api-key': 'b477RhECf8s8sdM7XrkLBs2wHc4kCMwpbcFC55Kt',
        }
        if multipart:
            headers['content-type'] = multipart.content_type
        return headers

    def get_image_hash(self):
        for i in range(5):
            try:
                image_size = random.choice([i for i in range(500, 1001, 100)])
                image = self.helper.fetch_url(url=f'https://picsum.photos/{image_size}', type='get', content=True)
                if not image:
                    continue

                fields = { 'path': ('blob', image, 'application/octet-stream') }
                boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
                multipart = MultipartEncoder(fields=fields, boundary=boundary)
                url = 'https://prod.ipfs.aragon.network/api/v0/add'
                result = self.helper.fetch_url(url=url, type='post', data=multipart, headers=self.get_headers(multipart=multipart))
                ipfs_hash = result['Hash']
                return ipfs_hash, multipart, image, boundary
            except:
                time.sleep((i+1)*i)
        return None

    def process_dao_creation(self, account, private_key, new_w3):

        image_hash, multipart, image, boundary = self.get_image_hash()
        if not image_hash:
            return 'error'

        url = f'https://prod.ipfs.aragon.network/api/v0/pin/add?arg={image_hash}'
        result = self.helper.fetch_url(url=url, type='post', headers=self.get_headers())

        dao_name = f"{generate_name(min_length=3)} {random.choice(['DAO', 'Community', 'Token', 'Collective', 'Commune', 'dao' 'public', 'Public', 'society', 'Society', 'token'])}"

        payload = {"name":dao_name,"description":dao_name,"links": [],"avatar":f"ipfs://{image_hash}"}
        json_payload = json.dumps(payload)
        fields = {
            'path': ('', json_payload, 'application/json')  # 'blob' is the field name
        }
        multipart = MultipartEncoder(fields=fields, boundary=boundary)

        result = self.helper.fetch_url(url='https://prod.ipfs.aragon.network/api/v0/add', type='post', data=multipart, headers=self.get_headers(multipart=multipart))
        hash = result['Hash']

        url = f'https://prod.ipfs.aragon.network/api/v0/pin/add?arg={hash}'
        headers = self.get_headers()
        headers['path'] = f'/api/v0/pin/add?arg={hash}'
        result = self.helper.fetch_url(url=url, type='post', headers=headers)

        hex_hash = hash.encode("utf-8").hex()

        args = [
                [
                  "0x0000000000000000000000000000000000000000",
                  "",
                  "",
                  f"0x697066733a2f2f51{hex_hash[2:]}"
                ],
                [
                  [
                    [
                      [
                        1,
                        2
                      ],
                      "0xcDC4b0BC63AEfFf3a7826A19D101406C6322A585"
                    ],
                    f"0x0000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000{account.address.lower()[2:]}"
                  ]
                ]
              ]

        func_ = getattr(self.contract.functions, 'createDao')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно сделал DAO "{dao_name}"!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        return self.process_dao_creation(account, private_key, new_w3)

#FREE NFT
class Mintfun():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'MINTFUN'

    def get_collections(self, chain=8453):

        url = f'https://mint.fun/api/mintfun/feed/free?range=24h&chain={chain}'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                return result['collections']
            except:
                time.sleep(i*1)
        return []

    def get_data(self, collection, chain=8453):
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

    def main(self, private_key, attempt = 0):

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

        collections = self.get_collections()
        if not collections:
            return self.main(private_key=private_key, attempt=attempt+1)
        collection = random.choice(collections)

        _, contract = collection['contract'].split(':')
        tx_data = self.get_data(contract)
        if not tx_data:
            return self.main(private_key=private_key, attempt=attempt + 1)

        if int(tx_data['ethValue']) > 0:
            return self.main(private_key=private_key, attempt = attempt + 1)

        tx = make_tx(new_w3, account, data=tx_data['callData'], to=tx_data['to'], gas_multiplier=1, value=0)

        if tx in ["low_native", "change_nft"] or not tx:
            return self.main(private_key=private_key, attempt = attempt + 2)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key, attempt = attempt + 1)
        self.logger.log_success(f"{self.project} | Успешно заминтил NFT {collection['name']} за 0 ETH",account.address)
        return new_w3.to_hex(hash)

#FREE NFT + GAMING
class Landtorn():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'LANDTORN'
        self.contract_settler = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract_settler']), abi=other_data[self.project]['ABI_settler'])
        self.contract_satchel = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract_satchel']), abi=other_data[self.project]['ABI_satchel'])
        self.contract_dungeon = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract_dungeon']), abi=other_data[self.project]['ABI_dungeon'])

    def get_token_id(self, account):

        url = f'https://api.landtorn.com/api/v1/account/balance/{account.address}/1'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                return result
            except:
                time.sleep(i * 1)
        return []

    def get_account_data(self, token_id):

        url = f'https://api.landtorn.com/api/v1/account/infor/{token_id}'
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                return result
            except:
                time.sleep(i * 1)
        return []

    def post_create_char(self, token_id, hash):

        url = 'https://api.landtorn.com/api/v1/account'
        for i in range(5):
            try:
                account = self.contract_satchel.functions.account('0xaa6297e24fF79B1702a61e099218D260ba648dA0', 8453, '0xB311Ec23c4A7578a4c18F66774a5d7b51DD1DD07', token_id, 0).call()
                payload = {"implementation": "0xaa6297e24fF79B1702a61e099218D260ba648dA0","account": account, "chainId": 8453, "tokenContract": "0xB311Ec23c4A7578a4c18F66774a5d7b51DD1DD07", "tokenId": token_id, "salt": 0, "txHash": hash, "Asset": [], "AccountMythic": []}
                result = self.helper.fetch_url(url=url, type='post', payload=payload)
                return result
            except:
                time.sleep(i * 1)
        return []

    def get_char(self, account, private_key, new_w3, only_create=False):

        if not only_create:
            func_ = getattr(self.contract_settler.functions, 'safeMint')

            tx = make_tx(new_w3, account, value=0, func=func_, args=None, args_positioning=True)
            if tx == "low_native" or not tx:
                return tx

            sign = account.sign_transaction(tx)
            hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

            tx_status = check_for_status(new_w3, hash)
            if not tx_status:
                return self.main(private_key=private_key)

        func_ = getattr(self.contract_satchel.functions, 'createAccount')
        token_id = self.get_token_id(account)[-1]['tokenId']
        args = '0xaa6297e24fF79B1702a61e099218D260ba648dA0', 8453, '0xB311Ec23c4A7578a4c18F66774a5d7b51DD1DD07', int(token_id), 0, b''
        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)

        post_char = self.post_create_char(token_id, new_w3.to_hex(hash))
        if post_char:
            self.logger.log_success(f"{self.project} | Успешно сделал персонажа #{token_id}!", wallet=account.address)
            return True

    def main(self, private_key, attempt = 0):

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

        token = self.get_token_id(account)
        try:
            if token.get('message', 'none') == "wallet don't have any torn":
                return self.get_char(account, private_key, new_w3)
        except:
            pass

        account_data = self.get_account_data(token[-1]['tokenId'])

        func_ = getattr(self.contract_dungeon.functions, 'participate')
        try:
            type = 1 if int(account_data['balance']['shardPower']) < 15 else 2
        except:
            return self.get_char(account, private_key, new_w3)

        energy = random.choice([1, 2, 5])
        if int(account_data['energy']) < energy and int(account_data['energy']) != 0:
            energy = 1
        elif int(account_data['energy']) == 0:
            self.logger.log_success(f"{self.project} | Нет энергии для похода в данж :(",wallet=account.address)
            return True

        args = account_data['account'], type, energy
        value = self.contract_dungeon.functions.gasFee(energy).call()
        tx = make_tx(new_w3, account, value=value, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)

        self.logger.log_success(f"{self.project} | Успешно сходил в данж {'первого' if type == 1 else 'второго'} уровня и залутал предметов!", wallet=account.address)
        return True

#JUST DEGEN
class Friendtech():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'FRIENDTECH'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])

    def get_shares_trades(self):
        url = 'https://api.studio.thegraph.com/query/51062/enemytech/version/latest'
        for i in range(5):
            try:
                payload = {"query":'\n      query MyQuery { trades( first: 1000 orderBy: blockTimestamp orderDirection: desc where: {isBuy: false, subjectEthAmount: "3125000000000"} ) { id isBuy ethAmount blockTimestamp blockNumber shareAmount protocolEthAmount trader supply subjectEthAmount subject } }'}
                result = self.helper.fetch_url(url=url, type='post', payload=payload)
                return result['data']['trades']
            except:
                time.sleep(i * 1)
        return []

    def get_user_shares(self, account):
        for i in range(5):
            try:
                result = self.helper.fetch_url(url=f'https://friendmex.com/api/token/holdings?address={account.address}', type='get')
                return result
            except:
                time.sleep(i * 1)
        return []

    def get_user(self, address):
        url = f'https://frentech.octav.fi/api/users/user?address={address}'
        for i in range(2):
            try:
                result = self.helper.fetch_url(url=url, type='get')
                return result['twitterName'], result['twitterUsername'], result['followers']
            except:
                time.sleep(i * 1)
        return None

    def buy_share(self, account, private_key, address, new_w3, value=0):
        func_ = getattr(self.contract.functions, 'buyShares')

        tx = make_tx(new_w3, account, value=value, func=func_, args=(address, 1), args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        return True

    def sell_share(self, account, private_key, address, new_w3):

        for i in range(10):
            try:
                sell_price = self.contract.functions.getSellPriceAfterFee(address, 1).call()

                func_ = getattr(self.contract.functions, 'sellShares')
                tx = make_tx(new_w3, account, func=func_, args=(address, 1), args_positioning=True)
                if tx == "low_native" or not tx:
                    return tx

                sign = account.sign_transaction(tx)
                hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)

                tx_status = check_for_status(new_w3, hash)
                if not tx_status:
                    return self.main(private_key=private_key)
                return sell_price
            except:
                time.sleep(1)
        return False

    def main(self, private_key, attempt = 0):

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
            own_shares = self.contract.functions.getBuyPriceAfterFee(account.address, 1).call()
        except:
            return self.main(private_key=private_key, attempt=attempt)
        if own_shares == 0:
            buy_share = self.buy_share(account, private_key, account.address, new_w3)
            if not buy_share:
                return self.main(private_key=private_key, attempt=attempt+1)
            self.logger.log_success(f"{self.project} | Успешно купил свою акцию!", wallet=account.address)
            return True
        trades = self.get_shares_trades()
        if not trades:
            return self.main(private_key=private_key, attempt=attempt + 1)
        user_shares_ = self.get_user_shares(account)
        if not user_shares_:
            return self.main(private_key=private_key, attempt=attempt + 1)
        user_shares = [share for share in user_shares_ if share['address'].lower() != account.address.lower()]
        buy_action = True if len(user_shares) == 0 else random.choice([True, True, False])
        if buy_action:
            random.shuffle(trades)
            for trade in trades:
                try:
                    price = self.contract.functions.getBuyPriceAfterFee(new_w3.to_checksum_address(trade['subject']), 1).call()
                    if price == 68750000000000:
                        buy_share = self.buy_share(account, private_key, new_w3.to_checksum_address(trade['subject']), new_w3, price)
                        if not buy_share:
                            return self.main(private_key=private_key, attempt=attempt + 1)
                        user_data_ = self.get_user(trade['subject'])
                        user_data = "UNKNOWN" if not user_data_ else f"@{user_data_[1]} | {user_data_[2]} пдп"
                        self.logger.log_success(f"{self.project} | Успешно купил акцию ({user_data}) за 0.00006875 ETH!", wallet=account.address)
                        return True
                except:
                    pass
        else:
            share = random.choice(user_shares)
            sell_share = self.sell_share(account, private_key, new_w3.to_checksum_address(share['address']), new_w3)
            if not sell_share:
                return self.main(private_key=private_key, attempt=attempt + 1)
            user_data_ = self.get_user(share['address'])
            user_data = "UNKNOWN" if not user_data_ else f"@{user_data_[1]} | {user_data_[2]} пдп"
            self.logger.log_success(f"{self.project} | Успешно продал акцию ({user_data}) за {sell_share / (10 ** 18)} ETH!", wallet=account.address)
            return True

#0.00069 ETH NFT
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

    def get_collections(self, chain=8453):

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

    def main(self, private_key, attempt = 0):

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

        collections = self.get_collections()
        if not collections:
            return self.main(private_key=private_key, attempt=attempt+1)
        collection = random.choice(collections)

        contract = collection['writingNFT']['proxyAddress']
        col_contract = new_w3.eth.contract(address=new_w3.to_checksum_address(contract), abi=other_data[self.project]['ABI'])
        price = col_contract.functions.price().call()
        if price != 0:
            return self.main(private_key=private_key, attempt=attempt + 1)

        func_ = getattr(col_contract.functions, 'purchase')

        tx = make_tx(new_w3, account, value=int(0.00069 * 10 ** 18), func=func_, args=(account.address, ""), args_positioning=True)
        if tx == "low_native" or not tx:
            return self.main(private_key=private_key, attempt = attempt + 2)

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key, attempt = attempt + 1)

        self.logger.log_success(f"{self.project} | Успешно заминтил статью {collection['writingNFT']['title']} за 0.00069 ETH",account.address)
        return new_w3.to_hex(hash)

#FREE NFT
class Nfts2me():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'NFTS2ME'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])

    def process_collection_creation(self, account, private_key, new_w3):

        name = generate_collection_name()
        symbol = generate_collection_symbol(name)

        supply = random.randint(1, 10)

        args = name, symbol, [account.address for i in range(supply)], new_w3.eth.account.create().key.hex(), [], '0x0000000000000000000000000000000000000000', 750, False, new_w3.eth.account.create().key.hex(), '0x3732310000000000000000000000000000000000000000000000000000000000'

        func_ = getattr(self.contract.functions, 'createAndMintCollection')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)

        self.logger.log_success(f'{self.project} | Успешно сделал коллекцию "{name}" и заминтил {supply} NFT!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        return self.process_collection_creation(account, private_key, new_w3)

#FREE NFT
class Omnisea():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'OMNISEA'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])

    def get_headers(self, multipart=None):
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Origin': 'https://omnisea.org',
            'Referer': 'https://omnisea.org/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'authorization': 'Basic MjdwTVA4SEFtckp3TXVHemJGdXBlN0dPY0FBOmU0OTA0N2I2YmM4MmExZjYwY2VkMDUwY2I5MjVkNzYy',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        if multipart:
            headers['content-type'] = multipart.content_type
        return headers

    def generate_random_filename(self):
        random_uuid = uuid.uuid4()

        random_filename = str(random_uuid).replace("-", "")

        return random_filename

    def get_image_hash(self):
        for i in range(5):
            try:
                image_size = random.choice([i for i in range(500, 1001, 100)])
                image = self.helper.fetch_url(url=f'https://picsum.photos/{image_size}', type='get', content=True)
                if not image:
                    continue
                col_name = generate_collection_name()
                col_desc = generate_collection_description(col_name)
                fields = {
                    'file': ('', image, 'image/jpeg'),
                }

                boundary = '----WebKitFormBoundary' + ''.join(random.sample(string.ascii_letters + string.digits, 16))
                multipart = MultipartEncoder(fields=fields, boundary=boundary)
                return multipart, col_name, col_desc
            except:
                time.sleep((i+1)*i)
        return None

    def process_collection_creation(self, account, private_key, new_w3):

        multipart, name, desc = self.get_image_hash()

        url = f'https://ipfs.infura.io:5001/api/v0/add?stream-channels=true&progress=false'
        result = self.helper.fetch_url(url=url, type='post', headers=self.get_headers(multipart=multipart), data=multipart)
        hash = result['Hash']

        name = generate_collection_name()
        symbol = generate_collection_symbol(name)
        end_time = int(time.time() + random.randint(30*24*60*60, 30*24*60*60*12))
        royaly = int(random.randint(0, 10) * 100)
        supply = random.choice([int(random.randint(10, 1000) * random.randint(1, 10)), 6969, int(random.randint(1, 10) * 1000)])
        args = name, symbol, hash, '', supply, True, royaly, end_time

        func_ = getattr(self.contract.functions, 'create')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=False)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно создал коллекцию "{name}"!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        return self.process_collection_creation(account, private_key, new_w3)

#SMART TX
class Gnosis():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'GNOSIS SAFE'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])

    def process_safe_creation(self, account, private_key, new_w3):

        data = self.contract.encodeABI(fn_name="setup", args=[[account.address], 1, NULL_ADDRESS, "0x", new_w3.to_checksum_address("0x017062a1dE2FE6b99BE3d9d37841FeD19F573804"), NULL_ADDRESS, 0, NULL_ADDRESS])
        args = new_w3.to_checksum_address('0xfb1bffC9d739B8D520DaF37dF666da4C687191EA'), data, int(time.time()+600)

        func_ = getattr(self.contract.functions, 'createProxyWithNonce')

        tx = make_tx(new_w3, account, value=0, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        #tx_receipt = new_w3.eth.get_transaction_receipt(hash)
        #print(tx_receipt.logs[0]['address'])
        self.logger.log_success(f'{self.project} | Успешно создал Gnosis Safe!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        return self.process_safe_creation(account, private_key, new_w3)

#0.0026 ETH NFT
class Basepaint():
    def __init__(self, w3, logger, helper):
        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'BASEPAINT'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])

    def process_daily_mint(self, account, private_key, new_w3):

        current_art_id = self.contract.functions.today().call() - 1
        current_day_balance = self.contract.functions.balanceOf(account.address, current_art_id).call()
        if current_day_balance > 0:
            self.logger.log_success(f'{self.project} | Сегодняшняя NFT уже заминчена!',wallet=account.address)
            return
        current_art_price = self.contract.functions.openEditionPrice().call()

        args = current_art_id, 1

        func_ = getattr(self.contract.functions, 'mint')

        tx = make_tx(new_w3, account, value=current_art_price, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно заминтил NFT №{current_art_id} за {current_art_price / (10**18)} ETH!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):

        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        return self.process_daily_mint(account, private_key, new_w3)

# CHEAP TX + L0
class L2telegraph():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'L2TELEGRAPH'
        self.contract_nft = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract_nft']), abi=other_data[self.project]['ABI_nft'])
        self.contract_message = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract_message']), abi=other_data[self.project]['ABI_message'])
        self.chains = {'MANTLE': 181,'ZKEVM': 158,'LINEA': 183,'ZORA': 195,'OPBNB': 202}

    def process_mint_and_bridge(self, account, private_key, new_w3):
        selected_chain = random.choice(list(self.chains.items()))

        func_ = getattr(self.contract_nft.functions, 'mint')

        tx = make_tx(new_w3, account, value=new_w3.to_wei(0.0005, "ether"), func=func_, args=None)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно заминтил NFT для бриджа за 0.0005 ETH!', wallet=account.address)

        receipts = new_w3.eth.get_transaction_receipt(hash)
        nft_id = int(receipts["logs"][0]["topics"][-1].hex(), 0)
        fee = int(self.contract_nft.functions.estimateFees(selected_chain[1], account.address, '0x', False, '0x').call()[0] * 1.5)
        func_ = getattr(self.contract_nft.functions, 'crossChain')
        args = selected_chain[1], '0x64e0f6164ac110b67df9a4848707ffbcb86c87a936a358b3ba1fb368e35b71ea40c7f4ab89bfd8e1', nft_id
        tx = make_tx(new_w3, account, value=fee, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно забриджил NFT в сеть {selected_chain[0]}!', wallet=account.address)
        return new_w3.to_hex(hash)

    def process_message(self, account, private_key, new_w3):
        selected_chain = random.choice(list(self.chains.items()))
        fee = int(self.contract_message.functions.estimateFees(selected_chain[1], account.address, '0x', False, '0x').call()[0] * 1.2)
        func_ = getattr(self.contract_message.functions, 'sendMessage')
        message = random.choice([generate_collection_name(), generate_name(10)])
        args = message, selected_chain[1], "0xdc60fd9d2a4ccf97f292969580874de69e6c326e64e0f6164ac110b67df9a4848707ffbcb86c87a9"
        tx = make_tx(new_w3, account, value=int(int(new_w3.to_wei(0.00025, "ether")) + fee), func=func_, args=args)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно отправил письмо в сеть {selected_chain[0]}!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):
        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        action = random.choice([self.process_mint_and_bridge, self.process_message])
        return action(account, private_key, new_w3)

# CHEAP TX + L0
class Zerius():

    def __init__(self, w3, logger, helper):

        self.w3 = w3
        self.logger = logger
        self.helper = helper
        self.project = 'ZERIUS'
        self.contract = self.w3.eth.contract(address=self.w3.to_checksum_address(other_data[self.project]['contract']), abi=other_data[self.project]['ABI'])
        self.chains = {"ZORA": 195,"ARB": 110,"OPT": 111,"POLY": 109,"BSC": 102,"AVAX": 106,}

    def process_mint_and_bridge(self, account, private_key, new_w3):
        selected_chain = random.choice(list(self.chains.items()))

        mint_fee = self.contract.functions.mintFee().call()
        func_ = getattr(self.contract.functions, 'mint')

        tx = make_tx(new_w3, account, value=mint_fee, func=func_, args=None)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно заминтил NFT для бриджа за {mint_fee / (10**18)} ETH!', wallet=account.address)

        receipts = new_w3.eth.get_transaction_receipt(hash)
        nft_id = int(receipts["logs"][0]["topics"][-1].hex(), 0)
        fee = int(self.contract.functions.estimateSendFee(selected_chain[1], account.address, nft_id, False, '0x').call()[0] * 1.2)
        func_ = getattr(self.contract.functions, 'sendFrom')
        args = account.address, selected_chain[1], account.address, nft_id, NULL_ADDRESS, NULL_ADDRESS, '0x0001000000000000000000000000000000000000000000000000000000000003d090'
        tx = make_tx(new_w3, account, value=fee, func=func_, args=args, args_positioning=True)
        if tx == "low_native" or not tx:
            return tx

        sign = account.sign_transaction(tx)
        hash = new_w3.eth.send_raw_transaction(sign.rawTransaction)
        tx_status = check_for_status(new_w3, hash)
        if not tx_status:
            return self.main(private_key=private_key)
        self.logger.log_success(f'{self.project} | Успешно забриджил NFT в сеть {selected_chain[0]}!', wallet=account.address)
        return new_w3.to_hex(hash)

    def main(self, private_key):
        try:
            if private_key.get('proxy', None):
                new_w3 = self.helper.get_web3(private_key['proxy'], self.w3)
            else:
                raise Exception
        except Exception:
            new_w3 = self.w3

        account = new_w3.eth.account.from_key(private_key['private_key'])

        return self.process_mint_and_bridge(account, private_key, new_w3)

def initialize_misc(classes_to_init, w3, logger, helper):
    available_swaps = {
        "Landtorn": Landtorn,
        "Mintfun": Mintfun,
        "Aragon": Aragon,
        "Friendtech": Friendtech,
        "Mirror": Mirror,
        "Omnisea": Omnisea,
        "Nfts2me": Nfts2me,
        "Basepaint": Basepaint,
        "Gnosis": Gnosis,
        "L2telegraph": L2telegraph,
        "Zerius": Zerius,
    }

    initialized_objects = {}

    for class_name, should_init in classes_to_init.items():
        if should_init:
            initialized_objects[class_name] = available_swaps[class_name](w3, logger, helper)

    return initialized_objects
