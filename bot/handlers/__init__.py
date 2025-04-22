from .profile import router as profile_router
from .core import router as core_router
from .feed import router as feed_router

all_handlers = [profile_router, core_router, feed_router]
