"""IMD intensity classes from wind (kts). Documented proxy mapping for MVP.

IMD (3-min sustained):
  Depression <28, Deep Depression 28-33, Cyclonic Storm 34-47,
  Severe 48-63, Very Severe 64-89, Extremely Severe 90-119, Super >=120
"""
CLASSES = [
    "Depression",
    "Deep Depression",
    "Cyclonic Storm",
    "Severe Cyclonic Storm",
    "Very Severe Cyclonic Storm",
    "Extremely Severe Cyclonic Storm",
    "Super Cyclonic Storm",
]

def wind_to_class(wind_kts: float) -> str:
    try:
        w = float(wind_kts)
    except (TypeError, ValueError):
        return CLASSES[0]
    if w < 28: return CLASSES[0]
    if w <= 33: return CLASSES[1]
    if w <= 47: return CLASSES[2]
    if w <= 63: return CLASSES[3]
    if w <= 89: return CLASSES[4]
    if w <= 119: return CLASSES[5]
    return CLASSES[6]
