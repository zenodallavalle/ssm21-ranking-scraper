import json
import os
import grabber_v3
import pandas as pd

WORKERS = None
SHEET_NAME = 'first-round'


def scrape(save=True, verbose=True, detect_min_pts=False, workers=WORKERS, sheet_name=SHEET_NAME):
    # If save == False will return ranking as pd.DataFrame
    write_link = False
    if not 'credentials.json' in os.listdir():
        raise FileNotFoundError('credentials.json must be in this folder.')
    with open('credentials.json', 'r') as f:
        cred = json.load(f)
        email = cred.get('email', None)
        if email is None:
            raise KeyError('email must be present')
        password = cred.get('password', None)
        if password is None:
            raise KeyError('password must be present')
        authentication_link = cred.get('authentication_link', None)
        if authentication_link is None:
            print('Authentication_link was not found. For this time we will login with email and password, then we will retrieve authentication link and save it in credentials.json for next times. Using authentication_link can save ~5 seconds.')
            print(
                'Authentication link is strictly personal, don\'t share it with anyone!')
            write_link = True
            authentication_link = grabber_v3.get_authentication_link(
                email, password)
    if write_link:
        with open('credentials.json', 'w') as f:
            json.dump({
                'email': email,
                'password': password,
                'authentication_link': authentication_link
            }, f)
        print('authentication_link written in credentials.json')
    if verbose:
        print('Starting process')
    ranking = grabber_v3.grab(email, password, authentication_link, workers)
    if verbose:
        print('Done, downloaded', len(ranking), 'entries.')
        print('Displaying the first 5 and the last 5 entries.')
        print(ranking.head())
        print(ranking.tail())
    if detect_min_pts:
        min_pts = ranking[ranking['Specializzazione'].astype(bool)].groupby(['Specializzazione', 'Sede', 'Contratto'], as_index=False, ).min()[
            ['Specializzazione', 'Sede', 'Contratto', '#', 'Tot']]
    if save:
        kwargs = {}
        if 'graduatoria_2021.xlsx' in os.listdir():
            kwargs['mode'] = 'a'
            kwargs['if_sheet_exists'] = 'replace'
        with pd.ExcelWriter('graduatoria_2021.xlsx', **kwargs) as writer:
            ranking.to_excel(writer, index=False,
                             sheet_name=sheet_name, float_format='%.2f')
        if detect_min_pts:
            kwargs = {}
            if 'min_pts_2021.xlsx' in os.listdir():
                kwargs['mode'] = 'a'
                kwargs['if_sheet_exists'] = 'replace'
            with pd.ExcelWriter('min_pts_2021.xlsx') as writer:
                min_pts.to_excel(writer, index=False,
                                 sheet_name=f'{sheet_name}', float_format='%.2f')

        if verbose:
            print('Saved.')
    else:
        if detect_min_pts:
            return ranking, min_pts
        else:
            return ranking


if __name__ == '__main__':
    scrape()
