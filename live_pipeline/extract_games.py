"""Script to get information from Steam website and API"""
from bs4 import BeautifulSoup
import pandas as pd
import requests
from urllib.request import urlopen


RELEASE_WEBSITE = "https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&supportedlang=english&ndl=1"


def get_html(url):
    """function to open the url and get the information"""
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf_8")
    return html


def parse_app_id_bs(html) -> list[dict]:
    """function to find the app id from the url"""
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.find_all(
        "a", class_="search_result_row ds_collapse_flag")

    all_games = []
    for game in tags:
        application = {}
        application["app_id"] = game.attrs['data-ds-appid']
        application["title"] = game.find('span', class_='title').text
        application["release_date"] = game.find(
            'div', class_="col search_released responsive_secondrow").text
        all_games.append(application)

    return all_games


def parse_game_bs(soup) -> list[str]:
    """function to find application's tags"""
    tags = soup.find_all("a", class_="app_tag")
    game_tags = []
    for each in tags:
        game_tags.append(each.string.strip())

    return game_tags


def parse_price_bs(soup) -> dict:
    """function to find application price"""
    prices = {}
    try:
        tag = soup.find("div", class_="game_purchase_price price")
        prices["full price"] = tag.string.strip()
        prices["sale price"] = tag.string.strip()
    except:
        full_tag = soup.find("div", class_="discount_original_price")
        prices["full price"] = full_tag.string.strip()
        discount_tag = soup.find("div", class_="discount_final_price")
        prices["sale price"] = discount_tag.string.strip()

    return prices


def system_requirements(data) -> dict:
    """function to find compatible systems"""
    response = data['platforms']
    return response


def get_genre_from_steam(data) -> list:
    """function to find steam generate genre"""
    genres = []
    response = data['genres']
    for genre in response:
        genres.append(genre['description'])
    return genres


def get_developer_name(data) -> list:
    """function to get developer names"""
    developers = []
    response = data['developers']
    for developer in response:
        developers.append(developer)

    return developers


def get_publisher_name(data) -> list:
    """function to get publisher names"""
    publishers = []
    response = data['publishers']
    for publisher in response:
        publishers.append(publisher)
    return publishers


def update_game_information(game_id: int):
    """update game dictionary with information from API"""

    game_webpage = get_html(
        f"https://store.steampowered.com/app/{game_id}")
    soup = BeautifulSoup(game_webpage, "html.parser")
    tags_for_game = parse_game_bs(soup)
    game["user_tags"] = tags_for_game
    price_of_game = parse_price_bs(soup)
    game.update(price_of_game)

    request = requests.get(
        f"""https://store.steampowered.com/api/appdetails?appids={game_id}""")

    response = request.json()[game_id]['data']
    compatible_systems = system_requirements(response)
    game.update(compatible_systems)
    steam_genres = get_genre_from_steam(response)
    game['genres'] = steam_genres
    developer = get_developer_name(response)
    game['developers'] = developer
    publisher = get_publisher_name(response)
    game['publishers'] = publisher


if __name__ == "__main__":

    website = get_html(RELEASE_WEBSITE)
    all_recent_games = parse_app_id_bs(website)

    for game in all_recent_games:
        update_game_information(game["app_id"])

    data_frame = pd.DataFrame(all_recent_games)
    data_frame.to_csv('test.csv')
