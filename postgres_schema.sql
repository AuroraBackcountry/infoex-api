-- PostgreSQL Schema for Aurora InfoEx Reporting System
-- Each row represents a single API call to InfoEx

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop existing tables if needed (for clean setup)
DROP TABLE IF EXISTS report_capsules CASCADE;
DROP TABLE IF EXISTS capsule_templates CASCADE;

-- =====================================================
-- CAPSULE TEMPLATES TABLE (Static templates)
-- =====================================================
CREATE TABLE capsule_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_type VARCHAR(50) NOT NULL UNIQUE,
    template_version VARCHAR(10) DEFAULT '1.0',
    capsule_structure JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX idx_capsule_templates_type ON capsule_templates(capsule_type);

-- =====================================================
-- REPORT CAPSULES TABLE (Each row = one API submission)
-- =====================================================
CREATE TABLE report_capsules (
    -- Primary identification
    capsule_uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_report_uuid UUID NOT NULL, -- Groups all capsules for a daily report
    report_type VARCHAR(50) NOT NULL, -- 'field_summary', 'avalanche_observation', etc.
    sequence_number INTEGER DEFAULT 1, -- For multiple observations of same type (avalanche 1, 2, 3)
    
    -- Report metadata
    report_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    
    -- User/Operation info
    user_id TEXT NOT NULL,
    user_name TEXT NOT NULL,
    guide_names TEXT[], -- Array for multiple guides
    operation_uuid UUID NOT NULL,
    operation_name TEXT,
    location_uuids UUID[] NOT NULL,
    zone_name TEXT,
    zone_uuid UUID,
    mountain_range TEXT,
    mountain_range_uuid UUID,
    
    -- Location data
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOGRAPHY GENERATED ALWAYS AS (
        CASE
            WHEN (latitude IS NOT NULL AND longitude IS NOT NULL) 
            THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
            ELSE NULL::geography
        END
    ) STORED,
    
    -- Capsule-specific fields
    question TEXT,
    is_complete BOOLEAN DEFAULT FALSE,
    missing_required_fields TEXT[],
    missing_ideal_fields TEXT[],
    
    -- Content fields (single object for each row)
    payload JSONB NOT NULL DEFAULT '{}', -- Single avalanche, hazard assessment, etc.
    markdown_content TEXT, -- Markdown representation
    embedding vector(1536), -- OpenAI embeddings
    data_tsv TSVECTOR, -- Full text search
    
    -- Submission tracking
    submission_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'validated', 'submitted', 'error'
    submission_state VARCHAR(20) DEFAULT 'IN_REVIEW', -- 'IN_REVIEW' or 'SUBMITTED'
    infoex_response JSONB,
    infoex_uuid TEXT, -- UUID returned by InfoEx for this specific submission
    validation_errors JSONB,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    -- Extracted fields for quick queries (populated by triggers)
    max_avalanche_size NUMERIC(2,1),
    trigger_type TEXT, -- Single trigger for this observation
    hazard_rating_alp TEXT,
    hazard_rating_tl TEXT,
    hazard_rating_btl TEXT,
    weather_summary JSONB,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- Constraints
    CONSTRAINT capsules_type_check CHECK (
        report_type IN (
            'initial_data_collection',
            'field_summary',
            'avalanche_observation',
            'avalanche_summary',
            'hazard_assessment',
            'snowpack_summary',
            'snowProfile_observation',
            'terrain_observation',
            'pwl_persistent_weak_layer',
            'complete_daily_report'
        )
    ),
    CONSTRAINT capsules_status_check CHECK (
        submission_status IN ('pending', 'validated', 'submitted', 'error', 'retry')
    ),
    CONSTRAINT capsules_state_check CHECK (
        submission_state IN ('IN_REVIEW', 'SUBMITTED')
    )
);

-- Indexes for performance
CREATE INDEX idx_capsules_parent ON report_capsules(parent_report_uuid);
CREATE INDEX idx_capsules_type ON report_capsules(report_type);
CREATE INDEX idx_capsules_date ON report_capsules(report_date DESC);
CREATE INDEX idx_capsules_user ON report_capsules(user_id);
CREATE INDEX idx_capsules_operation ON report_capsules(operation_uuid);
CREATE INDEX idx_capsules_zone ON report_capsules(zone_uuid, report_date DESC);
CREATE INDEX idx_capsules_status ON report_capsules(submission_status);
CREATE INDEX idx_capsules_complete ON report_capsules(is_complete);
CREATE INDEX idx_capsules_infoex_uuid ON report_capsules(infoex_uuid) WHERE infoex_uuid IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_capsules_parent_type ON report_capsules(parent_report_uuid, report_type);
CREATE INDEX idx_capsules_type_status ON report_capsules(report_type, submission_status);
CREATE INDEX idx_capsules_date_type ON report_capsules(report_date, report_type);

