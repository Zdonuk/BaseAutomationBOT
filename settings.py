                                        # /// НАСТРОЙКИ ///

settings_dict = {                       #   /////ОБЩИЕ/////
    "max_gwei": 99,                                                  # МАКСИМУМ ГАЗ В ЭФИРЕ ПРИ РАБОТЕ
    "attempts" : 5,                                                  # МАКСИМУМ ПОПЫТОК ПРИ ОШИБКЕ
    "tx_min" : 10,                                                   # МИНИМУМ ДЕЙСТВИЙ
    "tx_max": 15,                                                    # МАКСИМУМ ДЕЙСТВИЙ
    "min_sleep": 20,                                                 # МИНИМУМ СОН МЕЖДУ ДЕЙСТВИЯМИ
    "max_sleep": 60,                                                 # МАКСИМУМ СОН МЕЖДУ ДЕЙСТВИЯМИ
    "max_start_delay": 10,                                           # МАКСИМАЛЬНАЯ ЗАДЕРЖКУ ПЕРЕД СТАРТОМ КОШЕЛЬКА В ПАЧКЕ
    "min_after_gas_delay": 0,                                        # МИНИМАЛЬНАЯ ЗАДЕРЖКА ПОСЛЕ ВЫХОДА ИЗ ЦИКЛА ПРОВЕРКИ ГАЗА (ЧТОБЫ КОШЕЛЬКИ НЕ НАЧИНАЛИ В ОДНУ МИНУТУ)
    "max_after_gas_delay": 100,                                      # МАКСИМАЛЬНАЯ ЗАДЕРЖКА ПОСЛЕ ВЫХОДА ИЗ ЦИКЛА ПРОВЕРКИ ГАЗА (ЧТОБЫ КОШЕЛЬКИ НЕ НАЧИНАЛИ В ОДНУ МИНУТУ)
    "max_batch_wallets": 10,                                         # МАКСИМУМ КОШЕЛЬКОВ ЗА ПАЧКУ (20 МАКСИМУМ)
    "shuffle_wallets": True,                                         # МЕШАТЬ ЛИ КОШЕЛЬКИ
    "min_eth_balance": 0.05,                                         # МИНИМАЛЬНЫЙ БАЛАНС ЭФИРА В BASE (МЕНЬШЕ - БУДЕТ БРИДЖИТЬ)
    "show_warnings": True,                                           # ВЫВОДИТЬ ЛИ WARNING ЛОГИ
    "requests_proxy": None,                                          # ПРОКСИ ДЛЯ ЗАПРОСОВ (ИНАЧЕ НЕ БУДУТ РАБОТАТЬ KYBERSWAP, ELEMENT, OPENSEA, OPENOCEAN И Т.П)
                                                                     # ЛИБО ВКЛЮЧАЕМ VPN | ФОРМАТ - log:pass@ip:port
                                        #  /////МОСТ/////
    "to_base_min": 0.05,                                             # МИНИМУМ БРИДЖ В BASE
    "to_base_max": 0.10,                                             # МАКСИМУМ БРИДЖ В BASE
    "min_after_bridge_delay": 0,                                     # МИНИМАЛЬНАЯ ЗАДЕРЖКА ПОСЛЕ БРИДЖА
    "max_after_bridge_delay": 100,                                   # МАКСИМАЛЬНАЯ ЗАДЕРЖКА ПОСЛЕ БРИДЖА
    "black_chains": ['ANY_CHAIN_HERE'],                              # ЧЕЙНЫ С КОТОРЫМИ НЕ РАБОТАЕМ
    "max_bridge_slippage": 5,                                        # МАКСИМАЛЬНЫЙ СПИЛЕДЖ БРИДЖА (SYMBIOSIS, XY, PORTAL)
    "main_prioritet": True,                                          # ПРИОРИТЕТ НА МЕЙН БРИДЖ (ЕСЛИ ЕСТЬ ЭФИР В ОСНОВНОЙ СЕТИ)
                                        #  /////СВАПЫ/////
    "max_slippage": 3,                                               # МАКСИМАЛЬНЫЙ СЛИПЕДЖ СВАПОВ
    "max_swap_value": 100,                                           # МАКСИМАЛЬНОЕ ВЕЛЬЮ СВАПА В $
    "swap_out_after": True,                                          # СВАПНУТЬ ОБРАТНО ВСЕ ТОКЕНЫ В ETH В КОНЦЕ КРУГА
                                        #   /////НФТ/////
    "max_nft_price": 0.0005,                                         # МАКСИМУМ ЦЕНА НФТ НА МАРКЕТАХ ДЛЯ ПОКУПКИ (В ETH)
    "list_nfts": True,                                               # ЛИСТИТЬ ЛИ НФТ
                                        #  /////ДОМЕНЫ//////
    "multiple_domains": False,                                       # МИНТИТЬ ЛИ ДОМЕН ЕСЛИ УЖЕ ЕСТЬ 1 (РАБОТАЕТ НА ВСЕХ КРОМЕ ZNS.ID)
    "domain_reg_time": 1,                                            # КОЛ-ВО ЛЕТ ДЛЯ МИНТА ДОМЕНА (ЛУЧШЕ НЕ МЕНЯТЬ - ЦЕНА БУДЕТ ДОРОЖЕ)
    "domain_dop_action": True,                                       # ДОП ДЕЙСТВИЕ НА ДОМЕНАХ
                                        #/////ЛИКВИДНОСТЬ/////
    "max_liq_in_usd": 15,                                            # МАКСИМУМ ДОБАВЛЯЕМ В ЛИКВУ В $ (ОДНОГО ТОКЕНА)
    "remove_liq_after": True,                                        # ВЫВОДИТЬ ЛИ ИЗ ВСЕХ ПУЛОВ В КОНЦЕ КРУГА
                                        #  /////ЛЕНДИНГИ/////
    "lendings_max_value": 50,                                        # МАКСИМАЛЬНО ИСПОЛЬЗУЕМОЕ ВЕЛЬЮ ДЛЯ ЛЕНДИНГОВ (В $)
    "remove_lendings_afrer": True,                                   # УБИРАТЬ ЛИ ИЗ ЛЕНДИНГОВ В КОНЦЕ КРУГА

    "deriv_max_value": 10,                                           # МАКСИМАЛЬНО ИСПОЛЬЗУЕМОЕ ВЕЛЬЮ ДЛЯ ДЕРИВАТИВОВ (В $)
    "close_deriv_positions": True,                                   # ЗАКРЫВАТЬ ЛИ ИЗ ПОЗИЦИИ В КОНЦЕ КРУГА

                                        # ///// ETH ПРОГРЕВ /////
    "warmup": True,                                                  # ДЕЛАТЬ ЛИ ПРОГРЕВ ТРАНЗЫ В ДРУГИХ ЧЕЙНАХ
    "min_warmup_tx": 1,                                              # МИН ТРАНЗ ПРОГРЕВА
    "max_warmup_tx": 2,                                              # МАКС ТРАНЗ ПРОГРЕВА
    "warmup_before_dep": True,                                       # ДЕЛАТЬ ТРАНЗЫ ДО ДЕПА В BASE
    "warmup_before_withdraw": True,                                  # ДЕЛАТЬ ТРАНЗЫ ДО ВЫВОДА НА ОКЕКС
                                  
}
                                        # ///// RPC НАСТРОЙКИ /////
