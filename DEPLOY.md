# Garmin AI — uruchomienie przez przeglądarkę

Ta wersja dodaje wyłącznie dostęp przez przeglądarkę do istniejącej analizy. Aplikacja jest przeznaczona dla jednej osoby. Dane Garmin i klucze pozostają po stronie serwera; podsumowania są wysyłane do OpenAI po naciśnięciu przycisku analizy.

## 1. Pliki w repozytorium

Do repozytorium `d0minikjankowski/Garmin-AI` dodaj pliki z tej paczki, zachowując strukturę katalogów. Istniejące skrypty PowerShell mogą pozostać w repozytorium. Nie dodawaj swoich lokalnych raportów, pliku kluczy ani danych Garmin.

- `app.py`, `web_service.py`
- `garmin_ai.py`, `recovery_probe.py`, `recovery_summary.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `.gitignore`

Wersja chmurowa używa strefy `Europe/Warsaw` niezależnie od lokalizacji serwera. Analiza i zasady przeliczania danych pozostały takie same.

## 2. Wdrożenie w Streamlit Community Cloud

1. Otwórz https://share.streamlit.io/ i zaloguj się własnym kontem.
2. Połącz GitHub i udziel dostępu do wybranego repozytorium.
3. Wybierz **Create app**, repozytorium `d0minikjankowski/Garmin-AI`, właściwą gałąź i plik `app.py`.
4. W ustawieniach zaawansowanych wybierz Python 3.12 i dodaj sekrety według przykładu poniżej. Wpisuj je bezpośrednio w panelu hostingu, nigdy w repozytorium ani w rozmowie.
5. Wdróż aplikację i ustaw prywatny dostęp wyłącznie dla siebie. Nie publikuj danych jako aplikacji publicznej. Oprócz bramki hostingu aplikacja wymaga własnego hasła.
6. Otwórz otrzymany adres HTTPS na telefonie i wpisz hasło aplikacji. Laptop nie musi być włączony.

Przykładowa struktura sekretów — zastąp wartości w panelu hostingu:

```toml
APP_PASSWORD = "REPLACE_WITH_RANDOM_PASSWORD_AT_LEAST_20_CHARACTERS"
GARMIN_PERSONAL_API_KEY = "REPLACE_WITH_GARMIN_KEY"
OPENAI_API_KEY = "REPLACE_WITH_OPENAI_KEY"
```

Użyj osobnego, losowego hasła aplikacji. Nie używaj hasła do konta Garmin lub GitHub. Zaszyfrowany plik Windows `.secrets.clixml` nie działa na serwerze Linux i nie jest przenoszony.

## 3. Kontrola po wdrożeniu

- Przed zalogowaniem nie mogą być widoczne raporty ani przycisk analizy.
- Brak lub zbyt krótkie hasło blokuje aplikację.
- Pierwsze kliknięcie pobiera dane i wykonuje analizę.
- Drugie kliknięcie przy niezmienionych danych powinno pominąć OpenAI.
- Wymuszenie analizy wykonuje nowe zapytanie.
- Wylogowanie ponownie ukrywa raport.
- Wejście na stronę samo w sobie nie wywołuje API.

## Przechowywanie raportów

Domyślnie raporty i pamięć analiz znajdują się w `.runtime/` na serwerze. Nie trafiają na GitHub. Nie należy traktować dysku Streamlit Community Cloud jako trwałej bazy: restart, ponowne wdrożenie lub odtworzenie środowiska może usunąć te pliki. Wtedy kolejna analiza wygeneruje raport ponownie i może ponownie naliczyć koszt OpenAI. Gotowy raport można pobrać przyciskiem.

Jeżeli zachowanie raportów i pamięci analiz między odtworzeniami środowiska jest wymagane, użyj hostingu Python z trwałym dyskiem i ustaw `GARMIN_DATA_DIR` na katalog tego dysku. Start: `python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501`. Nie uruchamiaj wielu replik współdzielących te pliki bez dodatkowej koordynacji; ta wersja jest przeznaczona na jeden serwer.

## Zakres sprawdzenia

Logika połączenia z istniejącym programem, przekazywania kluczy, blokady równoległej analizy i odczytu raportów może być testowana bez sieci. Pełny test interfejsu, instalacji zależności na Linuxie i połączeń z Garmin/OpenAI wymaga uruchomienia aplikacji z dostępnymi bibliotekami i sekretami. Nie uznawaj przygotowanej paczki za potwierdzone wdrożenie.

Dokumentacja hostingu: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