-- GIN indexes for JSONB
CREATE INDEX idx_capsules_payload ON report_capsules USING GIN (payload);
CREATE INDEX idx_capsules_metadata ON report_capsules USING GIN (metadata);
CREATE INDEX idx_capsules_infoex_response ON report_capsules USING GIN (infoex_response);

-- Array indexes
CREATE INDEX idx_capsules_location_uuids ON report_capsules USING GIN (location_uuids);
CREATE INDEX idx_capsules_tags ON report_capsules USING GIN (tags);

-- Full text search
CREATE INDEX idx_capsules_tsv ON report_capsules USING GIN (data_tsv);

-- Geospatial index
CREATE INDEX idx_capsules_location_gist ON report_capsules USING GIST (location);

-- Vector similarity search (requires pgvector extension)
CREATE INDEX idx_capsules_embedding ON report_capsules USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Index for finding all observations for a daily report
CREATE INDEX idx_capsules_daily_report ON report_capsules(parent_report_uuid, sequence_number);

-- Index for avalanche-specific queries
CREATE INDEX idx_capsules_avalanche_size ON report_capsules(max_avalanche_size, report_date DESC) 
WHERE report_type = 'avalanche_observation' AND max_avalanche_size >= 2;

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Function to generate parent_report_uuid for a new daily report
CREATE OR REPLACE FUNCTION generate_daily_report_uuid(
    p_user_id TEXT,
    p_report_date DATE,
    p_zone_uuid UUID
) RETURNS UUID AS $$
DECLARE
    v_uuid UUID;
BEGIN
    -- Generate deterministic UUID based on user, date, and zone
    v_uuid := uuid_generate_v5(
        uuid_ns_url(), 
        p_user_id || '::' || p_report_date::TEXT || '::' || p_zone_uuid::TEXT
    );
    RETURN v_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to get next sequence number for a report type
