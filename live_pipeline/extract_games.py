"""Script to get information from Steam website and API"""
import csv

from bs4 import BeautifulSoup
import pandas as pd
import requests
from urllib.request import urlopen


RELEASE_WEBSITE = "https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&supportedlang=english&ndl=1"


def get_html(url: str) -> str:
    """Open the url and get the information."""
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf_8")

    return html


def parse_app_id_bs(html) -> list[dict]:
    """Find the app id, title and release date from the url."""
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
    """Find the user tags for each game."""
    tags = soup.find_all("a", class_="app_tag")
    game_tags = []
    for each in tags:
        game_tags.append(each.string.strip())

    return game_tags


def parse_price_bs(soup) -> dict:
    """Find the cost of the application price."""
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
    """Find the platforms that the game is compatible with."""
    response = data['platforms']
    return response


def get_genre_from_steam(data) -> list:
    """Find the genres associated with the game"""
    genres = []
    response = data['genres']
    for genre in response:
        genres.append(genre['description'])
    return genres


def get_developer_name(data) -> list:
    """Find the game developer"""
    developers = []
    response = data['developers']
    for developer in response:
        developers.append(developer)

    return developers


def get_publisher_name(data) -> list:
    """Find publisher name"""
    publishers = []
    response = data['publishers']
    for publisher in response:
        publishers.append(publisher)
    return publishers


def update_game_information(all_recent_games: list):
    """Update game dictionary with information from the API"""
    for game in all_recent_games:
        game_webpage = get_html(
            f"""https://store.steampowered.com/app/{game["app_id"]}""")
        soup = BeautifulSoup(game_webpage, "html.parser")
        tags_for_game = parse_game_bs(soup)
        game["user_tags"] = tags_for_game
        price_of_game = parse_price_bs(soup)
        game.update(price_of_game)

        request = requests.get(
            f"""https://store.steampowered.com/api/appdetails?appids={game["app_id"]}""")

        response = request.json()[game["app_id"]]['data']
        compatible_systems = system_requirements(response)
        game.update(compatible_systems)
        steam_genres = get_genre_from_steam(response)
        game['genres'] = steam_genres
        developer = get_developer_name(response)
        game['developers'] = developer
        publisher = get_publisher_name(response)
        game['publishers'] = publisher

    return all_recent_games


def convert_to_csv(files: list[dict]) -> None:
    """Convert file to CSV"""
    keys = files[0].keys()
    with open('games.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(files)


if __name__ == "__main__":

    website = get_html(RELEASE_WEBSITE)
    all_recent_games = parse_app_id_bs(website)

    updated_games = update_game_information(all_recent_games)
    convert_to_csv(updated_games)
