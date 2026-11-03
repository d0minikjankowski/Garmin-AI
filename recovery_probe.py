"""Inspect Garmin recovery response structure locally, without OpenAI."""
import argparse
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import sys

from garmin_personal_api.auth import PersonalApiAuthenticator
from garmin_personal_api.client import GarminPersonalApiClient
from garmin_personal_api.errors import HttpError
from garmin_ai import save


class MemoryAuth(PersonalApiAuthenticator):
    def _read_cached_token(self, fingerprint):
        return None

    def _write_cached_token(self, fingerprint, token):
        pass


def structure(value):
    """Bounded field/type inventory; never print scalar values or identifiers."""
    fields = {}
    def walk(item, path, depth):
        if len(fields) >= 100 or depth > 5:
            return
        fields.setdefault(path, set()).add(type(item).__name__)
        if isinstance(item, dict):
            for key, child in item.items():
                # Only plausible schema names, not arbitrary strings/IDs.
                name = key if isinstance(key, str) and key.isidentifier() and len(key) <= 60 else '<key>'
                walk(child, f'{path}.{name}', depth + 1)
        elif isinstance(item, list):
            for child in item[:14]:
                walk(child, path + '[]', depth + 1)
    walk(value, '$', 0)
    return {key: sorted(types) for key, types in sorted(fields.items())}


def error_summary(error):
    if isinstance(error, HttpError):
        return f'HTTP {error.status_code}'
    return type(error).__name__


def collect(client, start, end, verbose=True):
    emit = print if verbose else lambda *args: None
    results = {}
    sources = [
        ('sleep', client.get_daily_sleep_summaries),
        ('hrv', client.get_daily_hrv_summaries),
        ('body_battery', client.get_daily_body_battery),
    ]
    for name, fetch in sources:
        emit(f'Pobieranie: {name}...')
        try:
            data = fetch(start, end)
            # Empty is a response property, not a diagnosis of device support.
            status = 'empty' if data is None or data == [] or data == {} else 'received'
            results[name] = {'status': status, 'data': data, 'structure': structure(data)}
            emit(f'  Status: {status}; typ odpowiedzi: {type(data).__name__}')
            if isinstance(data, list):
                emit(f'  Elementy listy: {len(data)} (nie musi oznaczać liczby dni z pomiarem)')
            for path, types in results[name]['structure'].items():
                emit(f"  {path}: {', '.join(types)}")
        except Exception as error:
            summary = error_summary(error)
            results[name] = {'status': 'error', 'error': summary}
            print(f'  Błąd: {summary}; pozostałe źródła będą sprawdzone.')
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--end-date', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    end = args.end_date
    start = end - timedelta(days=13)
    key = os.environ.get('GARMIN_PERSONAL_API_KEY', '').strip()
    if not key:
        print('Brak klucza Garmin. Uruchom start_garmin_ai.ps1 -Recovery.')
        return 1
    print(f'Zakres: {start} — {end} (14 dni, dzisiejsze dane mogą być niepełne).')
    print('Tryb rozpoznania danych: bez analizy i bez zapytań do OpenAI.')
    with MemoryAuth(timeout=30) as auth:
        token = auth.obtain_token(key)
        with GarminPersonalApiClient(token.access_token, timeout=30) as client:
            results = collect(client, start, end)
    target = Path(__file__).resolve().parent / 'recovery_data.json'
    save(target, json.dumps({
        'fetched_at': datetime.now().astimezone().isoformat(timespec='seconds'),
        'start_date': start.isoformat(), 'end_date': end.isoformat(),
        'sources': results,
    }, ensure_ascii=False, indent=2, allow_nan=False))
    print(f'Zapisano lokalnie: {target}')
    print('received oznacza odebraną odpowiedź, nie potwierdzenie kompletu pomiarów.')
    print('Do rozmowy wystarczy wynik konsoli; nie trzeba przesyłać całego JSON.')
    return 1 if any(item['status'] == 'error' for item in results.values()) else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('Przerwano.'); sys.exit(130)
    except Exception as error:
        print('Nie udało się zakończyć pobierania: ' + error_summary(error))
        sys.exit(1)
