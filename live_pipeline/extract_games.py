from urllib.request import urlopen
import pandas as pd
from bs4 import BeautifulSoup


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


def parse_game_bs(html) -> list[str]:
    """function to find application's tags"""

    soup = BeautifulSoup(html, "html.parser")
    tags = soup.find_all("a", class_="app_tag")
    game_tags = []
    for each in tags:
        game_tags.append(each.string.strip())

    return game_tags


def parse_price_bs(html):
    """function to find application price"""

    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("div", class_="game_purchase_price price")
    return tag.string.strip()


if __name__ == "__main__":

    website = get_html(
        "https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&supportedlang=english&ndl=1")
    all_recent_games = parse_app_id_bs(website)
    # print(all_recent_games)

    for game in all_recent_games:
        game_webpage = get_html(
            f"https://store.steampowered.com/app/{game['app_id']}")
        tags_for_game = parse_game_bs(game_webpage)
        game["tags"] = tags_for_game
        price_of_game = parse_price_bs(game_webpage)
        game["price"] = price_of_game
        print(game)
        break
