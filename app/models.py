from pydantic import BaseModel
from enum import Enum


class InfoModel(BaseModel):
    show_name: str
    total_episodes: int
    total_fillers: int
    last_episode_aired_at: int
    last_updated_at: int
    url: str


class GroupModel(BaseModel):
    manga_canon: list[int]
    mixed_canon: list[int]
    filler: list[int]
    anime_canon: list[int]


class EpisodeType(str, Enum):
    MANGA_CANON = "Manga Canon"
    MIXED_CANON = "Mixed Canon/Filler"
    FILLER = "Filler"
    ANIME_CANON = "Anime Canon"


class EpisodeModel(BaseModel):
    number: int
    title: str
    type: EpisodeType
    aired_at: int
    url: str


class ShowResponseModel(BaseModel):
    info: InfoModel
    groups: GroupModel
    episodes: list[EpisodeModel]


class ShowModel(BaseModel):
    name: str
    title: str
    url: str
