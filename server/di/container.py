from dependency_injector import containers, providers

from core.config import get_settings
from di.resources import init_infra_clients, init_repositories, init_caches, init_kafka_components, init_core_components, init_services

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "api.v1.routes.profile",
            "api.v1.routes.media",
            "api.v1.routes.recommendation",
            "api.v1.routes.swipe"
        ]
    )

    config = providers.Singleton(get_settings)

    infra_clients = providers.Resource(
        init_infra_clients,
        settings=config
    )

    repositories = providers.Singleton(
        init_repositories,
        pool=infra_clients.provided.postgres
    )

    caches = providers.Singleton(
        init_caches,
        redis=infra_clients.provided.redis
    )

    core = providers.Singleton(
        init_core_components,
        profile_repo=repositories.provided.profile,
        recommendation_cache=caches.provided.recommendation,
        swipe_cache=caches.provided.swipe,
        s3_client=infra_clients.provided.s3,
        clickhouse_client=infra_clients.provided.clickhouse,
        settings=config
    )

    kafka = providers.Resource(
        init_kafka_components,
        settings=config,
        profile_repo=repositories.provided.profile,
        recommendation_cache=caches.provided.recommendation
    )

    services = providers.Singleton(
        init_services,
        profile_repo=repositories.provided.profile,
        media_repo=repositories.provided.media,
        swipe_repo=repositories.provided.swipe,
        recommendation_cache=caches.provided.recommendation,
        swipe_cache=caches.provided.swipe,
        recommender=core.provided.recommender,
        uploader=core.provided.uploader,
        logger=core.provided.logger,
        producer=kafka.provided.producer,
        settings=config
    )
