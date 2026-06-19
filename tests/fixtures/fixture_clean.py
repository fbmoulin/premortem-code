"""Slot reservation worker (Python + Redis). [EVAL FIXTURE: correct, no real fragility]"""
import redis

r = redis.Redis()

def reserve_slot(event_id: str, capacity: int) -> bool:
    # Atomic reserve: increment first, roll back if over capacity.
    new = r.incr(f"slots:{event_id}")
    if new > capacity:
        r.decr(f"slots:{event_id}")
        return False
    return True
