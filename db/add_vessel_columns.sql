-- Run once on the HMS database before using the vessel segmentation display.
ALTER TABLE cvd_screenings
    ADD COLUMN vessel_overlay_path VARCHAR(255) NULL,
    ADD COLUMN vessel_density DOUBLE NULL;
