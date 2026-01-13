"""Scrape data from `animefillerlist.com`"""

import requests

from datetime import datetime, timezone
from typing import TypeGuard
from app.models import ShowModel, ShowResponseModel, EpisodeModel, InfoModel, GroupModel
from bs4 import BeautifulSoup, element

BASE_URL = "https://animefillerlist.com"
SHOWS_BASE_URL = BASE_URL + "/" + "shows"


def is_tag(ele: element.Tag | element.NavigableString | None) -> TypeGuard[element.Tag]:
    return isinstance(ele, element.Tag)


def expand_ranges(range_strings: list[str]) -> list[int]:
    expanded_list: list[int] = []

    for r in range_strings:
        parts = r.split("-")

        if len(parts) == 2:
            start, end = map(int, parts)

            expanded_list.extend(range(start, end + 1))
        elif len(parts) == 1:
            expanded_list.append(int(parts[0]))

    return expanded_list


def get_show_by_slug(slug: str) -> ShowResponseModel | None:
    """None means 404 error"""

    # InfoModel
    # GroupModel
    # EpisodeModel
    # ShowResponseModel

    manga_canon_episodes_list: list[int] = []
    mixed_canon_filler_episodes_list: list[int] = []
    filler_episodes_list: list[int] = []
    anime_canon_episodes_list: list[int] = []

    episodes_list: list[EpisodeModel] = []

    url = SHOWS_BASE_URL + "/" + slug

    res: requests.Response = requests.get(url)

    if res.status_code != 200:
        return None

    html = res.content

    soup = BeautifulSoup(html, "html.parser")
    condensed_div = soup.find("div", {"id": "Condensed"})

    if not is_tag(condensed_div):
        return None

    manga_canon_div = condensed_div.find("div", {"class": "manga_canon"})

    if is_tag(manga_canon_div):
        manga_canon_episodes_list = expand_ranges(
            [a.get_text() for a in manga_canon_div.find_all("a")]
        )

    mixed_canon_filler_div = condensed_div.find("div", {"class": "mixed_canon/filler"})

    if is_tag(mixed_canon_filler_div):
        mixed_canon_filler_episodes_list = expand_ranges(
            [a.get_text() for a in mixed_canon_filler_div.find_all("a")]
        )

    filler_div = condensed_div.find("div", {"class": "filler"})

    if is_tag(filler_div):
        filler_episodes_list = expand_ranges(
            [a.get_text() for a in filler_div.find_all("a")]
        )

    anime_canon_div = condensed_div.find("div", {"class": "anime_canon"})

    if is_tag(anime_canon_div):
        anime_canon_episodes_list = expand_ranges(
            [a.get_text() for a in anime_canon_div.find_all("a")]
        )

    episodes_list_table = soup.find("table", {"class": "EpisodeList"})

    if is_tag(episodes_list_table):
        table_body = episodes_list_table.find("tbody")
        if is_tag(table_body):
            for tr in table_body.find_all("tr"):
                ep_number = int(tr.find("td", {"class": "Number"}).get_text())
                title_a = tr.find("td", {"class": "Title"}).find("a")
                title = title_a.get_text()
                ep_url = BASE_URL + title_a["href"]

                ep_type = tr.find("td", {"class": "Type"}).find("span").get_text()
                ep_date = tr.find("td", {"class": "Date"}).get_text()

                dt = datetime.strptime(ep_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                timestamp = int(dt.timestamp())

                episode = EpisodeModel(
                    number=ep_number,
                    title=title,
                    type=ep_type,
                    aired_at=timestamp,
                    url=ep_url,
                )

                episodes_list.append(episode)

    last_updated_at_div = soup.find("div", {"class": "Date"})
    last_updated_at = 0
    last_updated_at_formatted = ""

    if is_tag(last_updated_at_div):
        last_updated_at_formatted = str(last_updated_at_div.contents[1]).strip()

        dt = datetime.strptime(last_updated_at_formatted, "%B %d, %Y").replace(
            tzinfo=timezone.utc
        )

        last_updated_at = int(dt.timestamp())

    info_model = InfoModel(
        show_name=slug,
        total_episodes=len(episodes_list) - 1,
        total_fillers=len(filler_episodes_list),
        last_episode_aired_at=episodes_list[-1].aired_at,
        last_updated_at=last_updated_at,
        url=url,
    )

    group_model = GroupModel(
        manga_canon=manga_canon_episodes_list,
        mixed_canon=mixed_canon_filler_episodes_list,
        filler=filler_episodes_list,
        anime_canon=anime_canon_episodes_list,
    )

    show_response_model = ShowResponseModel(
        info=info_model, groups=group_model, episodes=episodes_list
    )

    return show_response_model


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
