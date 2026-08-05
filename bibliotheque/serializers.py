import hashlib
from rest_framework import serializers
from .models import Livre, Emprunt, DemandeEmprunt, Etudiant, Utilisateur

class LivreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livre
        fields = '__all__'

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'nom', 'prenom', 'email']

class EtudiantSerializer(serializers.ModelSerializer):
    utilisateur = UtilisateurSerializer()
    class Meta:
        model = Etudiant
        fields = '__all__'

class EmpruntSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emprunt
        fields = '__all__'

class DemandeEmpruntSerializer(serializers.ModelSerializer):
    livre_details = LivreSerializer(source='livre', read_only=True)

    class Meta:
        model = DemandeEmprunt
        fields = ['id_demande', 'etudiant', 'livre', 'livre_details', 
                  'date_demande', 'statut', 'date_retour_prevue']
        
class ProfilEtudiantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Etudiant
        fields = ['id', 'nom', 'prenom', 'email', 'numero_carte_etudiant', 'nb_emprunts_en_cours']
        read_only_fields = ['numero_carte_etudiant', 'nb_emprunts_en_cours']

class ModifierProfilSerializer(serializers.ModelSerializer):
    nouveau_mot_de_passe = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Etudiant
        fields = ['nom', 'prenom', 'email', 'nouveau_mot_de_passe']

    def update(self, instance, validated_data):
        mdp = validated_data.pop('nouveau_mot_de_passe', None)
        instance.nom = validated_data.get('nom', instance.nom)
        instance.prenom = validated_data.get('prenom', instance.prenom)
        instance.email = validated_data.get('email', instance.email)
        if mdp:
            instance.mot_de_passe_hash = hashlib.sha256(mdp.encode()).hexdigest()
        instance.save()
        return instance
    
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    livre_image = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'message', 'lue', 'date_creation', 'livre', 'livre_image']

    def get_livre_image(self, obj):
        if obj.livre:
            return obj.livre.image
        return None