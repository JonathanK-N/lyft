# Church Lyft - Nouvelle Architecture

## Structure du Projet

```
lyft-church/
│── .env                    # Variables d'environnement
│── requirements.txt        # Dépendances Python
│── wsgi.py                # Point d'entrée WSGI
│── manage.py              # Commandes CLI
│── migrate_data.py        # Script de migration des données
│── seed.py                # Script de peuplement de la base
│
├── app/
│   ├── __init__.py        # Factory Flask
│   ├── config.py          # Configuration
│   ├── extensions.py      # Extensions Flask
│   │
│   ├── models/            # Modèles de données
│   │   ├── __init__.py
│   │   ├── user.py        # Modèle Member
│   │   ├── ride.py        # Modèle Ride
│   │   └── location.py    # Modèle Location
│   │
│   ├── routes/            # Routes/Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py        # Authentification
│   │   ├── portal.py      # Page principale
│   │   ├── driver.py      # Interface conducteur
│   │   ├── passenger.py   # Interface passager
│   │   └── admin.py       # Dashboard admin
│   │
│   ├── sockets/           # WebSockets (futur)
│   │   ├── __init__.py
│   │   ├── driver_events.py
│   │   └── passenger_events.py
│   │
│   ├── utils/             # Utilitaires
│   │   ├── __init__.py
│   │   ├── geolocation.py # Fonctions géolocalisation
│   │   └── whatsapp.py    # Notifications WhatsApp
│   │
│   └── templates/         # Templates HTML
│       ├── base.html
│       ├── index.html
│       ├── portal_driver.html
│       ├── portal_passenger.html
│       └── admin_dashboard.html
```

## Installation et Démarrage

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Migrer les données existantes (si applicable) :
```bash
python migrate_data.py
```

3. Démarrer l'application :
```bash
python wsgi.py
```

## Nouvelles Fonctionnalités

- Architecture modulaire avec blueprints
- Configuration via variables d'environnement
- Modèles séparés pour une meilleure organisation
- Utilitaires réutilisables
- Préparation pour les WebSockets
- Dashboard administrateur

## URLs Disponibles

- `/` - Page principale (inscription/liste)
- `/driver/<id>` - Interface conducteur
- `/passenger/<id>` - Interface passager  
- `/admin/` - Dashboard administrateur
- `/auth/login` - Connexion (à implémenter)
- `/auth/logout` - Déconnexion (à implémenter)