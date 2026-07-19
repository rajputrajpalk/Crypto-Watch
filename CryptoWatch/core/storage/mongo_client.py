from __future__ import annotations

from dataclasses import dataclass
from pymongo import MongoClient

from CryptoWatch import settings


@dataclass
class MongoHandle:
    client: MongoClient
    db: any


_mh: MongoHandle | None = None


def get_mongo() -> MongoHandle:
    global _mh
    if _mh is None:
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        _mh = MongoHandle(client=client, db=db)
    return _mh

