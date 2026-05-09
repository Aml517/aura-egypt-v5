-- 1. Enable extensions at the very top
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Users & Sessions
CREATE TABLE users (
  -- Changed uuid_generate_v4() to gen_random_uuid()
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  mbti VARCHAR(4),
  favorite_movies JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Itinerary Templates
CREATE TABLE itinerary_templates (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  movie_vibe_vector VECTOR(384),
  mbti_archetype VARCHAR(10),
  days INTEGER,
  price_min DECIMAL,
  price_max DECIMAL,
  activities JSONB,
  image_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Conversations
CREATE TABLE conversations (
  -- Changed uuid_generate_v4() to gen_random_uuid()
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  movie_title VARCHAR,
  vibe_match DECIMAL,
  itinerary_id INTEGER REFERENCES itinerary_templates(id),
  created_at TIMESTAMP DEFAULT NOW()
);