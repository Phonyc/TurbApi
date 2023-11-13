import requests
from bs4 import BeautifulSoup


class TurboCache:
    def __init__(self):
        self.etats = {}
        self.hoteid = ''

    def set_etats(self, dct_etats):
        for date, v in dct_etats.items():
            self.etats[date] = {}
            self.etats[date]['borneId'] = v['borneId']
            self.etats[date]['weekNumber'] = v['weekNumber']


class TurbApi:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.cache = TurboCache()

        self.connexion_infos = {
            '__LASTFOCUS': '',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            '__VIEWSTATEGENERATOR': '',
            '__EVENTVALIDATION': '',
            'ctl00$cntForm$txtLogin': self.username,
            'ctl00$cntForm$txtMotDePasse': self.password,
            'ctl00$cntForm$ssoUser': '',
            'ctl00$cntForm$btnConnexion': 'Connexion'
        }
        self.update_infos_connexion()
        self.session = requests.Session()
        if not self._login():
            raise Exception('Login ou Mot de Passe Incorrect')

    def update_infos_connexion(self):
        req = requests.get('https://espacenumerique.turbo-self.com/Connexion.aspx')
        page_bs4 = BeautifulSoup(req.text, 'html.parser')
        self.connexion_infos['__VIEWSTATE'] = page_bs4.find('input', {'id': '__VIEWSTATE'}).get('value')
        self.connexion_infos['__VIEWSTATEGENERATOR'] = page_bs4.find('input', {'id': '__VIEWSTATEGENERATOR'}).get(
            'value')
        self.connexion_infos['__EVENTVALIDATION'] = page_bs4.find('input', {'id': '__EVENTVALIDATION'}).get('value')

    def _login(self):
        post_req = self.session.post('https://espacenumerique.turbo-self.com/Connexion.aspx', data=self.connexion_infos)
        return 'mot de passe incorrect' not in post_req.text

    def get_etat_dates(self, dates: list[str]) -> dict:
        """
        Retourne les états de la réservation aux jours spécifiés.
        """
        out = {}
        req_resa = self.session.get('https://espacenumerique.turbo-self.com/ReserverRepas.aspx')
        page_bs4 = BeautifulSoup(req_resa.text, 'html.parser')
        if self.cache.hoteid == '':
            self.cache.hoteid = page_bs4.find('input', id='ctl00_cntForm_hote_id').get('value')
        for date in dates:
            try:
                out[date] = {}
                out[date]['borneId'] = page_bs4.find('input', id=date).parent.parent.find('input', {'name': 'borne'}).get(
                    'value')
                out[date]['weekNumber'] = page_bs4.find('input', id=date).parent.parent.parent.parent.get('value')
                out[date]['Reserved'] = int(
                    page_bs4.find('input', id=date).parent.parent.find('input', {'name': 'nbRsv'}).get('value')) > 0
            except AttributeError:
                del out[date]
                # Le jour existe pas

        self.cache.set_etats(out)
        return out

    def deresa_dates(self, dates: list[str]):
        """
        Pour déréserver à certaines dates
        """
        to_get_etats = []
        for date in dates:
            if date in self.cache.etats:
                print('Déréservation : ', date)
                json_send = {"param": {"hoteId": self.cache.hoteid, "week": self.cache.etats[date]['weekNumber'],
                                       "day": date, "usage": "3"}}
                self.session.post('https://espacenumerique.turbo-self.com/ServiceReservation.asmx/ClearReservation',
                                  json=json_send)
            else:
                to_get_etats.append(date)

        if to_get_etats:
            self.get_etat_dates(to_get_etats)
            self.deresa_dates(to_get_etats)

    def resa_dates(self, dates: list[str]):
        """
        Pour Réserver à certaines dates
        """
        to_get_etats = []
        for date in dates:
            if date in self.cache.etats:
                print('Réservation : ', date)
                json_send = {"param": {"action": "plus", "hoteId": self.cache.hoteid, "day": date,
                                       "week": self.cache.etats[date]['weekNumber'],
                                       "borneId": self.cache.etats[date]['borneId'], "usage": "3"}}

                self.session.post('https://espacenumerique.turbo-self.com/ServiceReservation.asmx/AddReservation',
                                  json=json_send)
            else:
                to_get_etats.append(date)

        if to_get_etats:
            self.get_etat_dates(to_get_etats)
            self.resa_dates(to_get_etats)

    def get_operations(self) -> list[list]:
        """
        Pour obtenir les dèrnières opérations
        """
        req = self.session.get('https://espacenumerique.turbo-self.com/Accueil.aspx')
        page_bs4 = BeautifulSoup(req.text, 'html.parser')
        table = page_bs4.find('table', id="ctl00_cntForm_gdvHistorique")
        out = []
        for row in table.find_all("tr")[1:]:
            col = row.find_all("td")
            out.append([col[0].contents[0].replace('\xa0', ' '),
                        col[1].contents[0],
                        col[1].span.contents[0]])
        return out

    def get_solde(self) -> tuple[float, str]:
        """
            Pour obtenir le solde courant
            :return: tuple[solde, devise]
        """
        req = self.session.get('https://espacenumerique.turbo-self.com/CrediterCompte.aspx')
        page_bs4 = BeautifulSoup(req.text, 'html.parser')
        txt = str(page_bs4.find('div', id="divModeArgent").div.find('span', {'class': 'prix'}).contents[0].strip())
        return float(txt[:-1].replace(',', '.')), txt[-1:],
