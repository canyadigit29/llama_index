-- Migrations for updating LlamaIndex document tracking table
-- Drop existing policies and recreate them

-- Drop existing policies (will not error if they don't exist)
DO $$ 
BEGIN
  -- Drop policies if they exist
  BEGIN
    DROP POLICY IF EXISTS "Users can view their own documents" ON "public"."llama_index_documents";
  EXCEPTION WHEN OTHERS THEN
    -- Do nothing, continue with script
  END;
  
  BEGIN
    DROP POLICY IF EXISTS "Users can insert their own documents" ON "public"."llama_index_documents";
  EXCEPTION WHEN OTHERS THEN
    -- Do nothing
  END;
  
  BEGIN
    DROP POLICY IF EXISTS "Users can update their own documents" ON "public"."llama_index_documents";
  EXCEPTION WHEN OTHERS THEN
    -- Do nothing
  END;
  
  BEGIN
    DROP POLICY IF EXISTS "Users can delete their own documents" ON "public"."llama_index_documents";
  EXCEPTION WHEN OTHERS THEN
    -- Do nothing
  END;
END $$;

-- Create table if it doesn't exist
CREATE TABLE IF NOT EXISTS "public"."llama_index_documents" (
  "id" uuid NOT NULL DEFAULT uuid_generate_v4(),
  "supabase_file_id" uuid NOT NULL,
  "processed" boolean NOT NULL DEFAULT false,
  "metadata" jsonb,
  "created_at" timestamp with time zone NOT NULL DEFAULT now(),
  "updated_at" timestamp with time zone NOT NULL DEFAULT now(),
  PRIMARY KEY ("id"),
  UNIQUE ("supabase_file_id"),
  CONSTRAINT "fk_supabase_file"
    FOREIGN KEY ("supabase_file_id")
    REFERENCES "public"."files" ("id")
    ON DELETE CASCADE
);

-- Add indexes
CREATE INDEX IF NOT EXISTS "idx_llama_index_documents_supabase_file_id" ON "public"."llama_index_documents" ("supabase_file_id");
CREATE INDEX IF NOT EXISTS "idx_llama_index_documents_processed" ON "public"."llama_index_documents" ("processed");

-- Enable RLS
ALTER TABLE "public"."llama_index_documents" ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own documents" ON "public"."llama_index_documents"
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM "public"."files"
      WHERE "files"."id" = "llama_index_documents"."supabase_file_id"
      AND "files"."user_id" = auth.uid()
    )
  );

CREATE POLICY "Users can insert their own documents" ON "public"."llama_index_documents"
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM "public"."files"
      WHERE "files"."id" = "llama_index_documents"."supabase_file_id"
      AND "files"."user_id" = auth.uid()
    )
  );

CREATE POLICY "Users can update their own documents" ON "public"."llama_index_documents"
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM "public"."files"
      WHERE "files"."id" = "llama_index_documents"."supabase_file_id"
      AND "files"."user_id" = auth.uid()
    )
  );

CREATE POLICY "Users can delete their own documents" ON "public"."llama_index_documents"
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM "public"."files"
      WHERE "files"."id" = "llama_index_documents"."supabase_file_id"
      AND "files"."user_id" = auth.uid()
    )
  );

-- Comments
COMMENT ON TABLE "public"."llama_index_documents" IS 'Table to track documents that have been processed by LlamaIndex';
