"""Scrape data from `animefillerlist.com`"""

import httpx
from urllib.parse import urljoin

from datetime import datetime, timezone
from typing import TypeGuard
from app.models import ShowModel, ShowResponseModel, EpisodeModel, InfoModel, GroupModel
from bs4 import BeautifulSoup, element

BASE_URL = "https://animefillerlist.com"
SHOWS_BASE_URL = urljoin(BASE_URL, "shows/")

MAL_ANIME_BASE_URL = "https://myanimelist.net/anime/"


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


async def get_show_by_slug(
    client: httpx.AsyncClient,
    slug: str,
    slug_to_mal_mapping: dict[str, int] | None = None,
) -> ShowResponseModel | None:
    manga_canon_episodes_list: list[int] = []
    mixed_canon_filler_episodes_list: list[int] = []
    filler_episodes_list: list[int] = []
    anime_canon_episodes_list: list[int] = []

    episodes_list: list[EpisodeModel] = []

    url = urljoin(SHOWS_BASE_URL, slug)

    try:
        res = await client.get(url, follow_redirects=True)
        if res.status_code != 200:
            return None
    except httpx.RequestError:
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
                ep_url = urljoin(BASE_URL, title_a["href"])

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

    main_div = soup.select_one("div.Right:nth-of-type(2)")
    title: str = slug

    if is_tag(main_div):
        h1_tag = main_div.find("h1")

        if is_tag(h1_tag):
            title = h1_tag.get_text().rstrip("Filler List")

    mal_id: int | None = None
    mal_url: str | None = None

    if slug_to_mal_mapping is not None:
        mal_id = slug_to_mal_mapping.get(slug)
        if mal_id:
            mal_url = urljoin(MAL_ANIME_BASE_URL, str(mal_id))

    info_model = InfoModel(
        title=title,
        slug=slug,
        mal_id=mal_id,
        mal_url=mal_url,
        total_episodes=len(episodes_list),
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


async def get_shows_list(
    client: httpx.AsyncClient, slug_to_mal_mapping: dict[str, int] | None = None
) -> list[ShowModel]:
    results: list[ShowModel] = []

    try:
        res = await client.get(SHOWS_BASE_URL, follow_redirects=True)
        if res.status_code != 200:
            return results
    except httpx.RequestError:
        return results

    html = res.content

    soup = BeautifulSoup(html, "html.parser")

    show_list_div = soup.find("div", {"id": "ShowList"})

    links_list = show_list_div.find_all("a")

    for link in links_list:
        url = link["href"]
        title = link.get_text()
        slug = url.split("/")[-1]

        mal_id: int | None = None
        mal_url: str | None = None

        if slug_to_mal_mapping is not None:
            mal_id = slug_to_mal_mapping.get(slug)
            if mal_id:
                mal_url = urljoin(MAL_ANIME_BASE_URL, str(mal_id))

        results.append(
            ShowModel(
                title=title,
                slug=slug,
                mal_id=mal_id,
                mal_url=mal_url,
                url=urljoin(BASE_URL, url),
            )
        )

    return results
