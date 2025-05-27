import requests
from urllib.parse import quote
from config import RIOT_API_KEY

def get_account_by_riot_id(name, tag):
    encoded_name = quote(name.strip())
    encoded_tag = quote(tag.strip().replace("#", ""))
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    print(f"[Account Lookup] URL: {url}")
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def get_summoner_icon(puuid, server):
    url = f"https://{server}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    print(f"[Icon Lookup] URL: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("profileIconId")
    return None