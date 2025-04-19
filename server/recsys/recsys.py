import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional
import logging
import random

class EmbeddingRecommender:
    def __init__(self, db, embedding_size = 384, recsys_coeff = 0.6, model = None):
        self.db = db
        self.model = model
        self.embedding_size = embedding_size
        self.recsys_coeff = recsys_coeff

    async def load_model(self):
        if self.model is None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.model

    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        query = """
        SELECT telegram_id, username, age, gender, preferred_gender, city, about, description_embedding
        FROM users 
        WHERE telegram_id = $1
        """
        records = await self.db.fetch(query, user_id)
        return dict(records[0]) if records else None

    async def update_user_embedding(self, user_id: int):
        user = await self.get_user_profile(user_id)
        if not user or not user.get('about'):
            return

        model = await self.load_model()
        embedding = model.encode(user['about'], convert_to_tensor=False)
        await self.db.execute(
            "UPDATE users SET description_embedding = $1 WHERE telegram_id = $2",
            embedding.tolist(),
            user_id
        )

    async def get_similar_profiles_by_embedding(
        self, user_id: int, count: int = 5
    ) -> List[Dict]:
        user = await self.get_user_profile(user_id)
        if not user or not user.get('description_embedding'):
            return []

        user_embedding = np.array(user['description_embedding']).reshape(1, -1)
        candidates = await self.db.fetch(
            """
            SELECT *, description_embedding 
            FROM users 
            WHERE telegram_id != $1
            AND is_active = TRUE
            AND description_embedding IS NOT NULL
            AND gender = ANY(
                CASE 
                    WHEN $2 = 'any' THEN ARRAY['male', 'female', 'other']
                    ELSE ARRAY[$2]
                END
            )
            AND age BETWEEN ($3::int - 15) AND ($3::int + 15)
            AND telegram_id NOT IN (
                SELECT to_user_id FROM swipes WHERE from_user_id = $1
            )
            LIMIT 100
            """,
            user_id,
            user['preferred_gender'],
            user['age'],
        )

        if not candidates:
            return []

        similarities = []
        for candidate in candidates:
            cand_embedding = np.array(candidate['description_embedding']).reshape(1, -1)
            similarity = cosine_similarity(user_embedding, cand_embedding)[0][0]
            similarities.append((similarity, candidate))

        similarities.sort(key=lambda x: x[0], reverse=True)
        top_matches = [dict(candidate) for similarity, candidate in similarities[:count]]
        return top_matches

    async def get_random_profiles_by_criteria(
        self, user_id: int, count: int = 5, rec_list: List[int] = None
    ) -> List[Dict]:
        """Случайные профили по фильтру: город, пол, возраст ±3"""
        user = await self.get_user_profile(user_id)
        if not user:
            return []

        records = await self.db.fetch(
            """
            SELECT * FROM users 
            WHERE telegram_id != $1
            AND telegram_id != ANY($5::int[])
            AND is_active = TRUE
            AND city = $2
            AND gender = ANY(
                CASE 
                    WHEN $3 = 'any' THEN ARRAY['male', 'female', 'other']
                    ELSE ARRAY[$3]
                END
            )
            AND age BETWEEN ($4::int - 3) AND ($4::int + 3)
            AND telegram_id NOT IN (
                SELECT to_user_id FROM swipes WHERE from_user_id = $1
            )
            """,
            user_id,
            user["city"],
            user["preferred_gender"],
            user["age"],
            rec_list
        )

        if not records:
            return []

        random.shuffle(records)
        return [dict(r) for r in records[:count]]

    async def get_hybrid_recommendations(
            self, user_id: int, count: int = 10
    ) -> List[Dict]:
        """Гибридная рекомендация: 60% контент + 40% фильтрация"""
        content_count = int(count * self.recsys_coeff)  
        random_count = count - content_count  

        content_based = await self.get_similar_profiles_by_embedding(user_id, count=content_count)
        rec_list = [user['telegram_id'] for user in content_based]

        random_based = await self.get_random_profiles_by_criteria(user_id, count=random_count, rec_list=rec_list)

        unique_ids = set()
        final_results = []

        for profile in content_based:
            if profile["telegram_id"] not in unique_ids:
                unique_ids.add(profile["telegram_id"])
                final_results.append(profile)

        for profile in random_based:
            if profile["telegram_id"] not in unique_ids:
                unique_ids.add(profile["telegram_id"])
                final_results.append(profile)

        return final_results[:count]