w3_dict = {
    "ETH": "https://rpc.ankr.com/eth/",
    "BASE": "https://rpc.ankr.com/base/",
    "ARB": "https://rpc.ankr.com/arbitrum/",
    "OPT": "https://rpc.ankr.com/optimism/"
}
                                        # ///// МОДУЛИ СВАПОВ /////
swaps_dict = {
    "Aerodrome": True,                                                       #  AERODROME   | aerodrome.finance
    "Baseswap": True,                                                        #  BASESWAP    | baseswap.fi
    "Alienbase": True,                                                       #  ALIENBASE   | alienswap.xyz
    "Swapbased": True,                                                       #  SWAPBASED   | swapbased.finance
    "Synthswap": True,                                                       #  SYNTHSWAP   | synthswap.io
    "Odos": True,                                                            #  ODOS        | odos.xyz
    "Maverick": True,                                                        #  MAVERICK    | app.mav.xyz
    "Inch": True,                                                            #  1INCH       | app.1inch.io
    "Openocean": True,                                                       #  OPENOCEAN   | openocean.finance
    "Okx": True,                                                             #  OKX         | okx.com/web3/dex
    "Pancake": True,                                                         #  PANCAKE     | pancakeswap.finance
    "Kyberswap": True,                                                       #  KYBERSWAP   | kyberswap.com
    "Sushiswap": True,                                                       #  SUSHISWAP   | sushi.com
    "Dodoex": True,                                                          #  DODOEX      | dodoex.io
    "Wowmax": True,                                                          #  WOWMAX      | wowmax.exchange
    "Equalizer": True,                                                       #  EQUALIZER   | equalizer.exchange
    "Firebird": True,                                                        #  FIREBIRD    | firebird.finance
    "Spaceswap": True,                                                       #  SPACESWAP   | spaceswap.tech
    "Woofi": True,                                                           #  WOOFI       | fi.woo.org
    "Uniswap": True,                                                         #  UNISWAP     | app.uniswap.org
}
                                        # ///// МОДУЛИ ЛИКВИДНОСТИ /////
