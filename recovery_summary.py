"""Local recovery summary; no API requests and no clinical interpretation."""
import argparse
from datetime import date, timedelta
import json
import math
from pathlib import Path
from statistics import mean


def number(value, low=0, high=math.inf):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and low <= value <= high else None


def records(source, name):
    entry = source.get(name, {})
    data = entry.get('data') if entry.get('status') == 'received' else None
    if name == 'hrv' and isinstance(data, dict):
        data = data.get('hrvSummaries')
    return data if isinstance(data, list) else []


def indexed(items, field):
    result = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get(field), str):
            continue
        key = date.fromisoformat(item[field]).isoformat()
        if key in result:
            raise ValueError('Powtórzona data w jednym źródle; wymaga sprawdzenia.')
        result[key] = item
    return result


def battery(item):
    descriptors = item.get('bodyBatteryValueDescriptorDTOList') or []
    mapping = {d.get('bodyBatteryValueDescriptorKey'): d.get('bodyBatteryValueDescriptorIndex')
               for d in descriptors if isinstance(d, dict)}
    ti, vi = mapping.get('timestamp'), mapping.get('bodyBatteryLevel')
    if any(type(i) is not int or i < 0 for i in (ti, vi)):
        return None, None, None, 0
    samples = []
    for row in item.get('bodyBatteryValuesArray') or []:
        if not isinstance(row, list) or len(row) <= max(ti, vi):
            continue
        stamp, value = number(row[ti]), number(row[vi], 0, 100)
        if stamp is not None and value is not None:
            samples.append((stamp, value))
    if not samples:
        return None, None, None, 0
    samples.sort()
    values = [v for _, v in samples]
    return min(values), max(values), samples[-1][1], len(samples)


def summarize(document):
    start, end = (date.fromisoformat(document[k]) for k in ('start_date', 'end_date'))
    if not 0 <= (end-start).days <= 366:
        raise ValueError('Nieprawidłowy zakres dat.')
    sources = document['sources']
    sleep = indexed(records(sources, 'sleep'), 'calendarDate')
    hrv = indexed(records(sources, 'hrv'), 'calendarDate')
    bb = indexed(records(sources, 'body_battery'), 'date')
    days = []
    for offset in range((end-start).days+1):
        day = (start+timedelta(days=offset)).isoformat()
        s, h, b = sleep.get(day, {}), hrv.get(day, {}), bb.get(day, {})
        scores = s.get('sleepScores') or {}
        overall = scores.get('overall') or {}
        low, high, last, count = battery(b)
        days.append({
            'date': day,
            'sleep_seconds': number(s.get('sleepTimeSeconds'), 0, 86400),
            'sleep_score': number(overall.get('value'), 0, 100),
            'hrv_night': number(h.get('lastNightAvg'), 0),
            'hrv_weekly': number(h.get('weeklyAvg'), 0),
            'hrv_status_garmin': h.get('status'),
            'body_battery_min': low, 'body_battery_max': high,
            'body_battery_last': last, 'body_battery_samples': count,
        })
    return days


def display(value):
    if value is None:
        return 'brak'
    return f'{value:g}' if isinstance(value, (int, float)) else str(value)


def duration(seconds):
    if seconds is None:
        return 'brak'
    minutes = math.floor(seconds/60 + .5)
    return f'{minutes//60}h {minutes%60:02d}m'


def report(document, days):
    lines = [
        f"REGENERACJA: {document['start_date']} — {document['end_date']}",
        f"Dane pobrane: {document.get('fetched_at', 'brak')}",
        'Zestawienie pomiarów Garmin, bez oceny medycznej.',
        'Ostatni dzień zakresu może być niepełny. Braki nie są zastępowane zerem.',
        'HRV: pola lastNightAvg / weeklyAvg; status przepisany z Garmin.',
        'BB: minimum / maksimum z otrzymanych próbek / ostatni dostępny pomiar (niekoniecznie wieczorny).',
        'Próbki BB nie muszą obejmować wszystkich pomiarów dnia ani rzeczywistych dziennych ekstremów.',
        '', 'Data | Sen | Ocena snu | HRV noc / tydzień | Status HRV | BB min / max / ostatni | Próbek BB',
    ]
    for row in days:
        lines.append(' | '.join([
            row['date'], duration(row['sleep_seconds']), display(row['sleep_score']),
            f"{display(row['hrv_night'])} / {display(row['hrv_weekly'])}",
            display(row['hrv_status_garmin']),
            ' / '.join(display(row[k]) for k in ('body_battery_min','body_battery_max','body_battery_last')),
            str(row['body_battery_samples']),
        ]))
    lines += ['', 'Dostępność i średnie z dostępnych pomiarów (bez uzupełniania braków):']
    for key, label in [('sleep_seconds','Czas snu'),('sleep_score','Ocena snu'),('hrv_night','HRV nocne')]:
        values = [r[key] for r in days if r[key] is not None]
        avg = mean(values) if values else None
        formatted = duration(avg) if key == 'sleep_seconds' else display(round(avg,1) if avg is not None else None)
        lines.append(f'{label}: {len(values)}/{len(days)} dni; średnia: {formatted}')
    for name, entry in document['sources'].items():
        if entry.get('status') != 'received':
            lines.append(f"Źródło {name}: {entry.get('status', 'brak statusu')}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path(__file__).with_name('recovery_data.json'))
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('recovery_summary.txt'))
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding='utf-8-sig'))
    text = report(document, summarize(document))
    temp = args.output.with_suffix('.tmp')
    temp.write_text(text, encoding='utf-8-sig')
    temp.replace(args.output)
    print(text)
    print(f'\nZapisano: {args.output}')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Nie udało się przygotować zestawienia. Typ błędu: ' + type(error).__name__)
        raise SystemExit(1)
