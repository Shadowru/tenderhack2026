"""Cart API — Redis-backed shopping cart with personalization tracking."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import get_tracker
from app.personalization.tracker import PersonalizationTracker

router = APIRouter(prefix="/api/cart", tags=["cart"])

TrackerDep = Annotated[PersonalizationTracker, Depends(get_tracker)]


def _cart_key(user_id: str) -> str:
    return f"cart:{user_id}"


@router.get("")
async def get_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
):
    """Return current cart contents as {product_id: quantity} mapping."""
    key = _cart_key(user_id)
    raw = await tracker.redis.hgetall(key)
    cart = {
        (k.decode() if isinstance(k, bytes) else k): int(v)
        for k, v in raw.items()
    }
    return {"user_id": user_id, "items": cart}


@router.post("/add")
async def add_to_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
    product_id: Annotated[str, Query()] = "",
    quantity: Annotated[int, Query(ge=1)] = 1,
    category: Annotated[str, Query()] = "",
):
    """Add `quantity` units of `product_id` to the cart.

    Also records a 'cart' event for personalization so the recommendation
    engine learns from add-to-cart signals.
    """
    if not product_id:
        return {"ok": False, "error": "product_id is required"}

    key = _cart_key(user_id)
    await tracker.redis.hincrby(key, product_id, quantity)

    # Track cart event for personalization (non-anonymous users only)
    if user_id != "anonymous":
        await tracker.track_event(
            user_id=user_id,
            event_type="cart",
            product_id=product_id,
            category=category,
        )

    raw_qty = await tracker.redis.hget(key, product_id)
    new_quantity = int(raw_qty) if raw_qty is not None else quantity
    return {"ok": True, "product_id": product_id, "quantity": new_quantity}


@router.post("/remove")
async def remove_from_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
    product_id: Annotated[str, Query()] = "",
    quantity: Annotated[int, Query(ge=1)] = 1,
):
    """Remove `quantity` units of `product_id` from the cart.

    If the resulting quantity is <= 0, the item is deleted entirely.
    """
    if not product_id:
        return {"ok": False, "error": "product_id is required"}

    key = _cart_key(user_id)
    raw_qty = await tracker.redis.hget(key, product_id)
    if raw_qty is None:
        return {"ok": False, "error": "product not in cart"}

    current = int(raw_qty)
    new_qty = current - quantity
    if new_qty <= 0:
        await tracker.redis.hdel(key, product_id)
        return {"ok": True, "product_id": product_id, "quantity": 0, "removed": True}

    await tracker.redis.hset(key, product_id, new_qty)
    return {"ok": True, "product_id": product_id, "quantity": new_qty, "removed": False}


@router.post("/clear")
async def clear_cart(
    tracker: TrackerDep,
    user_id: Annotated[str, Query()] = "anonymous",
):
    """Delete the entire cart for `user_id`."""
    key = _cart_key(user_id)
    await tracker.redis.delete(key)
    return {"ok": True, "user_id": user_id}
