CREATE DATABASE IF NOT EXISTS dating_bot;

USE dating_bot;

CREATE TABLE user_swipes
(
    from_user_id     UInt64,
    to_user_id       UInt64,
    
    action           Enum8('like' = 1, 'dislike' = 2, 'question' = 3),
    message          Nullable(String),
    
    created_at       DateTime,
    event_date       Date MATERIALIZED toDate(created_at),
    
    from_city        LowCardinality(String),
    to_city          LowCardinality(String),
    
    from_gender      Enum8('male' = 1, 'female' = 2),
    to_gender        Enum8('male' = 1, 'female' = 2),
    
    from_age         UInt8,
    to_age           UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (from_user_id, created_at)
TTL created_at + INTERVAL 6 MONTH
SETTINGS index_granularity = 8192;
