CREATE DATABASE IF NOT EXISTS dating_db;

USE dating_db;

CREATE TABLE user_actions (
    action_time DateTime,
    user_id UInt64,
    action_type String,
    target_user_id UInt64,
    message String
)
ENGINE = MergeTree()
ORDER BY (user_id, action_time);
