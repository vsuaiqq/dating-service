CREATE TYPE GENDER AS ENUM (
    'male', 
    'female'
);

CREATE TYPE INTERESTING_GENDER AS ENUM (
    'male', 
    'female',
    'any'
);

CREATE TYPE MEDIA_TYPE AS ENUM (
    'photo',
    'video'
);

CREATE TABLE IF NOT EXISTS profiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    gender GENDER,
    city VARCHAR(255),
    age INT,
    interesting_gender INTERESTING_GENDER,
    about TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON profiles(user_id);

CREATE TABLE IF NOT EXISTS media (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    s3_key TEXT NOT NULL,
    type MEDIA_TYPE
);

CREATE INDEX idx_profile_media ON media(profile_id);
