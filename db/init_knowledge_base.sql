-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for storing document embeddings
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedding vector(1536), -- Dimension for text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for faster similarity search
CREATE INDEX IF NOT EXISTS knowledge_base_embedding_idx ON knowledge_base USING hnsw (embedding vector_cosine_ops);

-- Create RPC function for vector search (required for Supabase API)
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  filter_region text
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    knowledge_base.id,
    knowledge_base.content,
    knowledge_base.metadata,
    1 - (knowledge_base.embedding <=> query_embedding) AS similarity
  FROM knowledge_base
  WHERE 1 - (knowledge_base.embedding <=> query_embedding) > match_threshold
  AND (
      (knowledge_base.metadata->>'region' = filter_region)
      OR 
      (knowledge_base.metadata->>'region' = 'generic')
      OR
      filter_region IS NULL
  )
  ORDER BY knowledge_base.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
