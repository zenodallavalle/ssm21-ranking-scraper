from datetime import datetime as dt
from multiprocessing import Pool, cpu_count
from itertools import repeat
from requests import Session

import pandas as pd
from bs4 import BeautifulSoup as BS


BASE_URL = 'https://www.universitaly.it/'

COLUMNS = ['#', 'cognome_nome', 'Tot', 'Prova', 'Titoli', 'Stato', 'Note']


def get_authentication_link(email, password):
    '''
    This function get the authentication link to access the private page at ssm.cineca.it
    Authentication link is strictly related to your account, don't share it.
    '''
    s = Session()
    r = s.get('https://www.universitaly.it/index.php/login')
    assert r.status_code == 200
    bs = BS(r.content, 'lxml')
    login_form = {}
    form_tag = bs.find(lambda tag: tag.name ==
                       'form' and 'login' in tag.attrs['id'])
    form_url = form_tag.attrs['action']
    for element in form_tag.find_all('input'):
        if element.attrs['type'] != 'submit':
            name = element.attrs['name']
            if 'email' in name:
                value = email
            elif 'password' in name:
                value = password
            else:
                value = element.attrs['value']
            login_form[name] = value
    r = s.post(BASE_URL + form_url, login_form)
    assert r.status_code == 200
    r = s.get(BASE_URL + 'index.php/dashboard-ssm')
    assert r.status_code == 200
    bs = BS(r.content, 'lxml')
    authentication_link = bs.find(
        lambda tag: tag.name == 'a' and 'href' in tag.attrs and 'ssm.cineca.it/autenticazione' in tag.attrs['href']).attrs['href']
    return authentication_link


def authenticate(email, password, authentication_link=None, session=None):
    '''
    Authenticate the session to ssm.cineca.it in order to access the ranking.
    If authentication link is provided it's ~5s faster.
    '''
    auth_link = authentication_link
    if auth_link is None:
        auth_link = get_authentication_link(email, password)
        print('Using authentication_link next time, can save ~5 seconds. You can get it with get_authentication_link function.')
    s = session or Session()
    r = s.get(auth_link)
    assert r.status_code == 200
    return s


def gen_url_paged(n):
    # Generate the url for every page of the ranking
    BASE = 'https://ssm.cineca.it/ssm21_graduatoria.php?user=MEMDLLZNE96D25L781A_21&year_ssm=2021'
    return BASE + f'&page={n}'


def detect_limit(s):
    r = s.get(gen_url_paged(1))
    assert r.status_code == 200
    bs = BS(r.content, 'lxml')
    select = bs.find('select', {'id': 'selPag'})
    return max([int(e.text.strip()) for e in select.find_all('option')])


def prepare_data(tds):
    '''
    Parse data for every row in the page.
    Return a dictionary containing columns as keys and values scraped from the page.
    '''
    row = {}
    for i, c in enumerate(COLUMNS):
        if i < 5:
            try:
                row[c] = float(tds[i].text.replace(',', '.'))
            except ValueError:
                row[c] = tds[i].text.strip() if i != 1 else list(
                    tds[i].children)[2].strip()
        elif i == 5:
            span = tds[i].find('span')
            value = span.attrs.get('title', None)
            if not value:
                value = span.text.strip()
            row[c] = value
        elif i == 6:
            span = tds[i].find('span')
            if span:
                children = list(span.children)
                row[c] = children[0].strip()
                row['Contratto'] = children[1].text.strip().upper()
            else:
                row[c] = tds[i].text.strip()
        else:
            row[c] = tds[i].text.strip()
    return row


def scan_page(session, n, request_status_callback=lambda r: r.status_code, empty_page_callback=lambda: None):
    '''
    Parse the page number (n)
    request_status_callback (optional) function called when request's status_code != 200; passed args = [request]
    empty_page_callback (optional) function called when there are no elements to analyze in page; passed args = []
    If the page is parsed correctly a pd.DataFrame instance containing the elements in the page is returned.
    '''
    r = (session.get(gen_url_paged(n)))
    if r.status_code != 200:
        return request_status_callback(r)
    bs = BS(r.content, 'lxml')
    trs = bs.find_all('tr')
    rows = []
    if len(trs) < 2:
        return empty_page_callback()
    for tr in trs:
        tds = tr.findChildren('td')
        if len(tds) > 0:
            rows.append(prepare_data(tds))
    return pd.DataFrame(rows)


def grab(email, password=None, authentication_link=None, workers=None):
    # Number of _workers is equal to passed argument workers or if None is equal to cpu_count()
    _workers = workers or cpu_count()
    # Get a session authenticated to access the ranking
    s = authenticate(email, password, authentication_link)
    # detect limit
    upper_limit = detect_limit(s)

    with Pool(_workers) as p:
        dfs = p.starmap(scan_page, zip(repeat(s), range(1, upper_limit + 1)))
        df = pd.concat([df for df in dfs if isinstance(df, pd.DataFrame)])

    # generate column birth from date within parenthesis
    df['nascita'] = df['cognome_nome'].map(lambda x: dt.strptime(
        x.rsplit('(', 1)[-1].replace(')', '').strip(), '%d/%m/%Y'))
    df['cognome_nome'] = df['cognome_nome'].map(
        lambda x: x.rsplit('(', 1)[0].strip())
    df['Note'] = df['Note'].astype(str)

    df['#'] = df['#'].astype(int)
    df.sort_values(by=['#'], inplace=True)

    df.reset_index(drop=True, inplace=True)
    # reorder columns
    cols = list(df.columns)
    popped = cols.pop()
    cols.insert(2, popped)
    df = df[cols].copy()
    df['Specializzazione'] = df['Note'].map(
        lambda x: x.rsplit(',', 1)[0].strip() if x else '')
    df['Sede'] = df['Note'].map(lambda x: x.rsplit(',', 1)[
                                1].strip() if x else '')
    # rename index col "index"
    df.rename_axis(['index'], axis=1, inplace=True)
    return df
