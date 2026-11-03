
import json
from pathlib import Path

# Odczyt zapisanych danych
file_path = Path("activity_latest.json")

with file_path.open("r", encoding="utf-16") as file:
    activities = json.load(file)

activity = activities[0]

# Pobranie podstawowych wartości
name = activity["activityName"]
distance_km = activity["distance"] / 1000
duration_seconds = activity["duration"]
average_hr = activity.get("averageHR")
max_hr = activity.get("maxHR")

# Przeliczenie czasu i tempa
minutes, seconds = divmod(round(duration_seconds), 60)
pace_seconds = duration_seconds / distance_km
pace_minutes, pace_remainder = divmod(round(pace_seconds), 60)

# Wyświetlenie raportu
print("\n=== GARMIN AI - RAPORT TRENINGOWY ===")
print(f"Aktywność: {name}")
print(f"Dystans: {distance_km:.2f} km")
print(f"Czas: {minutes:02d}:{seconds:02d}")
print(f"Średnie tempo: {pace_minutes}:{pace_remainder:02d} min/km")
print(f"Średnie tętno: {average_hr} bpm")
print(f"Maksymalne tętno: {max_hr} bpm")
print(f"Training Effect: {activity['aerobicTrainingEffect']:.1f}")
print("===================================\n")
