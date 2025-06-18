-- Supabase Authentication and Storage Troubleshooting
-- Run this in your Supabase SQL Editor to diagnose and fix issues

-- ========================
-- PART 1: DATABASE ACCESS CHECKS
-- ========================

-- Check if the llama_index_documents table exists
SELECT EXISTS (
  SELECT FROM information_schema.tables 
  WHERE table_name = 'llama_index_documents'
) AS llama_index_documents_exists;

-- Create llama_index_documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS llama_index_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  supabase_file_id UUID NOT NULL,
  processed BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================
-- PART 2: STORAGE BUCKET SETUP
-- ========================

-- Create the 'files' bucket if it doesn't exist
DO $$
BEGIN
  INSERT INTO storage.buckets (id, name, public, avif_autodetection)
  VALUES ('files', 'files', FALSE, FALSE)
  ON CONFLICT (id) DO NOTHING;
END
$$;

-- ========================
-- PART 3: RLS POLICIES
-- ========================

-- Enable Row Level Security on both tables
ALTER TABLE IF EXISTS public.llama_index_documents ENABLE ROW LEVEL SECURITY;

-- Check existing policies for llama_index_documents
SELECT 
  tablename, 
  policyname, 
  roles,
  permissive,
  cmd,
  qual AS policy_definition
FROM pg_policies 
WHERE schemaname = 'public' AND 
      tablename = 'llama_index_documents';

-- Create RLS policies for llama_index_documents if they don't exist
DO $$
BEGIN
  -- Select policy
  IF NOT EXISTS (
    SELECT FROM pg_policies 
    WHERE schemaname = 'public' AND 
          tablename = 'llama_index_documents' AND 
          policyname = 'Enable select for authenticated users'
  ) THEN
    CREATE POLICY "Enable select for authenticated users" 
      ON llama_index_documents FOR SELECT 
      TO authenticated USING (true);
    RAISE NOTICE 'Created select policy for llama_index_documents';
  END IF;

  -- Insert policy
  IF NOT EXISTS (
    SELECT FROM pg_policies 
    WHERE schemaname = 'public' AND 
          tablename = 'llama_index_documents' AND 
          policyname = 'Enable insert for authenticated users'
  ) THEN
    CREATE POLICY "Enable insert for authenticated users" 
      ON llama_index_documents FOR INSERT 
      TO authenticated WITH CHECK (auth.uid() = auth.uid());
    RAISE NOTICE 'Created insert policy for llama_index_documents';
  END IF;

  -- Update policy
  IF NOT EXISTS (
    SELECT FROM pg_policies 
    WHERE schemaname = 'public' AND 
          tablename = 'llama_index_documents' AND 
          policyname = 'Enable update for authenticated users'
  ) THEN
    CREATE POLICY "Enable update for authenticated users" 
      ON llama_index_documents FOR UPDATE
      TO authenticated USING (true) WITH CHECK (true);
    RAISE NOTICE 'Created update policy for llama_index_documents';
  END IF;
END
$$;

-- ========================
-- PART 4: STORAGE RLS POLICIES
-- ========================

-- Check for storage policies
SELECT 
  tablename, 
  policyname, 
  roles,
  permissive,
  cmd
FROM pg_policies 
WHERE schemaname = 'storage' AND 
      tablename = 'objects';

-- Create storage policies if they don't exist
DO $$
BEGIN
  -- For objects storage table
  IF NOT EXISTS (
    SELECT FROM pg_policies 
    WHERE schemaname = 'storage' AND 
          tablename = 'objects' AND 
          policyname = 'Allow authenticated users to read files'
  ) THEN
    CREATE POLICY "Allow authenticated users to read files"
      ON storage.objects FOR SELECT
      TO authenticated USING (bucket_id = 'files');
    RAISE NOTICE 'Created storage read policy';
  END IF;

  IF NOT EXISTS (
    SELECT FROM pg_policies 
    WHERE schemaname = 'storage' AND 
          tablename = 'objects' AND 
          policyname = 'Allow authenticated users to upload files'
  ) THEN
    CREATE POLICY "Allow authenticated users to upload files"
      ON storage.objects FOR INSERT
      TO authenticated WITH CHECK (bucket_id = 'files');
    RAISE NOTICE 'Created storage insert policy';
  END IF;
END
$$;

-- ========================
-- PART 5: VERIFY PERMISSION GRANTS
-- ========================

-- Check permissions for authenticated users
SELECT 
  grantee, 
  table_schema, 
  table_name, 
  privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' 
  AND table_name = 'llama_index_documents'
  AND grantee IN ('anon', 'authenticated', 'service_role');

-- Grant permissions if needed
GRANT ALL ON public.llama_index_documents TO authenticated;
GRANT ALL ON public.llama_index_documents TO service_role;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- ========================
-- PART 6: DIAGNOSTICS
-- ========================

-- List all storage buckets
SELECT * FROM storage.buckets;

-- Show sample files if any exist
SELECT * FROM storage.objects LIMIT 5;

-- Check for any llama_index_documents records
SELECT * FROM llama_index_documents LIMIT 5;

-- Exit message
DO $$
BEGIN
  RAISE NOTICE '=========================================';
  RAISE NOTICE 'Supabase setup complete';
  RAISE NOTICE 'Tables checked/created: llama_index_documents';
  RAISE NOTICE 'Buckets checked/created: files';
  RAISE NOTICE 'RLS policies configured for tables and storage';
  RAISE NOTICE 'Permissions granted to authenticated users';
  RAISE NOTICE '=========================================';
END
$$;
