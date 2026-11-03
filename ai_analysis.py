
import csv
from pathlib import Path
from openai import OpenAI

# Odczyt historii biegowej
csv_path = Path("running_history.csv")

with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file, delimiter=";")
    runs = list(reader)

if not runs:
    raise ValueError("Brak treningów do analizy.")

# Przygotowanie danych dla modelu
training_data = "\n".join(
    ", ".join(f"{key}: {value}" for key, value in run.items())
    for run in runs
)

client = OpenAI()

print("Analizuję historię treningów...\n")

response = client.responses.create(
    model="gpt-5-mini",
    reasoning={"effort": "low"},

instructions=(
    "Jesteś osobistym asystentem treningowym. "
    "Odpowiadasz po polsku, prostym i konkretnym językiem. "

    "PROFIL UŻYTKOWNIKA: "
    "Mężczyzna, 37 lat, 204 cm wzrostu, około 112 kg. "
    "Trenuje regularnie od maja 2026. "
    "Plan tygodniowy: dwa treningi biegowe i dwa siłowe. "
    "Priorytetem jest rozwijanie siły oraz poprawa kondycji. "
    "Cel: ukończenie oficjalnego biegu na 10 km "
    "11 listopada 2026 w czasie netto poniżej 60 minut. "

    "ZASADY ANALIZY: "
    "Tempo_min_km w pliku CSV jest wyrażone w MINUTACH "
    "na kilometr, nie w sekundach. "
    "Nie wymyślaj brakujących danych. "
    "Oddzielaj fakty od hipotez. "
    "Nie porównuj treningów o różnej intensywności "
    "bez wyraźnego zastrzeżenia. "
    "Nie proponuj zwiększania liczby biegów bez uzasadnienia. "
    "Uwzględniaj konieczność regeneracji przed zawodami. "
    "Nie stawiaj diagnoz medycznych. "
    "Jeśli dane są niewystarczające, powiedz o tym."
),

    input=(
        "Przeanalizuj poniższą historię biegania.\n\n"
        f"{training_data}\n\n"
        "Przygotuj:\n"
        "1. Podsumowanie aktywności.\n"
        "2. Ocenę zmian tempa i tętna.\n"
        "3. Możliwe oznaki poprawy kondycji.\n"
        "4. Ograniczenia analizy.\n"
        "5. Trzy praktyczne wskazówki treningowe.\n"
    ),
    max_output_tokens=8000,
)

print("=== ANALIZA AI ===\n")
print("Status:", response.status)
print("Przyczyna przerwania:", response.incomplete_details)
print("Zużycie tokenów:", response.usage)
print("Długość odpowiedzi:", len(response.output_text))
print("\nOdpowiedź modelu:")
print(response.output_text or "BRAK ODPOWIEDZI TEKSTOWEJ")
