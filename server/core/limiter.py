from fastapi import Request

def get_user_id_rate_key(request: Request) -> str:
    user_id = request.headers.get("X-User-ID")
    return f"user:{user_id}"
