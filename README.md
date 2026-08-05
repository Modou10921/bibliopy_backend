# 📚 BiblioPy — Backend (API REST)

BiblioPy est une application web full-stack de gestion de bibliothèque. Ce dépôt contient l'API REST développée avec Django et Django REST Framework.

---

## 🛠️ Stack Technique Backend

- **Langage :** Python
- **Framework :** Django / Django REST Framework
- **Base de données :** SQLite / PostgreSQL
- **Authentification :** JWT (JSON Web Tokens)

---

## ✨ Fonctionnalités Principales

- **Gestion des Livres :** API CRUD complète (ajout, modification, suppression, consultation).
- **Gestion des Étudiants :** Suivi des utilisateurs et profils.
- **Gestion des Emprunts :** Validation des demandes, retours et suivi des retards.
- **Authentification sécurisée :** Sécurisation des routes d'administration par jetons JWT.

---

## 💻 Installation & Lancement en Local

```bash
# 1. Cloner le dépôt
git clone [https://github.com/Modou10921/bibliopy_backend.git](https://github.com/Modou10921/bibliopy_backend.git)
cd bibliopy_backend

# 2. Créer et activer l'environnement virtuel
python -m venv venv
venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations
python manage.py migrate

# 5. Lancer le serveur
python manage.py runserver
