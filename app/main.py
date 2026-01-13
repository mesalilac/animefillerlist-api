import time

from app.models import ShowResponseCacheModel, ShowsListResponseCacheModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from app.scrape import get_shows_list, get_show_by_slug

app = FastAPI()

show_cache: dict[str, ShowResponseCacheModel] = {}
shows_list_cache: ShowsListResponseCacheModel | None = None

SHOW_CACHE_TTL = 43200  # 12 hours
SHOWS_LIST_CACHE_TTL = 259200  # 3 days


@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/docs")


@app.get("/shows/{slug}")
async def get_show(slug: str):
    current_time = int(time.time())

    cached_item = show_cache.get(slug)

    if cached_item and current_time - cached_item.last_updated_at < SHOW_CACHE_TTL:
        return cached_item.data

    new_data = get_show_by_slug(slug)

    if new_data is None:
        raise HTTPException(status_code=404, detail="Show not found!")

    show_cache[slug] = ShowResponseCacheModel(
        data=new_data, last_updated_at=current_time
    )

    return new_data


@app.get("/shows")
async def get_shows():
    global shows_list_cache
    current_time = int(time.time())

    if (
        shows_list_cache is not None
        and current_time - shows_list_cache.last_updated_at < SHOWS_LIST_CACHE_TTL
    ):
        return shows_list_cache.data

    new_data = get_shows_list()

    shows_list_cache = ShowsListResponseCacheModel(
        data=new_data, last_updated_at=current_time
    )

    return new_data
