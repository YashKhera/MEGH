# Satellite cloud structure and intensity cues
Title: Satellite observation cues for cyclone intensity
Source: NOAA / WMO tropical cyclone guidance (curated extract)
URL: https://www.noaa.gov/jetstream/ocean/tropical-cyclone-introduction
Date: 2024-01-01
Topic: satellite-interpretation
Basin: global

Infrared satellite imagery shows cloud-top temperature: colder (brighter) cloud tops
indicate deeper convection. Organized tropical cyclones develop a central dense
overcast, curved banding features, and — in intense storms — a warm, cloud-free eye.

The Dvorak technique is the classical method relating satellite cloud patterns to
intensity: more symmetric cold cloud tops with a distinct eye correspond to higher
wind speeds. Automated vision models such as MEGH's learn similar statistical
regularities (bright symmetric core, cold ring structure) from historical frames,
but they are pattern estimators, not physical measurements.

Limitations: different sensors and channels render cloud structure differently;
a model trained on one satellite source may misread another without recalibration.
