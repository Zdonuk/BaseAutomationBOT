# BaseAutomationBOT
Multi-functional bot for automating activities on the Base network. Performs swaps, liquidity provision, NFT operations, domain services, lending protocols and much more to simulate natural user activity.

# 🤖 BASE CHAIN AUTOMATION BOT

Multi-functional bot for automating activities on the Base network. Performs swaps, liquidity provision, NFT operations, domain services, lending protocols and much more to simulate natural user activity.

---



### 🔄 DeFi Protocols

**DEX Swaps (17 protocols):**
- Aerodrome, Baseswap, Alienbase, Swapbased
- Odos, Maverick, 1inch, Openocean
- Pancake, Kyberswap, Sushiswap, Dodoex
- Wowmax, Equalizer, Firebird, Spaceswap
- Woofi, Uniswap

**Liquidity (5 protocols):**
- Aerodrome, Baseswap, Alienbase
- Swapbased

**Lending (4 protocols):**
- Granary, Moonwell, Sonnie, Aave

### 🌉 Bridges (8 protocols)

Automatic ETH bridging to BASE from other networks:
- Main Bridge (official Base bridge)
- Orbiter, Symbiosis, XY Finance
- Socket, Layerswap, Lifi, OmniBTC

### 🎨 NFT Marketplaces (3 protocols)

- Element
- Opensea
- Alienswap

### 🌐 Domain Services (4 protocols)

- Openname
- Basens
- Basename
- BNS

### 🎯 Other Modules (10 protocols)

- Landtorn - NFT minting
- Mintfun - NFT platform
- Aragon - DAO
- Mirror - blog platform
- Omnisea - NFT
- Nfts2me - NFT creation
- Gnosis - multisig wallets
- Basepaint - generative art
- L2telegraph - on-chain messaging
- Zerius - protocol

### 🔥 Warmup

Executes transactions on ETH, ARB, OPT networks to warm up wallets before and after working on BASE.

---

## 🚀 QUICK START

### 1. Requirements

```bash
Python 3.8+
pip install -r req
```

### 2. Configuration

**File `wallets.txt`:**
```
0xYourPrivateKey1
0xYourPrivateKey2;login:password@proxy_ip:port
0xYourPrivateKey3
```

**File `settings.py`:**
```python
settings_dict = {
    "max_gwei": 50,              # Max gas in Gwei
    "tx_min": 10,                # Minimum transactions
    "tx_max": 15,                # Maximum transactions
    "min_eth_balance": 0.05,     # Min ETH balance in BASE
    "min_sleep": 20,             # Min pause between actions (sec)
    "max_sleep": 60,             # Max pause between actions (sec)
    # ... other settings
}
```

### 3. Run

```bash
python3 main.py
```

---

## ⚙️ MAIN SETTINGS

### General Parameters

| Parameter | Description | Recommended Value |
|----------|----------|------------------------|
| `max_gwei` | Maximum gas for operations | 50-100 |
| `tx_min` / `tx_max` | Range of transaction count | 10-15 |
| `min_sleep` / `max_sleep` | Pause between actions (sec) | 20-60 |
| `min_eth_balance` | Minimum ETH balance in BASE | 0.05 |
| `max_batch_wallets` | Max wallets simultaneously | 10 |
| `shuffle_wallets` | Shuffle wallets order | True |

### Swaps

| Parameter | Description | Value |
|----------|----------|----------|
| `max_slippage` | Maximum slippage (%) | 3 |
| `max_swap_value` | Max swap amount ($) | 100 |
| `swap_out_after` | Swap everything to ETH at the end | True |

### Bridges

| Parameter | Description | Value |
|----------|----------|----------|
| `to_base_min` / `to_base_max` | Bridge amount range to BASE | 0.05-0.10 ETH |
| `max_bridge_slippage` | Max bridge slippage (%) | 5 |
| `main_prioritet` | Main Bridge priority | True |
| `black_chains` | Ignore networks | ['ANY_CHAIN'] |

### NFT

| Parameter | Description | Value |
|----------|----------|----------|
| `max_nft_price` | Max NFT price for purchase (ETH) | 0.0005 |
| `list_nfts` | List purchased NFTs | True |

### Domains

