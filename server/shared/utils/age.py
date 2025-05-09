from typing import Tuple

def get_match_age_range(age: int) -> Tuple[int, int]:
    if not 12 <= age <= 100:
        raise ValueError("Age must be in range [12, 100].")

    ethical_min = int(age / 2 + 7)
    ethical_max = int((age - 7) * 2)

    delta = 1.5 if age < 18 else min(12, 2 + (age - 18) * 0.25)

    soft_min = age - delta
    soft_max = age + delta

    min_age = max(12, round((soft_min + ethical_min) / 2))
    max_age = min(100, round((soft_max + ethical_max) / 2))

    return min_age, max_age
