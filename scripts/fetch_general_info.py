import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")

def fetch_general_info():
    url = f"https://min-api.cryptocompare.com/data/coin/generalinfo?fsyms=BTC,ETH,BNB,SOL,XRP,DOGE,ADA,AVAX,DOT,TRX,SUI&tsym=USD&api_key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json().get("Data", [])
        
        if not data:
            raise ValueError("No general info data returned from API")
        
        general_info = []
        btc_price_usd = None 
        
        for item in data:
            coin_info = item.get("CoinInfo", {})
            conversion_info = item.get("ConversionInfo", {})
            
            coin_name = coin_info.get("Name", "unknown coin")
            
            
            raw_data = conversion_info.get("RAW", [])
            if not raw_data:
                raise ValueError(f"No RAW data for {coin_name}")
            
            raw_split = raw_data[0].split("~")
            if len(raw_split) < 6:
                raise ValueError(f"Invalid RAW data format for {coin_name}: {raw_data[0]}")
            
            try:
                price = float(raw_split[5])  
                if price <= 0:
                    raise ValueError(f"Invalid price (non-positive) for {coin_name}: {price}")
            except ValueError as e:
                raise ValueError(f"Failed to parse price for {coin_name}: {raw_split[5]}") from e
            
            
            price_currency = raw_split[3]  
            if coin_name == "BTC":
                btc_price_usd = price
                price_usd = price
            elif price_currency == "BTC":
                if btc_price_usd is None:
                    raise ValueError(f"BTC price not available to convert {coin_name} price")
                price_usd = price * btc_price_usd  
            else:
                price_usd = price
            
           
            supply = conversion_info.get("Supply", 0)
            if supply <= 0:
                raise ValueError(f"Invalid supply (non-positive) for {coin_name}: {supply}")
            
            
            market_cap = supply * price_usd
            
         
            proof_type = coin_info.get("ProofType", "N/A")
            
            general_info.append({
                "coin": coin_name,
                "full_name": coin_info.get("FullName", ""),
                "launch_date": coin_info.get("AssetLaunchDate", ""),
                "algorithm": coin_info.get("Algorithm", "N/A"),
                "proof_type": proof_type,  
                "price_usd": round(price_usd, 2),
                "market_cap_usd": market_cap  
            })
        
        return pd.DataFrame(general_info)
    
    except Exception as e:
        raise Exception(f"Failed to fetch general info: {str(e)}")