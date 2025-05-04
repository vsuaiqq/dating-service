from recsys.EmbeddingRecommender import EmbeddingRecommender
from models.api.recsys.responses import GetRecommendationsResponse

class RecommendationsService:
    def __init__(self, recommender: EmbeddingRecommender):
        self.recommender = recommender
    
    async def get_recommendations(self, user_id: int, count: int) -> GetRecommendationsResponse:
        recommendations = await self.recommender.get_hybrid_recommendations(user_id, count)
        return GetRecommendationsResponse(recommendations=recommendations)
