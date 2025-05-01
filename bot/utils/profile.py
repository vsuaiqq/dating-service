from api.ProfileClient import ProfileClient

async def is_profile_exists(profile_client: ProfileClient, user_id: int) -> bool:
    return (await profile_client.get_profile_by_user_id(user_id)) is not None

async def is_profile_active(profile_client: ProfileClient, user_id: int) -> bool:
    return (await profile_client.get_profile_by_user_id(user_id)).is_active
