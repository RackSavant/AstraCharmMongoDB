from typing import Optional

from app import config
from app.design_spec import DEFAULT_RULES

_db = None


def using_atlas() -> bool:
    return bool(config.mongodb_uri())


def get_db():
    global _db
    if _db is None:
        if using_atlas():
            from pymongo import MongoClient

            _db = MongoClient(config.mongodb_uri())[config.mongodb_db()]
        else:
            import mongomock

            _db = mongomock.MongoClient()[config.mongodb_db()]
        seed_constraints(_db)
        seed_components(_db)
    return _db


def seed_constraints(db=None, version: int = 1) -> None:
    db = db if db is not None else get_db()
    if db.constraints.count_documents({}) == 0:
        db.constraints.insert_many([{**r, "version": version} for r in DEFAULT_RULES])


COMPONENTS = [
    {"id": "metal_silver", "kind": "metal", "name": "silver", "price_per_g": 1.0},
    {"id": "metal_gold", "kind": "metal", "name": "gold", "price_per_g": 65.0},
    {"id": "metal_platinum", "kind": "metal", "name": "platinum", "price_per_g": 35.0},
    {"id": "stone_round", "kind": "stone", "name": "round", "price_per_mm": 2.0},
    {"id": "stone_oval", "kind": "stone", "name": "oval", "price_per_mm": 2.5},
]


def seed_components(db=None) -> None:
    db = db if db is not None else get_db()
    if db.components.count_documents({}) == 0:
        db.components.insert_many([dict(c) for c in COMPONENTS])


def reset_db(clear_constraints: bool = False) -> None:
    db = get_db()
    for name in ("customers", "products", "designs", "design_sessions", "feedback", "memories",
                 "agent_events", "manufacturing_jobs", "evaluations"):
        db[name].delete_many({})
    if clear_constraints:
        db.constraints.delete_many({})
        seed_constraints(db)


def reset_connection(db: Optional[object] = None) -> None:
    global _db
    _db = db
