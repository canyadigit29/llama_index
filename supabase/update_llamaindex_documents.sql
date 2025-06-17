-- Migrations for creating or updating LlamaIndex document tracking table
-- Modified to handle existing policies

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

-- Add indexes (IF NOT EXISTS ensures they won't cause errors if they already exist)
CREATE INDEX IF NOT EXISTS "idx_llama_index_documents_supabase_file_id" ON "public"."llama_index_documents" ("supabase_file_id");
CREATE INDEX IF NOT EXISTS "idx_llama_index_documents_processed" ON "public"."llama_index_documents" ("processed");

-- Enable RLS if not already enabled
ALTER TABLE "public"."llama_index_documents" ENABLE ROW LEVEL SECURITY;

-- Helper function to check if a policy exists before creating it
CREATE OR REPLACE FUNCTION create_policy_if_not_exists(
  policy_name text,
  table_name text,
  action text,
  using_expr text DEFAULT NULL,
  check_expr text DEFAULT NULL
) RETURNS void AS $$
DECLARE
  policy_exists boolean;
BEGIN
  -- Check if policy exists
  SELECT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_policies
    WHERE policyname = policy_name
    AND tablename = table_name
  ) INTO policy_exists;
  
  -- Create policy only if it doesn't exist
  IF NOT policy_exists THEN
    IF action = 'SELECT' OR action = 'DELETE' THEN
      EXECUTE format(
        'CREATE POLICY "%s" ON %s FOR %s USING (%s)',
        policy_name, table_name, action, using_expr
      );
    ELSIF action = 'INSERT' THEN
      EXECUTE format(
        'CREATE POLICY "%s" ON %s FOR %s WITH CHECK (%s)',
        policy_name, table_name, action, check_expr
      );
    ELSIF action = 'UPDATE' THEN
      EXECUTE format(
        'CREATE POLICY "%s" ON %s FOR %s USING (%s)',
        policy_name, table_name, action, using_expr
      );
    END IF;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Create policies only if they don't exist
SELECT create_policy_if_not_exists(
  'Users can view their own documents',
  'llama_index_documents',
  'SELECT',
  'EXISTS (SELECT 1 FROM "public"."files" WHERE "files"."id" = "llama_index_documents"."supabase_file_id" AND "files"."user_id" = auth.uid())'
);

SELECT create_policy_if_not_exists(
  'Users can insert their own documents',
  'llama_index_documents',
  'INSERT',
  NULL,
  'EXISTS (SELECT 1 FROM "public"."files" WHERE "files"."id" = "llama_index_documents"."supabase_file_id" AND "files"."user_id" = auth.uid())'
);

SELECT create_policy_if_not_exists(
  'Users can update their own documents',
  'llama_index_documents',
  'UPDATE',
  'EXISTS (SELECT 1 FROM "public"."files" WHERE "files"."id" = "llama_index_documents"."supabase_file_id" AND "files"."user_id" = auth.uid())'
);

SELECT create_policy_if_not_exists(
  'Users can delete their own documents',
  'llama_index_documents',
  'DELETE',
  'EXISTS (SELECT 1 FROM "public"."files" WHERE "files"."id" = "llama_index_documents"."supabase_file_id" AND "files"."user_id" = auth.uid())'
);

-- Add comment
COMMENT ON TABLE "public"."llama_index_documents" IS 'Table to track documents that have been processed by LlamaIndex';

-- Clean up helper function if you don't want it to persist
DROP FUNCTION create_policy_if_not_exists;
