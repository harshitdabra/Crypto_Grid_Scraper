import requests
import pandas as pd

def fetch_prices():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'bitcoin,ethereum,binancecoin,cardano,ripple,solana,dogecoin,polkadot,shiba-inu,tron,aptos,near-protocol,hbar',
        'vs_currencies': 'usd'
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    name_mapping = {
        'bitcoin': 'Bitcoin',
        'ethereum': 'Ethereum',
        'binancecoin': 'Binance Coin',
        'cardano': 'Cardano',
        'ripple': 'Ripple',
        'solana': 'Solana',
        'dogecoin': 'Dogecoin',
        'polkadot': 'Polkadot',
        'shiba-inu': 'Shiba Inu',
        'tron': 'Tron',
        'aptos': 'Aptos',
        'near-protocol': 'NEAR Protocol',
        'hbar': 'Hedera'
    }

    df = pd.DataFrame(data).T
    df.reset_index(inplace=True)
    df.columns = ['coin', 'price_usd']
    df['coin'] = df['coin'].map(name_mapping)

    df = df.sort_values(by='price_usd', ascending=False).reset_index(drop=True)

    return df
