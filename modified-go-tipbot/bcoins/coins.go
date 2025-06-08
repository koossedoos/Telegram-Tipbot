// Copyright (c) 2019 Romano (Viacoin developer)
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
package bcoins

import (
	"fmt"
	"github.com/viacoin/viad/chaincfg"
	"github.com/viacoin/viad/wire"
)

type Coin struct {
	Symbol     string
	Name       string
	Network    *Network
	Insight    *Insight
	FeePerByte int64
	Binance    bool
}

type Insight struct {
	Explorer string
	Api      string
}

type Network struct {
	Name     string
	Symbol   string
	xpubkey  byte
	xprivkey byte
	magic    wire.BitcoinNet
}

var coins = map[string]Coin{
	"aegs": {Name: "aegisum", Symbol: "aegs", Network: &Network{"aegisum", "aegs", 0x17, 0x97, 0xabc6680f},
		Insight: &Insight{"https://explorer.aegisum.com", "https://explorer.aegisum.com/api"}, FeePerByte: 100, Binance: false,
	},
	"advc": {Name: "adventurecoin", Symbol: "advc", Network: &Network{"adventurecoin", "advc", 0x17, 0x97, 0xadc6680f},
		Insight: &Insight{"https://explorer.advc.com", "https://explorer.advc.com/api"}, FeePerByte: 100, Binance: false,
	},
	"shic": {Name: "shibacoin", Symbol: "shic", Network: &Network{"shibacoin", "shic", 0x3f, 0xbf, 0xabc6681f},
		Insight: &Insight{"https://explorer.shibacoin.com", "https://explorer.shibacoin.com/api"}, FeePerByte: 100, Binance: false,
	},
	"pepe": {Name: "pepecoin", Symbol: "pepe", Network: &Network{"pepecoin", "pepe", 0x37, 0xb7, 0xabc6682f},
		Insight: &Insight{"https://explorer.pepecoin.com", "https://explorer.pepecoin.com/api"}, FeePerByte: 100, Binance: false,
	},
}

// returns all coins in a Coin struct slice
func GetAllCoins() []Coin {
	var coinList []Coin

	for _, coin := range coins {
		coinList = append(coinList, coin)
	}
	return coinList
}

// select a coin by symbol and return Coin struct and error
func SelectCoin(symbol string) (Coin, error) {
	if coins, ok := coins[symbol]; ok {
		return coins, nil
	}
	return Coin{}, fmt.Errorf("altcoin %s not found\n", symbol)
}

func (network Network) GetNetworkParams() *chaincfg.Params {
	networkParams := &chaincfg.MainNetParams
	networkParams.Name = network.Name
	networkParams.Net = network.magic
	networkParams.PubKeyHashAddrID = network.xpubkey
	networkParams.PrivateKeyID = network.xprivkey
	return networkParams
}
