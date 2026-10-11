import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo.operations import SearchIndexModel  # noqa: E402

from app import config  # noqa: E402
from app.db import get_db, using_atlas  # noqa: E402

DIMENSIONS = 1024


def main():
    if not using_atlas():
        print("MONGODB_URI is not set; nothing to do.")
        return
    db = get_db()
    existing = [i["name"] for i in db.feedback.list_search_indexes()]
    if "feedback_vec" in existing:
        print("feedback_vec already exists")
        return
    model = SearchIndexModel(
        name="feedback_vec",
        type="vectorSearch",
        definition={"fields": [
            {"type": "vector", "path": "embedding", "numDimensions": DIMENSIONS, "similarity": "cosine"},
            {"type": "filter", "path": "customer_id"},
        ]},
    )
    db.feedback.create_search_index(model=model)
    print(f"created feedback_vec on {config.mongodb_db()}.feedback ({DIMENSIONS} dims)")


if __name__ == "__main__":
    main()
