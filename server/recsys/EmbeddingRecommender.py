import numpy as np
import random
import re
import pymorphy2
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
from nltk.stem import WordNetLemmatizer
from langdetect import detect
from math import radians, sin, cos, sqrt, atan2

from database.ProfileRepository import ProfileRepository
from cache.RecommendationCache import RecommendationCache
from cache.SwipeCache import SwipeCache
from utils.age import get_match_age_range

class EmbeddingRecommender:
    def __init__(
            self, 
            profile_repo: ProfileRepository, 
            recommendation_cache: RecommendationCache,
            swipe_cache: SwipeCache,
            embedding_size = 384, 
            recsys_coeff = 0.7, 
            stop_words = [], 
            max_distance_search = 20, 
            model = None
    ):
        self.model = model or SentenceTransformer('all-MiniLM-L6-v2')
        self.profile_repo = profile_repo
        self.recommendation_cache = recommendation_cache
        self.swipe_cache = swipe_cache
        self.embedding_size = embedding_size
        self.recsys_coeff = recsys_coeff
        self.stop_words = stop_words
        self.max_distance_search = max_distance_search
        self.lemmatizer = WordNetLemmatizer()
        self.morph = pymorphy2.MorphAnalyzer()

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return 6371 * c

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
    ) -> List[Tuple[int, float]]:
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
        top_matches = [
            (candidate['user_id'], candidate['dist'])
            for _, candidate in similarities[:count]
        ]
        return top_matches

    async def _get_random_profiles_by_criteria(
            self, user_id: int, count: int = 5, rec_list: List[int] = None
    ) -> List[Tuple[int, float]]:
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user:
            return []

        min_age, max_age = get_match_age_range(user['age'])

        candidate_ids = await self.profile_repo.get_candidates_by_criteria(
            user_id, user, rec_list, min_age, max_age, self.max_distance_search
        )
        if not candidate_ids:
            return []

        results = []
        user_lat = user['latitude']
        user_lon = user['longitude']

        for cand_id in candidate_ids:
            cand_profile = await self.profile_repo.get_profile_by_user_id(cand_id)
            if cand_profile and cand_profile.get('latitude') and cand_profile.get('longitude'):
                distance = self.calculate_distance(
                    user_lat, user_lon,
                    cand_profile['latitude'], cand_profile['longitude']
                )
                results.append((cand_id, distance))

        random.shuffle(results)
        return results[:count]

    async def update_user_embedding(self, user_id: int):
        user = await self.profile_repo.get_profile_by_user_id(user_id)
        if not user or not user.get('about'):
            return

        preprocessed_about = await self._preprocess_text(user['about'])
        embedding = self.model.encode(preprocessed_about, convert_to_tensor=False)
        await self.profile_repo.update_embedding(user_id, embedding)
        
    async def get_hybrid_recommendations(
        self, user_id: int, count: int
    ) -> List[Tuple[int, float]]:
        already_swiped = await self.swipe_cache.get_all_swiped_ids(user_id)

        cached = await self.recommendation_cache.get(user_id)
        if cached:
            filtered = [
                (uid, dist)
                for uid, dist in cached
                if uid not in already_swiped
            ][:count]
            return filtered

        content_count = int(count * self.recsys_coeff)
        random_count = count - content_count

        content_based = await self._get_similar_profiles_by_embedding(user_id, content_count)
        content_filtered = [
            (uid, dist)
            for uid, dist in content_based
            if uid not in already_swiped
        ]

        random_based = await self._get_random_profiles_by_criteria(
            user_id, random_count, [uid for uid, _ in content_filtered]
        )
        random_filtered = [
            (uid, dist)
            for uid, dist in random_based
            if uid not in already_swiped
        ]

        seen = set()
        final_results = []
        for uid, dist in content_filtered + random_filtered:
            if uid not in seen:
                seen.add(uid)
                final_results.append((uid, dist))
        final_results = final_results[:count]

        if final_results:
            await self.recommendation_cache.set(user_id, final_results)

        return final_results
