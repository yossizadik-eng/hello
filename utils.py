import requests

def get_all_yugioh_cards():
    """
    Fetches all Yu-Gi-Oh! cards from the YGOPRODECK API 
    and stores them in a Python list.
    """
    url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"
    params = {
        "cardset": "Legend of Blue Eyes White Dragon"
    }
    
    print("Fetching Yu-Gi-Oh! card database... (This might take a few seconds)")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Check for HTTP errors
        
        # The API returns a JSON object where the 'data' key holds the list of cards
        data = response.json()
        card_list = data['data']
        
        print(success_msg := f"Successfully loaded {len(card_list)} cards into the collection!")
        return card_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
