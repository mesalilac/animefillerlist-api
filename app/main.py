from typing import Union

from fastapi import FastAPI

from app.scrape import get_shows_list, get_show_by_slug

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/shows/{slug}")
def get_show(slug: str):
    return get_show_by_slug(slug)


@app.get("/shows")
def get_shows():
    return get_shows_list()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
