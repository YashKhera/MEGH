# IBTrACS best-track provenance
Title: IBTrACS best-track dataset documentation
Source: NOAA NCEI IBTrACS
URL: https://www.ncei.noaa.gov/products/international-best-track-archive
Date: 2024-01-01
Topic: data-provenance
Basin: global (MEGH uses North Indian Ocean subset)

IBTrACS (International Best Track Archive for Climate Stewardship) merges
post-season reanalysed tropical cyclone tracks from meteorological agencies
worldwide into one archive: position, time, sustained wind, central pressure,
and agency-specific fields per 6-hourly fix.

MEGH uses IBTrACS as ground truth for storm position, wind, and historical track:
storm_id (SID), timestamp (ISO_TIME), latitude, longitude, wind (preferring the
New Delhi/IMD field, then USA/WMO fields), and pressure. Labels carry historical
and reanalysis uncertainty; they are the best available record, not perfect truth.

For India-focused analysis MEGH filters BASIN=NI (North Indian Ocean) and keeps
the most recent storms for a tractable MVP.