liqs_dict = {
    "Aerodrome_liq": True,                                                   #  AERODROME   | aerodrome.finance
    "Baseswap_liq": True,                                                    #  BASESWAP    | baseswap.fi
    "Alienbase_liq": True,                                                   #  ALIENBASE   | alienswap.xyz
    "Swapbased_liq": True,                                                   #  SWAPBASED   | swapbased.finance
    "Synthswap_liq": True,                                                   #  SYNTHSWAP   | synthswap.io
    "Equalizer_liq": True,                                                   #  EQUALIZER   | equalizer.exchange
}
                                        # ///// МОДУЛИ ЛЕНДИНГОВ /////
lendings_dict = {
    "Granary": True,                                                         #  GRANARY     | granary.finance
    "Moonwell": True,                                                        #  MOONWELL    | moonwell.fi
    "Sonnie": True,                                                          #  SONNIE      | sonne.finance
    "Aave": True,                                                            #  AAVE        | aave.com
    "Seamless": True,                                                        #  SEAMLESS    | seamlessprotocol.com
}
                                        # ///// МОДУЛИ НФТ МАРКЕТОВ /////
nft_markets_dict = {
    "Element": True,                                                         #  ELEMENT     | element.market
    "Opensea": True,                                                         #  OPENSEA     | opensea.io
    'Alienswap': True,                                                       #  ALIENSWAP   | alienswap.xyz
    'Zonic': True,                                                           #  ZONIC       | zonic.app
    "Kreatorland": True,                                                     #  KREATORLAND | kreatorland.com
}
                                        # ///// МОДУЛИ ДЕРИВАТИВОВ /////
derivs_dict = {
    "Onchain": True,                                                         #  ONCHAIN     | onchain.trade
    "Unidex": True,                                                          #  UNIDEX      | unidex.exchange
}

                                        # ///// МОДУЛИ ДОМЕННЫХ СЕРВИСОВ /////
name_services_dict = {
    "Openname" : True,                                                       #  OPENNAME    | app.open.name
    "Basens": True,                                                          #  BASENS     | basens.domains
    'Basename': True,                                                        #  BASENAME   | base.name
    'Bns': True,                                                             #  BNS        | basename.domains
}
                                        # ///// МОДУЛИ МОСТОВ /////
bridges_dict = {
    "Main" : True,                                                           #  MAIN        | bridge.base.org
    "Orbiter" : True,                                                        #  ORBITER     | orbiter.finance
    "Symbiosis": True,                                                       #  SYMBIOSIS   | app.symbiosis.finance
    "Xyfinance": True,                                                       #  XYFINANCE   | app.xy.finance
    "Socket": True,                                                          #  SOCKET      | socket.tech
    "Layerswap": True,                                                       #  LAYERSWAP   | layerswap.io
    "Lifi": True,                                                            #  LIFI        | li.fi
    "Omnibtc": True,                                                         #  OMNIBTC     | app.omnibtc.finance
}
                                        # ///// МОДУЛИ РАЗНЫЕ /////
misc_dict = {
    "Landtorn": True,                                                        #  LANDTORN    | landtorn.com
    "Mintfun": True,                                                         #  MINTFUN     | mint.fun
    "Aragon": True,                                                          #  ARAGON      | app.aragon.org
    "Friendtech": True,                                                      #  FRIENDTECH  | friend.tech
    "Mirror": True,                                                          #  MIRROR      | mirror.xyz
    "Omnisea": True,                                                         #  OMNISEA     | omnisea.org
    "Nfts2me": True,                                                         #  NFTS2ME     | nfts2me.com
    "Gnosis": True,                                                          #  GNOSIS      | safe.global
    "Basepaint": True,                                                       #  BASEPAINT   | basepaint.xyz
    "L2telegraph": True,                                                     #  L2TELEGRAPH | l2telegraph.xyz
    "Zerius": True,                                                          #  ZERIUS      | zerius.io
}