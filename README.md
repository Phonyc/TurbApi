# TurbApi

Client fonctionnant pour 1 réservation (midi) par jour.

```Python
client = TurbApi('username@username.com', 'password')
```
Format de date : `jjmmyyyy`

## Méthodes
### client.get_etat_dates(dates: list[str])
Retourne sous forme d'un dictionaire les états aux dates spécifiées.

Retour : 
```python
{
    "jjmmyyy": {"borneId": "1234", "weekNumber": "12", "Reserved": False}
}
```
Si la date est passée ou n'est pas affichée, elle ne sera pas dans le dictionnaire retourné.

### client.deresa_dates(dates: list[str])
Déréserve pour les dates spécifiées.

### client.resa_dates(dates: list[str])
Réserve pour les dates spécifiées.

### client.get_operations() -> list[list]
Retourne sous une forme de liste de listes l'équivalent du tableau "dernières opérations"

### client.get_solde() -> tuple[float, str]

Retourn le solde courant sous forme d'un tuple (solde, devise)

Exemple : `(100, '€')`
