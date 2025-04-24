import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
import random
import re
from nltk.stem import WordNetLemmatizer
import pymorphy2
from langdetect import detect
from postgres.ProfileRepository import ProfileRepository
from redis.asyncio import Redis
from typing import Optional, Dict

from utils.age import get_match_age_range

class EmbeddingRecommender:
    def __init__(
            self, 
            profile_repo: ProfileRepository, 
            redis: Redis, 
            redis_ttl,
            embedding_size = 384, 
            recsys_coeff = 0.7, 
            stop_words = [], 
            max_distance_search = 20, 
            model = None
            ):
        self.model = model
        self.profile_repo = profile_repo
        self.redis = redis
        self.ttl = redis_ttl
        self.embedding_size = embedding_size
        self.recsys_coeff = recsys_coeff
        self.stop_words = stop_words
        self.max_distance_search = max_distance_search
        self.lemmatizer = WordNetLemmatizer()
        self.morph = pymorphy2.MorphAnalyzer()

    def _cache_key(self, user_id: int) -> str:
        return f"recs:{user_id}"

    async def cache_recommendations(self, user_id: int, recommendations: List[Dict]):
        if not recommendations:
            return
            
        key = self._cache_key(user_id)
        pipe = self.redis.pipeline()
        
        pipe.delete(key)
        
        for rec in recommendations:
            pipe.rpush(key, rec['user_id'])
        
        pipe.expire(key, self.ttl)
        await pipe.execute()

    async def get_cached_recommendations(self, user_id: int) -> Optional[List[Dict]]:
        key = self._cache_key(user_id)
        rec_ids = await self.redis.lrange(key, 0, -1)
        
        if not rec_ids:
            return None
            
        profiles = []
        for rec_id in rec_ids:
            profile = await self.profile_repo.get_profile_by_user_id(int(rec_id))
            if profile:
                profiles.append(dict(profile))
        
        return profiles

    async def _load_model(self):
        if self.model is None:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.model

    async def _preprocess_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^a-zа-яё0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        lang = detect(text)

        words = text.split()

        lemmas = []
        for word in words:
            if word not in self.stop_words and len(word) > 2:
                if lang == 'ru':
                    lemmas.append(self.morph.parse(word)[0].normal_form)
                elif lang == 'en':
                    lemmas.append(self.lemmatizer.lemmatize(word))
                else:
                    lemmas.append(word)

        return ' '.join(lemmas)

    async def _get_similar_profiles_by_embedding(
        self, user_id: int, count: int = 5
    ) -> List[int]:
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user or not user.get('about_embedding'):
            return []

        user_embedding = np.array(user['about_embedding']).reshape(1, -1)
        min_age, max_age = get_match_age_range(user['age'])
        users = await self.profile_repo.get_candidates_with_embeddings(
            user_id, user, self.max_distance_search, min_age, max_age
        )

        if not users:
            return []

        similarities = []
        for candidate in users:
            cand_embedding = np.array(candidate['about_embedding']).reshape(1, -1)
            similarity = cosine_similarity(user_embedding, cand_embedding)[0][0]
            similarities.append((similarity, candidate))

        similarities.sort(key=lambda x: x[0], reverse=True)
        top_matches = [candidate['user_id'] for _, candidate in similarities[:count]]
        return top_matches

    async def _get_random_profiles_by_criteria(
        self, user_id: int, count: int = 5, rec_list: List[int] = None
    ) -> List[int]:
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user:
            return []

        min_age, max_age = get_match_age_range(user['age'])
        users = await self.profile_repo.get_candidates_by_criteria(user_id, user, rec_list, min_age, max_age)
        if not users:
            return []

        random.shuffle(users)
        return users[:count]

    async def update_user_embedding(self, user_id: int):
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user or not user.get('about'):
            return

        model = await self._load_model()
        preprocessed_about = await self._preprocess_text(user['about'])
        embedding = model.encode(preprocessed_about, convert_to_tensor=False)
        await self.profile_repo.update_embedding(user_id, embedding)

    async def get_hybrid_recommendations(
            self, user_id: int, count: int = 30
    ) -> List[int]:
        cached = await self.get_cached_recommendations(user_id)
        if cached:
            return cached[:count]
        
        content_count = int(count * self.recsys_coeff)  
        random_count = count - content_count  

        content_based = await self._get_similar_profiles_by_embedding(user_id, count=content_count)
        random_based = await self._get_random_profiles_by_criteria(user_id, count=random_count, rec_list=content_based)
        final_results = list(set(content_based + random_based))[:count]

        await self.cache_recommendations(user_id, final_results)

        return final_results
