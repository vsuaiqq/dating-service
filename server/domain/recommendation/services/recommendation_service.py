from recsys.embedding_recommender import EmbeddingRecommender
from api.v1.schemas.recommendation import GetRecommendationsResponse, RecommendationItem

class RecommendationService:
    def __init__(self, recommender: EmbeddingRecommender):
        self.recommender = recommender

    async def get_recommendations(self, user_id: int, count: int) -> GetRecommendationsResponse:
        recommendations = await self.recommender.get_hybrid_recommendations(user_id, count)
        return GetRecommendationsResponse(
            recommendations=[
                RecommendationItem(user_id=uid, distance=dist)
                for uid, dist in recommendations
            ]
        )
