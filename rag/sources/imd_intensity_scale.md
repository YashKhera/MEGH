# IMD intensity scale (3-min sustained winds)
Title: IMD tropical cyclone intensity scale
Source: India Meteorological Department (IMD)
URL: https://mausam.imd.gov.in/
Date: 2024-01-01
Topic: intensity-classification
Basin: North Indian Ocean

IMD classifies North Indian Ocean systems by 3-minute sustained wind speed:
- Depression: below 28 kt (below 52 km/h)
- Deep Depression: 28-33 kt (52-61 km/h)
- Cyclonic Storm: 34-47 kt (62-88 km/h)
- Severe Cyclonic Storm: 48-63 kt (89-117 km/h)
- Very Severe Cyclonic Storm: 64-89 kt (118-165 km/h)
- Extremely Severe Cyclonic Storm: 90-119 kt (166-220 km/h)
- Super Cyclonic Storm: 120 kt and above (221 km/h and above)

MEGH's derived_class follows these IMD wind thresholds exactly, so a MEGH
intensity label can always be checked against the estimated wind value in knots.
A higher class means stronger sustained winds and, generally, higher damage potential,
but official warnings come only from IMD — MEGH is a research prototype.
