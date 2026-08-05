from django.db import models

# ==========================================
# 1. CLASSE UTILISATEUR (Abstraite)
# ==========================================
class Utilisateur(models.Model):
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    mot_de_passe_hash = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.prenom} {self.nom}"

# ==========================================
# 2. CLASSE ETUDIANT
# ==========================================
class Etudiant(Utilisateur):
    numero_carte_etudiant = models.CharField(max_length=50, unique=True)
    nb_emprunts_en_cours = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.numero_carte_etudiant})"

# ==========================================
# 3. CLASSE ADMIN
# ==========================================
class Admin(Utilisateur):
    niveau_acces = models.IntegerField(default=1)

    def __str__(self):
        return f"Admin: {self.prenom} {self.nom}"

# ==========================================
# 4. CLASSE LIVRE
# ==========================================
class Livre(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    titre = models.CharField(max_length=255)
    auteur = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100)
    filiere = models.CharField(max_length=100, blank=True, null=True)  # 👈 ajoute
    date_publication = models.DateField()
    image = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.titre

# ==========================================
# 5. CLASSE EXEMPLAIRE LIVRE
# ==========================================
class ExemplaireLivre(models.Model):
    id_exemplaire = models.CharField(max_length=50, unique=True)
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name="exemplaires")
    etat_physique = models.CharField(max_length=100)
    statut_disponibilite = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.livre.titre} - Réf: {self.id_exemplaire}"

# ==========================================
# 6. CLASSE DEMANDE EMPRUNT
# ==========================================
class DemandeEmprunt(models.Model):
    id_demande = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="demandes")
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name="demandes", null=True, blank=True)
    date_demande = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=50, default="En attente")
    date_retour_prevue = models.DateField(null=True, blank=True)  # 👈 ajoute cette ligne

    def __str__(self):
        return f"Demande {self.id_demande} par {self.etudiant}"

# ==========================================
# 7. CLASSE EMPRUNT
# ==========================================
class Emprunt(models.Model):
    id_emprunt = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="emprunts")
    exemplaire = models.ForeignKey(ExemplaireLivre, on_delete=models.CASCADE, related_name="emprunts")
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_reelle = models.DateField(null=True, blank=True)
    est_prolonge = models.BooleanField(default=False)

    def __str__(self):
        return f"Emprunt {self.id_emprunt} - {self.etudiant}"

# Ajoute ce modèle dans ton fichier bibliotheque/models.py
# (après tes modèles existants)

class Notification(models.Model):
    etudiant = models.ForeignKey(
        'Etudiant',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    livre = models.ForeignKey(
        'Livre',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    message = models.TextField()
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif pour {self.etudiant} - {self.message[:40]}"
    
class DetailBibliotheque(models.Model):
    nom = models.CharField(max_length=255)
    logo = models.TextField()  # Reçoit l'URL de l'image (ImgBB, etc.)

    def __str__(self):
        return self.nom