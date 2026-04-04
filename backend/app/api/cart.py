"""Cart API — Redis-backed shopping cart with personalization tracking."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import get_tracker
from app.personalization.tracker import PersonalizationTracker

router = APIRouter(prefix="/api/cart", tags=["cart"])

TrackerDep = Annotated[PersonalizationTracker, Depends(get_tracker)]


def _cart_key(user_id: str) -> str:
    return f"cart:{user_id}"


def _names_key(user_id: str) -> str:
    return f"cart_names:{user_id}"


def _favorites_key(user_id: str) -> str:
    return f"favorites:{user_id}"


@router.get("")
async def get_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
):
    """Return cart as list of {product_id, product_name, quantity}."""
    redis = tracker.redis
    key = _cart_key(user_id)
    nkey = _names_key(user_id)

    raw = await redis.hgetall(key)
    names = await redis.hgetall(nkey)

    items = []
    for k, v in raw.items():
        pid = k.decode() if isinstance(k, bytes) else k
        qty = int(v)
        name_raw = names.get(k, b"")
        name = name_raw.decode() if isinstance(name_raw, bytes) else name_raw
        items.append({"product_id": pid, "product_name": name or pid, "quantity": qty})

    return {"user_id": user_id, "items": items}


@router.post("/add")
async def add_to_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
    product_id: Annotated[str, Query()] = "",
    product_name: Annotated[str, Query()] = "",
    category: Annotated[str, Query()] = "",
    quantity: Annotated[int, Query(ge=1)] = 1,
):
    """Add item to cart. Stores name for display."""
    if not product_id:
        return {"ok": False, "error": "product_id is required"}

    redis = tracker.redis
    key = _cart_key(user_id)
    nkey = _names_key(user_id)

    await redis.hincrby(key, product_id, quantity)
    if product_name:
        await redis.hset(nkey, product_id, product_name)

    if user_id != "anonymous":
        await tracker.track_event(
            user_id=user_id,
            event_type="cart",
            product_id=product_id,
            category=category,
        )

    raw_qty = await redis.hget(key, product_id)
    new_quantity = int(raw_qty) if raw_qty is not None else quantity
    return {"ok": True, "product_id": product_id, "quantity": new_quantity}


@router.post("/remove")
async def remove_from_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
    product_id: Annotated[str, Query()] = "",
    quantity: Annotated[int, Query(ge=1)] = 1,
):
    """Remove item from cart. Deletes if quantity reaches 0."""
    if not product_id:
        return {"ok": False, "error": "product_id is required"}

    redis = tracker.redis
    key = _cart_key(user_id)
    nkey = _names_key(user_id)
    raw_qty = await redis.hget(key, product_id)
    if raw_qty is None:
        return {"ok": False, "error": "product not in cart"}

    new_qty = int(raw_qty) - quantity
    if new_qty <= 0:
        await redis.hdel(key, product_id)
        await redis.hdel(nkey, product_id)
        return {"ok": True, "product_id": product_id, "quantity": 0}

    await redis.hset(key, product_id, new_qty)
    return {"ok": True, "product_id": product_id, "quantity": new_qty}


@router.post("/clear")
async def clear_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
):
    """Delete the entire cart."""
    redis = tracker.redis
    await redis.delete(_cart_key(user_id))
    await redis.delete(_names_key(user_id))
    return {"ok": True, "user_id": user_id}


# ---------------------------------------------------------------------------
# Favorites endpoints
# ---------------------------------------------------------------------------

@router.get("/favorites")
async def get_favorites(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
):
    """Return favorites as list of {product_id, product_name}."""
    redis = tracker.redis
    key = _favorites_key(user_id)
    raw = await redis.hgetall(key)
    items = []
    for k, v in raw.items():
        pid = k.decode() if isinstance(k, bytes) else k
        name = v.decode() if isinstance(v, bytes) else v
        items.append({"product_id": pid, "product_name": name or pid})
    return {"user_id": user_id, "items": items}


@router.post("/favorites/add")
async def add_favorite(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
    product_id: Annotated[str, Query()] = "",
    product_name: Annotated[str, Query()] = "",
    category: Annotated[str, Query()] = "",
):
    """Add product to favorites."""
    if not product_id:
        return {"ok": False, "error": "product_id is required"}

    redis = tracker.redis
    key = _favorites_key(user_id)
    await redis.hset(key, product_id, product_name or product_id)

    if user_id != "anonymous":
        await tracker.track_event(
            user_id=user_id,
            event_type="click",
            product_id=product_id,
            category=category,
        )

    return {"ok": True, "product_id": product_id}


@router.post("/favorites/remove")
async def remove_favorite(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
    product_id: Annotated[str, Query()] = "",
):
    """Remove product from favorites."""
    if not product_id:
        return {"ok": False, "error": "product_id is required"}

    redis = tracker.redis
    await redis.hdel(_favorites_key(user_id), product_id)
    return {"ok": True, "product_id": product_id}


@router.post("/favorites/clear")
async def clear_favorites(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
):
    """Clear all favorites."""
    redis = tracker.redis
    await redis.delete(_favorites_key(user_id))
    return {"ok": True, "user_id": user_id}
