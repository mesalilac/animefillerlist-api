"""Scrape data from `animefillerlist.com`"""

import requests

from .models import ShowModel
from bs4 import BeautifulSoup

BASE_URL = "https://animefillerlist.com"
SHOWS_BASE_URL = BASE_URL + "/" + "shows"


def get_shows_list() -> list[ShowModel]:
    results: list[ShowModel] = []

    res: requests.Response = requests.get(SHOWS_BASE_URL)

    if res.status_code != 200:
        return results

    html = res.content

    soup = BeautifulSoup(html, "html.parser")

    show_list_div = soup.find("div", {"id": "ShowList"})

    links_list = show_list_div.find_all("a")

    for link in links_list:
        url = link["href"]
        title = link.get_text()
        name = url.split("/")[-1]

        results.append(ShowModel(name=name, title=title, url=BASE_URL + url))

    return results


# if __name__ == "__main__":
# for x in get_shows_list():
#     print(x.name)
