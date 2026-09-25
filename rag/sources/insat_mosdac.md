# INSAT-3D / MOSDAC satellite context
Title: INSAT-3D meteorological satellite (MOSDAC) context
Source: ISRO MOSDAC
URL: https://www.mosdac.gov.in/
Date: 2024-01-01
Topic: satellite-source
Basin: North Indian Ocean

INSAT-3D is ISRO's meteorological satellite carrying a 6-channel imager
(visible and infrared) and a 19-channel sounder. Data is distributed through
MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre).

Day-1 note: MEGH trains on deterministic synthetic proxy frames (SYN_PROXY,
IR_PROXY channel) standing in for storm-centred satellite archives such as
HURSAT, until INSAT-3D/MOSDAC or HURSAT ingest lands. The pipeline records
satellite_source per observation so any frame's provenance is always visible,
and sensor/domain shift is listed as a limitation in the model card.
