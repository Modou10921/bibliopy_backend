from django.contrib import admin
from django.contrib.auth.models import User

# ... tes autres enregistrements ...
# admin.site.register(User) # Optionnel, Django l'affiche déjà dans son interface principale
from .models import Etudiant, Livre, ExemplaireLivre, Emprunt, DemandeEmprunt, Admin

# Enregistrement de vos modèles pour qu'ils s'affichent dans l'administration
admin.site.register(Etudiant)
admin.site.register(Livre)
admin.site.register(ExemplaireLivre)
admin.site.register(Emprunt)
admin.site.register(DemandeEmprunt)
admin.site.register(Admin)