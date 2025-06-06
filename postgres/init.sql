CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS postgis;

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

CREATE TYPE SWIPE_ACTION AS ENUM (
    'like', 
    'dislike', 
    'question'
);

CREATE TABLE IF NOT EXISTS profiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    gender GENDER,
    city VARCHAR(255),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    age INT,
    interesting_gender INTERESTING_GENDER,
    about TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    about_embedding DOUBLE PRECISION[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location geography(Point, 4326)
);

CREATE TABLE IF NOT EXISTS media (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL,
    s3_key TEXT NOT NULL,
    type MEDIA_TYPE
);

CREATE TABLE IF NOT EXISTS swipes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    from_user_id BIGINT NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    to_user_id BIGINT NOT NULL REFERENCES profiles(user_id) ON DELETE CASCADE,
    action SWIPE_ACTION NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (from_user_id, to_user_id)
);

CREATE INDEX idx_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_location ON profiles USING GIST(location);
CREATE INDEX idx_profile_media ON media(user_id);
CREATE INDEX idx_swipes_from_user ON swipes(from_user_id);
CREATE INDEX idx_swipes_to_user ON swipes(to_user_id);
CREATE INDEX idx_swipes_action ON swipes(action);

CREATE OR REPLACE FUNCTION update_location_on_coords_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS DISTINCT FROM OLD.latitude OR NEW.longitude IS DISTINCT FROM OLD.longitude THEN
        NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_location
BEFORE UPDATE ON profiles
FOR EACH ROW
EXECUTE FUNCTION update_location_on_coords_change();
