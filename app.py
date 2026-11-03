"""Minimal private browser interface. No API calls on page load."""
import hashlib
import hmac
import os
import threading
import time

import streamlit as st

from web_service import data_directory, read_report, run_pipeline

st.set_page_config(page_title='Garmin AI', page_icon='🏃', layout='centered')


def secret(name):
    value = os.environ.get(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, ''))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return ''


@st.cache_resource
def login_limits():
    return {'failures': [], 'lock': threading.Lock()}


password = secret('APP_PASSWORD')
st.title('Garmin AI')
st.caption('Twoje treningi i regeneracja — w jednym raporcie.')
if len(password) < 20 or password.startswith('REPLACE_'):
    st.error('Aplikacja nie została jeszcze skonfigurowana. W ustawieniach hostingu ustaw silne APP_PASSWORD (co najmniej 20 znaków).')
    st.stop()

password_digest = hashlib.sha256(password.encode('utf-8')).hexdigest()
auth = st.session_state.get('auth', {})
logged_in = (auth.get('digest') == password_digest and auth.get('expires', 0) > time.time())


def attempt_login():
    submitted = st.session_state.pop('login_password', '')
    limits = login_limits()
    now = time.monotonic()
    with limits['lock']:
        limits['failures'] = [stamp for stamp in limits['failures'] if now-stamp < 300]
        if len(limits['failures']) >= 5:
            st.session_state['login_error'] = 'Zbyt wiele prób. Spróbuj ponownie za 5 minut.'
            return
        if hmac.compare_digest(submitted.encode('utf-8'), password.encode('utf-8')):
            st.session_state['auth'] = {'digest': password_digest, 'expires': time.time()+8*3600}
            st.session_state.pop('login_error', None)
            limits['failures'].clear()
        else:
            limits['failures'].append(now)
            st.session_state['login_error'] = 'Nieprawidłowe hasło.'


if not logged_in:
    with st.form('login'):
        st.text_input('Hasło do aplikacji', type='password', key='login_password')
        st.form_submit_button('Zaloguj', on_click=attempt_login)
    if st.session_state.get('login_error'):
        st.error(st.session_state['login_error'])
    st.stop()

if st.button('Wyloguj'):
    st.session_state.clear()
    st.rerun()

credentials = {name: secret(name) for name in ('OPENAI_API_KEY', 'GARMIN_PERSONAL_API_KEY')}
if not all(credentials.values()):
    st.error('Brakuje klucza Garmin lub OpenAI w ustawieniach hostingu.')
    st.stop()

st.caption('Do 50 biegów · 14 dni snu, HRV i Body Battery')
force = st.checkbox('Wymuś nową analizę AI', help='Nowa analiza może naliczyć opłatę API także przy niezmienionych danych.')
try:
    directory = data_directory()
    if st.button('Odśwież i przeanalizuj', type='primary'):
        with st.spinner('Pobieranie danych i przygotowywanie raportu. Może to potrwać kilka minut…'):
            success, message = run_pipeline(directory, credentials, force=force)
        if success:
            st.success(message)
        else:
            st.error(message)
    report, created_at = read_report(directory)
    if report:
        st.subheader('Ostatni raport')
        if created_at:
            st.caption(f'Wygenerowano: {created_at}')
        st.download_button('Pobierz raport', report, file_name='raport_ai.txt', mime='text/plain')
        # Plain text: no HTML, external images, or active links from model output.
        st.text(report)
    else:
        st.info('Brak raportu na tym serwerze. Naciśnij „Odśwież i przeanalizuj”, aby wygenerować pierwszy.')
except Exception:
    st.error('Nie można teraz odczytać lub zapisać raportu. Sprawdź konfigurację miejsca zapisu na serwerze.')

