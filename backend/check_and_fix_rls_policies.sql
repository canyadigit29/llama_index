-- This SQL script analyzes and fixes common RLS policy issues
-- Run this in your Supabase SQL Editor

-- Show all tables and their RLS status
SELECT
  table_schema,
  table_name,
  CASE
    WHEN EXISTS (
      SELECT 1
      FROM pg_policy
      JOIN pg_class ON pg_class.oid = pg_policy.polrelid
      JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
      WHERE pg_namespace.nspname = table_schema AND pg_class.relname = table_name
    ) THEN true
    ELSE false
  END AS has_rls_policies,
  row_security_active AS is_rls_enabled
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Show all RLS policies in detail
SELECT 
  schemaname, 
  tablename, 
  policyname, 
  permissive, 
  roles, 
  cmd, 
  qual AS policy_definition
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Create RLS policies for llama_index_documents if needed
DO $$
BEGIN
  -- Check if the table exists
  IF EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name = 'llama_index_documents'
  ) THEN
    -- Enable RLS on the table
    EXECUTE 'ALTER TABLE public.llama_index_documents ENABLE ROW LEVEL SECURITY';
    
    -- Check if the policy exists before creating
    IF NOT EXISTS (
      SELECT FROM pg_policies 
      WHERE schemaname = 'public' AND 
            tablename = 'llama_index_documents' AND 
            policyname = 'Allow authenticated read access'
    ) THEN
      -- Create read access policy
      CREATE POLICY "Allow authenticated read access" 
      ON public.llama_index_documents
      FOR SELECT 
      TO authenticated
      USING (true);  -- All authenticated users can read
      
      RAISE NOTICE 'Created read policy for llama_index_documents';
    ELSE
      RAISE NOTICE 'Read policy for llama_index_documents already exists';
    END IF;
    
    -- Check if the policy exists before creating
    IF NOT EXISTS (
      SELECT FROM pg_policies 
      WHERE schemaname = 'public' AND 
            tablename = 'llama_index_documents' AND 
            policyname = 'Allow authenticated insert access'
    ) THEN
      -- Create write access policy
      CREATE POLICY "Allow authenticated insert access" 
      ON public.llama_index_documents
      FOR INSERT 
      TO authenticated
      WITH CHECK (true);  -- All authenticated users can insert
      
      RAISE NOTICE 'Created insert policy for llama_index_documents';
    ELSE
      RAISE NOTICE 'Insert policy for llama_index_documents already exists';
    END IF;
    
    -- Check if the policy exists before creating
    IF NOT EXISTS (
      SELECT FROM pg_policies 
      WHERE schemaname = 'public' AND 
            tablename = 'llama_index_documents' AND 
            policyname = 'Allow authenticated update access'
    ) THEN
      -- Create update access policy
      CREATE POLICY "Allow authenticated update access" 
      ON public.llama_index_documents
      FOR UPDATE
      TO authenticated
      USING (true)
      WITH CHECK (true);
      
      RAISE NOTICE 'Created update policy for llama_index_documents';
    ELSE
      RAISE NOTICE 'Update policy for llama_index_documents already exists';
    END IF;
    
    -- Check if the storage.objects policy exists
    -- This is needed for document uploads to work
    IF EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_schema = 'storage' AND table_name = 'objects'
    ) THEN
      -- We can't directly check storage policies with the same query,
      -- so we'll try to create them and catch errors
      BEGIN
        -- Create policy to allow authenticated users to use storage
        CREATE POLICY "Allow authenticated storage" 
        ON storage.objects
        FOR ALL
        TO authenticated
        USING (true)
        WITH CHECK (true);
        
        RAISE NOTICE 'Created policy for storage.objects';
      EXCEPTION WHEN others THEN
        RAISE NOTICE 'Policy for storage.objects may already exist: %', SQLERRM;
      END;
    END IF;
    
    RAISE NOTICE 'RLS policies for llama_index_documents have been set up successfully';
  ELSE
    RAISE NOTICE 'Table llama_index_documents does not exist';
  END IF;
END
$$;

-- Show service-level permissions (service account vs. anonymous access)
SELECT 
  grantee, 
  table_schema, 
  table_name, 
  privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' 
  AND grantee IN ('anon', 'authenticated', 'service_role')
ORDER BY table_schema, table_name, grantee;
