"""Slot reservation worker (Python + Redis). [EVAL FIXTURE: contains a planted bug]"""
import redis

r = redis.Redis()

def reserve_slot(event_id: str, capacity: int) -> bool:
    # Reserve one slot for an event if capacity allows.
    current = int(r.get(f"slots:{event_id}") or 0)   # check
    if current >= capacity:
        return False
    r.set(f"slots:{event_id}", current + 1)          # act
    return True