| Parameter | Description | Value |
|----------|----------|----------|
| `multiple_domains` | Mint if domain already exists | False |
| `domain_reg_time` | Registration years | 1 |
| `domain_dop_action` | Additional domain actions | True |

### Liquidity

| Parameter | Description | Value |
|----------|----------|----------|
| `max_liq_in_usd` | Max liquidity to add ($) | 15 |
| `remove_liq_after` | Remove liquidity at the end | True |

### Lending

| Parameter | Description | Value |
|----------|----------|----------|
| `lendings_max_value` | Max lending amount ($) | 50 |
| `remove_lendings_afrer` | Remove from lending at the end | True |

### Warmup

| Parameter | Description | Value |
|----------|----------|----------|
| `warmup` | Enable warmup | True |
| `min_warmup_tx` / `max_warmup_tx` | Warmup transaction range | 1-2 |
| `warmup_before_dep` | Warmup before deposit to BASE | True |
| `warmup_before_withdraw` | Warmup before withdrawal | True |

---

## 🔧 RPC SETTINGS

```python
w3_dict = {
    "ETH": "https://rpc.ankr.com/eth/",
    "BASE": "https://rpc.ankr.com/base/",
    "ARB": "https://rpc.ankr.com/arbitrum/",
    "OPT": "https://rpc.ankr.com/optimism/"
}
```

**Recommendation:** Use your own RPC for better speed and reliability.

---

## 📊 WORKFLOW

### 1. Initialization
- Check RPC connections
- Load wallets from `wallets.txt`
- Generate unique route for each wallet

### 2. Route Generation
For each wallet, actions are randomly selected:
- **SWAP** - token exchange (weight: 10, decay: 0.7)
- **LIQUIDITY** - add liquidity (weight: 5, decay: 0.35)
- **NFT MARKET** - buy NFT (weight: 3, decay: 0.1)
- **NAMESERVICE** - register domain (weight: 1, decay: 0)
- **LENDING** - lending protocols (weight: 6, decay: 0.4)
- **OTHER** - other protocols (weight: 3, decay: 0.1)

**BRIDGE IN** is added automatically if balance < `min_eth_balance`.

### 3. Execution
- Gas check before each action
- Random pauses between actions
- Automatic error handling with retries
- Logging of all operations

### 4. Completion
After all actions are completed automatically:
- Swap all tokens back to ETH (if `swap_out_after: True`)
- Remove liquidity (if `remove_liq_after: True`)
- Withdraw from lending (if `remove_lendings_afrer: True`)

---

## 📁 PROJECT STRUCTURE

```
base-bot/
├── main.py                 # Main file
├── settings.py             # Settings
├── wallets.txt             # Private keys
├── helpers/
│   ├── utils.py           # Web3 utilities
│   ├── data.py            # Token data
│   ├── logger.py          # Logging
│   └── help.py            # Helpers
├── modules/
│   ├── swaps.py           # DEX swaps
│   ├── liquidity.py       # Liquidity
│   ├── lendings.py        # Lending
│   ├── bridges.py         # Bridges
│   ├── nft_markets.py     # NFT markets
│   ├── name_services.py   # Domains
│   ├── other.py           # Other
│   └── warmup.py          # Warmup
└── logs/                  # Logs (auto-created)
```

## 📈 OPTIMIZATION TIPS

### For maximum efficiency:

1. **Gas:** Work during low gas periods (night UTC)
2. **Proxies:** Use quality residential proxies
3. **RPC:** Own RPC endpoints are faster than public
4. **Pauses:** Increase `min_sleep`/`max_sleep` for naturalness
5. **Amounts:** Vary transaction amounts
6. **Wallets:** No more than 10-20 wallets simultaneously

### For saving costs:

1. Decrease `max_swap_value`
2. Decrease `max_liq_in_usd`
3. Decrease `lendings_max_value`
4. Decrease `max_nft_price`
5. Decrease `tx_max`

---

**IMPORTANT:**

- Use at your own risk
- No profit guarantee
- May result in loss of funds
- Author is not responsible
- Test on testnet
- Review code before use

---

### Requirements:
```bash
pip install web3>=6.0.0
pip install requests>=2.28.0
pip install colorama>=0.4.6
pip install pyotp>=2.8.0
pip install tls-client>=0.2.0
```
