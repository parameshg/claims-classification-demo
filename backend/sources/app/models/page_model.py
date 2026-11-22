from pydantic import BaseModel

from app.models.item_model import ItemModel


class PageModel(BaseModel):
    items: list[ItemModel]
    total: int
