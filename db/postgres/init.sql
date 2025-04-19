CREATE TABLE users (
    id BIGINT GENERATED always AS IDENTITY primary key,
    telegram_id BIGINT UNIQUE NOT NULL,
    phone_number TEXT NOT NULL,
    username TEXT,
    age INT,
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    preferred_gender TEXT CHECK (preferred_gender IN ('male', 'female', 'any')),
    city TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    about TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_online TIMESTAMP
);

CREATE INDEX idx_users_city ON users(city);
CREATE INDEX idx_users_age ON users(age);
CREATE INDEX idx_users_lat_lon ON users(lat, lon);
CREATE INDEX idx_users_created_at ON users(created_at);


CREATE TYPE swipe_action AS ENUM ('like', 'dislike', 'question');

CREATE TABLE swipes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    from_user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    to_user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    action swipe_action NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (from_user_id, to_user_id)
);

CREATE INDEX idx_swipes_from_user ON swipes(from_user_id);
CREATE INDEX idx_swipes_to_user ON swipes(to_user_id);
CREATE INDEX idx_swipes_action ON swipes(action);

CREATE TABLE matches (
    user1_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    user2_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user1_id, user2_id)
);

CREATE TABLE user_photos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    s3_path TEXT NOT NULL,
    is_main BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_photos_user ON user_photos(user_id);