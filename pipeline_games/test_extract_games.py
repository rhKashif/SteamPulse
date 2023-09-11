"""Script for testing extract_games functions"""
import os
from bs4 import BeautifulSoup

from extract_games import get_html, parse_app_id_bs, parse_game_bs, parse_price_bs, system_requirements, get_genre_from_steam, get_developer_name, get_publisher_name, convert_to_csv


def test_html_returns_a_string():
    """Ensure that string is returned for a generic website"""
    result = get_html("https://www.google.co.uk")

    assert isinstance(result, str) is True


def test_application_details_returned(fake_html):
    """Check whether app id, title and release date returned"""
    result = parse_app_id_bs(fake_html)
    assert result == [{'app_id': '12345', 'release_date': '5 Sep, 2023',
                       'title': 'SteamPulse: FAKE GAME'}]


def test_parse_game_bs(fake_html_soup):
    """Check a list of appropriate tags returned"""
    fake_soup = BeautifulSoup(fake_html_soup, "html.parser")
    result = parse_game_bs(fake_soup)

    assert result == ['Fake_Tag 1', 'Fake_Tag 2', 'Fake_Tag 3']
    assert isinstance(result, list) is True


def test_parse_game_bs_no_tags(html_no_tags):
    """Check empty list returned if no tags found"""
    fake_soup = BeautifulSoup(html_no_tags, "html.parser")
    result = parse_game_bs(fake_soup)

    assert result == []


def test_parse_price_bs(fake_html_soup):
    """Check same price returned if no discount"""
    fake_soup = BeautifulSoup(fake_html_soup, "html.parser")
    result = parse_price_bs(fake_soup)

    assert result == {'full price': '£1.69', 'sale price': '£1.69'}


def test_parse_price_for_discount(html_no_tags):
    """Check discounted price returned on discounted games"""
    fake_soup = BeautifulSoup(html_no_tags, "html.parser")
    result = parse_price_bs(fake_soup)

    assert result == {'full price': '£2.50', 'sale price': '£1.69'}


def test_system_requirements(fake_response):
    """Check system requirements are returned appropriately"""
    result = system_requirements(fake_response)

    assert result == {'linux': False, 'mac': False, 'windows': True}
    assert isinstance(result, dict) is True


def test_genres_returned(fake_response):
    """Check genres returned as a list"""
    result = get_genre_from_steam(fake_response)

    assert isinstance(result, list) is True
    assert result == ['Action', 'Adventure', 'Simulation', 'Strategy']


def test_developer_names(fake_response):
    """Check developer returned"""
    result = get_developer_name(fake_response)

    assert isinstance(result, list) is True
    assert result == ['Fake Developer 1', 'Fake Developer 2']


def test_publisher_name(fake_response):
    """Check publisher name returned"""
    result = get_publisher_name(fake_response)

    assert isinstance(result, list) is True
    assert result == ['Fake Publisher']


def test_csv_created():
    """Check CSV file is created"""
    assert os.path.exists('test.csv') is False
    convert_to_csv([{'fake_data': 3}, {'fake_data': 2}], 'test.csv')
    assert os.path.exists('test.csv') is True
    os.remove('test.csv')
