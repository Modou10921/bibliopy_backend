import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliopy_backend.settings')  # Adaptez si le nom du dossier settings diffère
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "bum"
email = "oluodom418@gmail.com"
password = "@fkbbaA0160"  # Changez ce mot de passe !

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superutilisateur '{username}' créé avec succès !")
else:
    print(f"L'utilisateur '{username}' existe déjà.")