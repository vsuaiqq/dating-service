import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import random

from postgres.ProfileRepository import ProfileRepository

class EmbeddingRecommender:
    def __init__(self, profile_repo: ProfileRepository, embedding_size = 384, recsys_coeff = 0.6, model = None):
        self.model = model
        self.profile_repo = profile_repo
        self.embedding_size = embedding_size
        self.recsys_coeff = recsys_coeff

    async def _load_model(self):
        if self.model is None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.model

    async def _get_similar_profiles_by_embedding(
        self, user_id: int, count: int = 5
    ) -> List[Dict]:
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user or not user.get('about_embedding'):
            return []

        user_embedding = np.array(user['about_embedding']).reshape(1, -1)
        candidates = await self.profile_repo.get_candidates_with_embeddings(user_id, user)

        if not candidates:
            return []

        similarities = []
        for candidate in candidates:
            cand_embedding = np.array(candidate['about_embedding']).reshape(1, -1)
            similarity = cosine_similarity(user_embedding, cand_embedding)[0][0]
            similarities.append((similarity, candidate))

        similarities.sort(key=lambda x: x[0], reverse=True)
        top_matches = [dict(candidate) for _, candidate in similarities[:count]]
        return top_matches

    async def _get_random_profiles_by_criteria(
        self, user_id: int, count: int = 5, rec_list: List[int] = None
    ) -> List[Dict]:
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user:
            return []

        records = await self.profile_repo.get_candidates_by_criteria(user_id, user, rec_list)
        if not records:
            return []

        random.shuffle(records)
        return [dict(r) for r in records[:count]]

    async def update_user_embedding(self, user_id: int):
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user or not user.get('about'):
            return

        model = await self._load_model()
        embedding = model.encode(user['about'], convert_to_tensor=False)
        await self.profile_repo.update_embedding(user_id, embedding)

    async def get_hybrid_recommendations(
            self, user_id: int, count: int = 10
    ) -> List[Dict]:
        content_count = int(count * self.recsys_coeff)  
        random_count = count - content_count  

        content_based = await self._get_similar_profiles_by_embedding(user_id, count=content_count)
        random_based = await self._get_random_profiles_by_criteria(user_id, count=random_count, rec_list=[user['user_id'] for user in content_based])

        unique_ids = set()
        final_results = []

        for profile in content_based:
            if profile["user_id"] not in unique_ids:
                unique_ids.add(profile["user_id"])
                final_results.append(profile)
        for profile in random_based:
            if profile["user_id"] not in unique_ids:
                unique_ids.add(profile["user_id"])
                final_results.append(profile)

        return final_results[:count]
