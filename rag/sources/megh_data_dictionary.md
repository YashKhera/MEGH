# MEGH data dictionary (condensed for retrieval)
Title: MEGH data dictionary
Source: Team Vittvanni (MEGH project)
URL: local:data/metadata/dataset.csv
Date: 2026-09-25
Topic: data-provenance
Basin: North Indian Ocean

Each dataset.csv row is one 6-hourly storm fix aligned to IBTrACS:
storm_id (IBTrACS SID), storm_name, basin, timestamp (UTC ISO), satellite_source
(SYN_PROXY until real ingest), image_path (proxy PNG), channels (IR_PROXY),
latitude, longitude, wind_kts (New Delhi > USA > WMO preference), pressure_hpa,
agency_status, derived_class (IMD scale from wind), split (train/val/test by
whole storm — test storms are unseen).

Track supervision needs triples of consecutive fixes: displacement from the
previous fix predicts displacement to the next fix. Persistence baseline repeats
the last displacement. Errors are great-circle kilometres.
