-- Create 3857 reprojection column and index
ALTER TABLE deprivation_scores_lsoa
  ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);

UPDATE deprivation_scores_lsoa
SET geom_3857 = ST_Transform(geom,3857)
WHERE geom IS NOT NULL AND geom_3857 IS NULL;

CREATE INDEX IF NOT EXISTS idx_lsoa_geom_3857 ON deprivation_scores_lsoa USING GIST (geom_3857);
ANALYZE deprivation_scores_lsoa;

-- Simplified geometries for zoom tiers (adjust tolerances as needed)
ALTER TABLE deprivation_scores_lsoa
  ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857),
  ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857),
  ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);

-- Initial simplification (kept for new rows). Tolerances adjusted:
-- z0-4: coarse (1000m), z5-7: medium (50m), z8-10: fine (2m)
UPDATE deprivation_scores_lsoa
SET geom_3857_simp_z0_4 = ST_SimplifyPreserveTopology(geom_3857, 1000)
WHERE geom_3857 IS NOT NULL AND geom_3857_simp_z0_4 IS NULL;

UPDATE deprivation_scores_lsoa
SET geom_3857_simp_z5_7 = ST_SimplifyPreserveTopology(geom_3857, 50)
WHERE geom_3857 IS NOT NULL AND geom_3857_simp_z5_7 IS NULL;

UPDATE deprivation_scores_lsoa
SET geom_3857_simp_z8_10 = ST_SimplifyPreserveTopology(geom_3857, 2)
WHERE geom_3857 IS NOT NULL AND geom_3857_simp_z8_10 IS NULL;

-- Recompute (overwrite) existing simplified columns to pick up new tolerances
UPDATE deprivation_scores_lsoa
SET geom_3857_simp_z5_7 = ST_SimplifyPreserveTopology(geom_3857, 50)
WHERE geom_3857 IS NOT NULL;

UPDATE deprivation_scores_lsoa
SET geom_3857_simp_z8_10 = ST_SimplifyPreserveTopology(geom_3857, 2)
WHERE geom_3857 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_lsoa_geom_3857_simp_z0_4 ON deprivation_scores_lsoa USING GIST (geom_3857_simp_z0_4);
CREATE INDEX IF NOT EXISTS idx_lsoa_geom_3857_simp_z5_7 ON deprivation_scores_lsoa USING GIST (geom_3857_simp_z5_7);
CREATE INDEX IF NOT EXISTS idx_lsoa_geom_3857_simp_z8_10 ON deprivation_scores_lsoa USING GIST (geom_3857_simp_z8_10);
ANALYZE deprivation_scores_lsoa;

-- Local Authority 3857 column and index
ALTER TABLE deprivation_scores_localauthority
  ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);

UPDATE deprivation_scores_localauthority
SET geom_3857 = ST_Transform(geom,3857)
WHERE geom IS NOT NULL AND geom_3857 IS NULL;

CREATE INDEX IF NOT EXISTS idx_la_geom_3857 ON deprivation_scores_localauthority USING GIST (geom_3857);
ANALYZE deprivation_scores_localauthority;

-- Views for pg_tileserv: expose minimal attributes
CREATE OR REPLACE VIEW public.lsoa_tiles_z0_4 AS
SELECT
  l.id,
  l.lsoa_code,
  l.year,
  COALESCE(e.imd_decile, 0) AS imd_decile,
  l.geom_3857_simp_z0_4 AS geom
FROM deprivation_scores_lsoa l
LEFT JOIN deprivation_scores_englishindexmultipledeprivation e
  ON e.lsoa_id = l.id AND e.year = l.year
WHERE l.geom_3857_simp_z0_4 IS NOT NULL;

CREATE OR REPLACE VIEW public.lsoa_tiles_z5_7 AS
SELECT
  l.id,
  l.lsoa_code,
  l.year,
  COALESCE(e.imd_decile, 0) AS imd_decile,
  l.geom_3857_simp_z5_7 AS geom
FROM deprivation_scores_lsoa l
LEFT JOIN deprivation_scores_englishindexmultipledeprivation e
  ON e.lsoa_id = l.id AND e.year = l.year
WHERE l.geom_3857_simp_z5_7 IS NOT NULL;

CREATE OR REPLACE VIEW public.lsoa_tiles_z8_10 AS
SELECT
  l.id,
  l.lsoa_code,
  l.year,
  COALESCE(e.imd_decile, 0) AS imd_decile,
  l.geom_3857_simp_z8_10 AS geom
FROM deprivation_scores_lsoa l
LEFT JOIN deprivation_scores_englishindexmultipledeprivation e
  ON e.lsoa_id = l.id AND e.year = l.year
WHERE l.geom_3857_simp_z8_10 IS NOT NULL;

CREATE OR REPLACE VIEW public.la_tiles AS
SELECT
  la.id,
  la.local_authority_district_code,
  la.year,
  la.local_authority_district_name,
  la.geom_3857 AS geom
FROM deprivation_scores_localauthority la
WHERE la.geom_3857 IS NOT NULL;

-- Grant select on views to public (pg_tileserv reads them)
GRANT SELECT ON public.lsoa_tiles_z0_4 TO PUBLIC;
GRANT SELECT ON public.lsoa_tiles_z5_7 TO PUBLIC;
GRANT SELECT ON public.lsoa_tiles_z8_10 TO PUBLIC;
GRANT SELECT ON public.la_tiles TO PUBLIC;
