def fetch_sentiment(coin_id, symbol, *, api_key, session):
    url = f"https://min-api.cryptocompare.com/data/social/coin/latest?coinId={coin_id}&api_key={api_key}"
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "Data" not in data or not data["Data"]:
            print(f"Error: No social data found for {symbol.upper()} (ID: {coin_id})")
            return None

        formatted_data = {
            "Data": [data["Data"]]
        }
        return formatted_data

    except requests.exceptions.Timeout:
        print(f"Error: Request to CryptoCompare timed out for {symbol.upper()} (ID: {coin_id}) after 30 seconds.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sentiment for {symbol.upper()} (ID: {coin_id}): HTTP Status: {e.response.status_code if e.response else 'N/A'}")
        print(f"Error details: {str(e)}")
        return None
    except Exception as e:
        print(f"Error fetching sentiment for {symbol.upper()} (ID: {coin_id}): {str(e)}")
        return None