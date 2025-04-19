-- Создаем расширение для работы с массивами
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Создаем тип для свайпов
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'swipe_action') THEN
        CREATE TYPE swipe_action AS ENUM ('like', 'dislike', 'question');
    END IF;
END$$;

-- Создаем таблицу users
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    phone_number TEXT NOT NULL,
    username TEXT,
    age INT CHECK (age >= 18),
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    preferred_gender TEXT CHECK (preferred_gender IN ('male', 'female', 'any')),
    city TEXT,
    about TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_online TIMESTAMP,
    description_embedding DOUBLE PRECISION[]
);

-- Создаем индексы для users
CREATE INDEX IF NOT EXISTS idx_users_city ON users(city);
CREATE INDEX IF NOT EXISTS idx_users_age ON users(age);
CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender);
CREATE INDEX IF NOT EXISTS idx_users_preferred_gender ON users(preferred_gender);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Создаем таблицу swipes
CREATE TABLE IF NOT EXISTS swipes (
    id BIGSERIAL PRIMARY KEY,
    from_user_id BIGINT NOT NULL,
    to_user_id BIGINT NOT NULL,
    action swipe_action NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (from_user_id, to_user_id),
    FOREIGN KEY (from_user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (to_user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- Создаем таблицу matches
CREATE TABLE IF NOT EXISTS matches (
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user1_id, user2_id),
    FOREIGN KEY (user1_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- Создаем таблицу user_photos
CREATE TABLE IF NOT EXISTS user_photos (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    file_id TEXT NOT NULL,
    is_main BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- Создаем индексы для других таблиц
CREATE INDEX IF NOT EXISTS idx_swipes_from_user ON swipes(from_user_id);
CREATE INDEX IF NOT EXISTS idx_swipes_to_user ON swipes(to_user_id);
CREATE INDEX IF NOT EXISTS idx_swipes_action ON swipes(action);
CREATE INDEX IF NOT EXISTS idx_user_photos_user ON user_photos(user_id);