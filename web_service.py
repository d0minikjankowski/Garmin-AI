"""Server-side execution of the existing single-user pipeline."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def data_directory():
    path = Path(os.environ.get('GARMIN_DATA_DIR', str(ROOT / '.runtime'))).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_report(directory):
    target = directory / 'raport_ai.txt'
    if not target.exists():
        return None, None
    report = target.read_text(encoding='utf-8-sig')
    try:
        state = json.loads((directory / 'analysis_state.json').read_text(encoding='utf-8-sig'))
        timestamp = state.get('created_at') if isinstance(state, dict) else None
    except (OSError, ValueError):
        timestamp = None
    return report, timestamp


def run_pipeline(directory, credentials, force=False):
    # Credentials never appear in command-line arguments or captured log output.
    from filelock import FileLock, Timeout
    try:
        with FileLock(str(directory / 'analysis.lock'), timeout=0):
            env = os.environ.copy()
            for name in ('OPENAI_API_KEY', 'GARMIN_PERSONAL_API_KEY'):
                env[name] = credentials[name]
            env['GARMIN_DATA_DIR'] = str(directory)
            env['PYTHONIOENCODING'] = 'utf-8'
            env['TZ'] = 'Europe/Warsaw'
            args = [sys.executable, str(ROOT / 'garmin_ai.py')]
            if force:
                args.append('--force')
            result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=600)
            if result.returncode:
                return False, 'Nie udało się zakończyć analizy. Sprawdź klucze, dostęp do API i połączenie. Poprzedni raport pozostaje dostępny.'
            if 'pominięto analizę OpenAI' in result.stdout:
                return True, 'Dane bez zmian. Zachowano poprzedni raport bez nowego zapytania do AI.'
            return True, 'Dane odświeżone. Nowy raport jest gotowy.'
    except Timeout:
        return False, 'Analiza już trwa. Poczekaj na jej zakończenie i odśwież stronę.'
    except subprocess.TimeoutExpired:
        return False, 'Przekroczono czas oczekiwania. Spróbuj ponownie później.'

