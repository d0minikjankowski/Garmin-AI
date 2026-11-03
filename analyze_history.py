import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Wczytanie historii aktywności
path = Path("activities_history.json")

with path.open("r", encoding="utf-8-sig") as file:
    activities = json.load(file)

# Filtrujemy tylko bieganie
runs = [
    activity for activity in activities
    if activity.get("activityType", {}).get("typeKey") == "running"
]

# Grupujemy kilometraż według tygodni kalendarzowych
weekly_distance = defaultdict(float)

print("\n=== GARMIN AI - HISTORIA BIEGANIA ===\n")

for run in runs:
    date = datetime.strptime(
        run["startTimeLocal"], "%Y-%m-%d %H:%M:%S"
    )

    distance_km = run["distance"] / 1000
    duration = run["duration"]
    pace = duration / distance_km

    pace_minutes, pace_seconds = divmod(round(pace), 60)
    year, week, _ = date.isocalendar()

    weekly_distance[(year, week)] += distance_km

    print(
        f"{date:%Y-%m-%d} | "
        f"{distance_km:.2f} km | "
        f"{pace_minutes}:{pace_seconds:02d} min/km | "
        f"HR: {run.get('averageHR', 'brak')} bpm"
    )

print("\n=== PODSUMOWANIE ===")

total_distance = sum(
    run["distance"] for run in runs
) / 1000

print(f"Liczba biegów: {len(runs)}")
print(f"Łączny dystans: {total_distance:.2f} km")

print("\nKilometraż tygodniowy:")

for (year, week), distance in sorted(weekly_distance.items()):
    print(f"{year}, tydzień {week}: {distance:.2f} km")


# Eksport treningów do CSV
with open("running_history.csv", "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.writer(file, delimiter=";")

    writer.writerow([
        "Data",
        "Dystans_km",
        "Czas_min",
        "Tempo_min_km",
        "Srednie_HR",
        "Training_Effect"
    ])

    for run in runs:
        distance_km = run["distance"] / 1000
        duration_min = run["duration"] / 60
        pace_min_km = (run["duration"] / 60) / distance_km

        writer.writerow([
            run["startTimeLocal"],
            round(distance_km, 2),
            round(duration_min, 2),
            round(pace_min_km, 2),
            run.get("averageHR"),
            round(run.get("aerobicTrainingEffect") or 0, 1)
        ])

print("\nZapisano running_history.csv")