CREATE OR REPLACE FUNCTION get_next_sequence_number(
    p_parent_uuid UUID,
    p_report_type VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_max_seq INTEGER;
BEGIN
    SELECT COALESCE(MAX(sequence_number), 0) + 1
    INTO v_max_seq
    FROM report_capsules
    WHERE parent_report_uuid = p_parent_uuid
    AND report_type = p_report_type;
    
    RETURN v_max_seq;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_capsules_updated_at
    BEFORE UPDATE ON report_capsules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Extract avalanche fields trigger
CREATE OR REPLACE FUNCTION extract_avalanche_fields()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.report_type = 'avalanche_observation' THEN
        NEW.max_avalanche_size = (NEW.payload->>'size')::NUMERIC(2,1);
        NEW.trigger_type = NEW.payload->>'trigger';
    ELSIF NEW.report_type = 'hazard_assessment' THEN
        -- Extract hazard ratings from the complex structure
        NEW.hazard_rating_alp = NEW.payload->'hazardRatings'->0->>'rating';
        NEW.hazard_rating_tl = NEW.payload->'hazardRatings'->1->>'rating';
        NEW.hazard_rating_btl = NEW.payload->'hazardRatings'->2->>'rating';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_extract_avalanche_fields
    BEFORE INSERT OR UPDATE OF payload ON report_capsules
    FOR EACH ROW EXECUTE FUNCTION extract_avalanche_fields();

-- Update TSV for full text search
CREATE OR REPLACE FUNCTION update_capsules_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_tsv = to_tsvector('english',
        COALESCE(NEW.zone_name, '') || ' ' ||
        COALESCE(NEW.mountain_range, '') || ' ' ||
        COALESCE(NEW.markdown_content, '') || ' ' ||
        COALESCE(NEW.payload->>'comments', '') || ' ' ||
        COALESCE(NEW.payload->>'summary', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_capsules_tsv
    BEFORE INSERT OR UPDATE ON report_capsules
    FOR EACH ROW EXECUTE FUNCTION update_capsules_tsv();

-- =====================================================
-- VIEWS
-- =====================================================

-- View for complete daily reports
CREATE VIEW daily_reports_summary AS
SELECT 
    parent_report_uuid,
    report_date,
    user_name,
    zone_name,
    COUNT(*) FILTER (WHERE report_type = 'avalanche_observation') as avalanche_count,
    MAX(max_avalanche_size) as max_avalanche_size,
    COUNT(*) FILTER (WHERE submission_status = 'submitted') as submitted_count,
    COUNT(*) FILTER (WHERE submission_status = 'error') as error_count,
    MAX(created_at) as last_updated
FROM report_capsules
GROUP BY parent_report_uuid, report_date, user_name, zone_name;

-- View for avalanche observations with details
CREATE VIEW avalanche_observations_detail AS
SELECT 
    capsule_uuid,
    parent_report_uuid,
    report_date,
    sequence_number,
    zone_name,
    payload->>'trigger' as trigger,
    payload->>'character' as avalanche_type,
    (payload->>'size')::NUMERIC(2,1) as size,
    payload->>'aspectFrom' as aspect_from,
    payload->>'aspectTo' as aspect_to,
    (payload->>'elevationMin')::INTEGER as elevation_min,
    (payload->>'elevationMax')::INTEGER as elevation_max,
    payload->>'comments' as comments,
    submission_status,
    infoex_uuid
FROM report_capsules
WHERE report_type = 'avalanche_observation'
ORDER BY report_date DESC, sequence_number;

-- =====================================================
-- SAMPLE DATA (for testing)
-- =====================================================

-- Insert sample capsule templates
-- Note: In production, these would be loaded from the actual capsule JSON files
INSERT INTO capsule_templates (capsule_type, capsule_structure) VALUES
('initial_data_collection', '{"question": "Let''s start with today''s basic information. What zones did you guide in today, what time did you start and finish, who were the other guides working, and how many guests did you have?", "fields": {}}'::JSONB),
('field_summary', '{"question": "Please provide a comprehensive field summary including: today''s weather (temps, winds, precipitation), snowpack observations, avalanche activity you witnessed, skiing/riding conditions, and any operational concerns or decisions made.", "fields": {}}'::JSONB),
('avalanche_observation', '{"question": "Tell me about the avalanche: What triggered it? What type and size? What aspect and elevation? Any other important details about the avalanche?", "fields": {}}'::JSONB),
('avalanche_summary', '{"question": "Please provide an avalanche summary: Did you observe any avalanches today? If yes, how many and what types/sizes? What percentage of the terrain could you effectively observe for avalanche activity?", "fields": {}}'::JSONB),
('hazard_assessment', '{"question": "What are today''s avalanche hazard ratings by elevation band (alpine, treeline, below treeline)? What are the primary avalanche problems, their distribution, and sensitivity?", "fields": {}}'::JSONB),
('snowpack_summary', '{"question": "Describe the current snowpack structure: What are the main layers? Any persistent weak layers? How is the snow bonding? What are the primary concerns?", "fields": {}}'::JSONB),
('snowProfile_observation', '{"question": "If you dug a snow profile, please describe: Location, elevation, aspect, total depth, layer details, and any test results (CT, ECT, PST).", "fields": {}}'::JSONB),
('terrain_observation', '{"question": "Describe your terrain use today: What ATES ratings did you travel in? What was your strategic mindset (stepping out, status quo, assessment)? Any specific terrain features avoided or utilized?", "fields": {}}'::JSONB),
('pwl_persistent_weak_layer', '{"question": "Are there any persistent weak layers (PWLs) in the snowpack? Describe their characteristics, distribution, and how they''re affecting your operational decisions.", "fields": {}}'::JSONB);

-- =====================================================
-- USEFUL QUERIES
-- =====================================================

-- Get all capsules for a daily report
-- SELECT * FROM report_capsules 
-- WHERE parent_report_uuid = ? 
-- ORDER BY created_at;

-- Get all avalanche observations for a specific day/zone
-- SELECT * FROM avalanche_observations_detail
-- WHERE report_date = ? AND zone_name = ?;

-- Get submission queue (ready to submit)
-- SELECT * FROM report_capsules
-- WHERE is_complete = true 
-- AND submission_status = 'pending'
-- ORDER BY created_at;

-- Get failed submissions for retry
-- SELECT * FROM report_capsules
-- WHERE submission_status = 'error'
-- AND retry_count < 3
-- ORDER BY updated_at;
