def get_city_coords_key(city: str) -> str:
        return f"city_coords:{city.lower()}"

def get_recs_key(user_id: int) -> str:
        return f"recs:{user_id}"

def get_swipes_key(user_id: int) -> str:
        return f"swipes:{user_id}"
