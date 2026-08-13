import json

from app.config import SPOTS_CONFIG_PATH
from app.scoring import SpotConfig


def load_spots() -> list[SpotConfig]:
    data = json.loads(SPOTS_CONFIG_PATH.read_text())
    return [SpotConfig.from_dict(d) for d in data["spots"]]


def load_spot(spot_id: str) -> SpotConfig | None:
    for spot in load_spots():
        if spot.id == spot_id:
            return spot
    return None
