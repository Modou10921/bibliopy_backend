from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from datetime import date, timedelta, datetime
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
import uuid

from .models import Livre, ExemplaireLivre, Etudiant, Emprunt, DemandeEmprunt, Notification, DetailBibliotheque
from .serializers import (
    LivreSerializer, EmpruntSerializer, DemandeEmpruntSerializer,
    ProfilEtudiantSerializer, ModifierProfilSerializer, NotificationSerializer
)

# =========================================================
# VIEWSETS LIVRES
# =========================================================

class LivreViewSet(viewsets.ModelViewSet):
    queryset = Livre.objects.all()
    serializer_class = LivreSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['categorie', 'filiere']


# =========================================================
# DEMANDE EMPRUNT — AVEC LOGIQUE AUTOMATIQUE
# =========================================================

class DemandeViewSet(viewsets.ModelViewSet):
    queryset = DemandeEmprunt.objects.all()
    serializer_class = DemandeEmpruntSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = DemandeEmprunt.objects.select_related('livre', 'etudiant')
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id:
            queryset = queryset.filter(etudiant_id=etudiant_id)
        return queryset

    def create(self, request, *args, **kwargs):
        etudiant_id = request.data.get('etudiant')
        livre_id = request.data.get('livre')

        # Vérifier que l'étudiant existe
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
        except Etudiant.DoesNotExist:
            return Response(
                {'error': "Étudiant introuvable."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier que le livre existe
        try:
            livre = Livre.objects.get(id=livre_id)
        except Livre.DoesNotExist:
            return Response(
                {'error': "Livre introuvable."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🎯 AJOUT DE LA NOUVELLE RÈGLE MÉTIER : Pas de doublon au même moment
        # On vérifie s'il existe une demande active (ni rendue, ni refusée, ni annulée) pour ce même livre et cet étudiant
        deja_emprunte = DemandeEmprunt.objects.filter(
            etudiant=etudiant,
            livre=livre
        ).exclude(
            statut__in=['rendu', 'refuse', 'annule']
        ).exists()

        if deja_emprunte:
            return Response(
                {'error': f"Vous avez déjà un emprunt en cours ou une demande active pour le livre \"{livre.titre}\"."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ ANCIENNE RÈGLE MÉTIER : Compter les emprunts globaux en cours
        emprunts_en_cours = DemandeEmprunt.objects.filter(
            etudiant=etudiant,
            statut='accepte'
        ).count()

        if emprunts_en_cours >= 2:
            # ❌ Refus automatique — trop d'emprunts en cours
            demande = DemandeEmprunt.objects.create(
                etudiant=etudiant,
                livre=livre,
                statut='refuse',
                date_demande=date.today()
            )

            # Notification de refus
            Notification.objects.create(
                etudiant=etudiant,
                message=f"Votre demande d'emprunt du livre \"{livre.titre}\" a été refusée. Vous avez déjà 2 emprunts en cours.",
                livre=livre
            )

            return Response(
                {'message': 'Demande refusée : vous avez déjà 2 emprunts en cours.', 'statut': 'refuse'},
                status=status.HTTP_200_OK
            )
        else:
            # ✅ Acceptation automatique
            demande = DemandeEmprunt.objects.create(
                etudiant=etudiant,
                livre=livre,
                statut='accepte',
                date_demande=date.today(),
                date_retour_prevue=date.today() + timedelta(days=14)
            )

            # Notification d'acceptation
            Notification.objects.create(
                etudiant=etudiant,
                message=f"Votre demande d'emprunt du livre \"{livre.titre}\" a été acceptée.",
                livre=livre
            )

            serializer = DemandeEmpruntSerializer(demande)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# =========================================================
# VIEWSET EMPRUNTS
# =========================================================

class EmpruntViewSet(viewsets.ModelViewSet):
    queryset = Emprunt.objects.all()
    serializer_class = EmpruntSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = Emprunt.objects.all()
        etudiant_id = self.request.query_params.get('etudiant')
        if etudiant_id and etudiant_id.strip() != '':
            queryset = queryset.filter(etudiant_id=etudiant_id)
        return queryset


# =========================================================
# NOTIFICATIONS (Version Unique Nettoyée GET & POST)
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def get_notifications(request):
    if request.method == 'POST':
        etudiant_id = request.data.get('etudiant')
        livre_id = request.data.get('livre')
        message = request.data.get('message')
        try:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            livre = Livre.objects.get(id=livre_id) if livre_id else None
            Notification.objects.create(
                etudiant=etudiant,
                livre=livre,
                message=message
            )
            return Response({'message': 'Notification créée.'}, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    # GET
    etudiant_id = request.query_params.get('etudiant')
    if not etudiant_id:
        return Response({'error': 'ID étudiant manquant'}, status=400)
    notifications = Notification.objects.filter(
        etudiant_id=etudiant_id
    ).order_by('-date_creation')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def marquer_notification_lue(request, pk):
    try:
        notif = Notification.objects.get(pk=pk)
        notif.lue = True
        notif.save()
        return Response({'message': 'Notification marquée comme lue.'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification introuvable.'}, status=404)


# =========================================================
# STATS DASHBOARD ADMIN
# =========================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def stats(request):
    today = date.today()
    total_livres = Livre.objects.count()

    livres_empruntes_ids = DemandeEmprunt.objects.filter(
        statut='accepte'
    ).values_list('livre_id', flat=True)
    livres_disponibles = Livre.objects.exclude(id__in=livres_empruntes_ids).count()

    emprunts_en_cours = DemandeEmprunt.objects.filter(
        statut='accepte',
        date_retour_prevue__gte=today
    ).count()

    retards = DemandeEmprunt.objects.filter(
        statut='accepte',
        date_retour_prevue__lt=today
    ).count()

    return Response({
        'total_livres': total_livres,
        'livres_disponibles': livres_disponibles,
        'emprunts_en_cours': emprunts_en_cours,
        'retards': retards,
    })


# =========================================================
# EMPRUNTS EN COURS POUR LE DASHBOARD ADMIN
# =========================================================

@api_view(['GET'])
def emprunts_en_cours_admin(request):
    today = date.today()
    emprunts = DemandeEmprunt.objects.filter(
        statut='accepte'
    ).select_related('etudiant', 'livre').order_by('date_retour_prevue')

    data = []
    for e in emprunts:
        est_en_retard = e.date_retour_prevue and e.date_retour_prevue < today
        data.append({
            'id': e.id,
            'etudiant_nom': f"{e.etudiant.prenom} {e.etudiant.nom}",
            'livre_titre': e.livre.titre,
            'livre_image': e.livre.image if hasattr(e.livre, 'image') else '',
            'genre': e.livre.categorie if hasattr(e.livre, 'categorie') else '',
            'date_retour': e.date_retour_prevue,
            'statut': 'En retard' if est_en_retard else 'En cours',
        })

    return Response(data)


# =========================================================
# INSCRIPTION & CONNEXION
# =========================================================

@api_view(['POST'])
def inscription_etudiant(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    prenom = data.get('prenom')
    nom = data.get('nom')
    is_admin = data.get('isAdmin', False)

    from .models import Admin
    if Etudiant.objects.filter(email=email).exists() or Admin.objects.filter(email=email).exists():
        return Response({"error": "Cet email est déjà utilisé."}, status=400)

    hashed_password = make_password(password)

    if is_admin:
        Admin.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe_hash=hashed_password,
            niveau_acces=1
        )
        return Response({"message": "Inscription Admin réussie !"}, status=201)
    else:
        ine_carte = data.get('ine') or data.get('numero_carte_etudiant', 'SANS_INE')
        if Etudiant.objects.filter(numero_carte_etudiant=ine_carte).exists():
            return Response({"error": "Ce numéro d'INE / Carte étudiant existe déjà."}, status=400)
        Etudiant.objects.create(
            nom=nom,
            prenom=prenom,
            email=email,
            mot_de_passe_hash=hashed_password,
            numero_carte_etudiant=ine_carte
        )
        return Response({"message": "Inscription Étudiant réussie !"}, status=201)


@api_view(['POST'])
def connexion_etudiant(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    is_etudiant_checked = data.get('isEtudiant', True)

    from .models import Admin

    if is_etudiant_checked:
        try:
            etudiant = Etudiant.objects.get(email=email)
            if check_password(password, etudiant.mot_de_passe_hash):
                fake_token = str(uuid.uuid4())
                return Response({
                    "access": fake_token,
                    "user": {
                        "id": etudiant.id,
                        "email": etudiant.email,
                        "nom": etudiant.nom,
                        "prenom": etudiant.prenom,
                        "is_admin": False
                    }
                }, status=200)
        except Etudiant.DoesNotExist:
            pass
    else:
        try:
            admin_user = Admin.objects.get(email=email)
            if check_password(password, admin_user.mot_de_passe_hash):
                fake_token = str(uuid.uuid4())
                return Response({
                    "access": fake_token,
                    "user": {
                        "id": admin_user.id,
                        "email": admin_user.email,
                        "nom": admin_user.nom,
                        "prenom": admin_user.prenom,
                        "is_admin": True
                    }
                }, status=200)
        except Admin.DoesNotExist:
            pass

    return Response({"error": "Email ou mot de passe incorrect pour le rôle sélectionné."}, status=400)


# =========================================================
# PROFIL ETUDIANT
# =========================================================

@api_view(['GET'])
def get_profil(request):
    etudiant_id = request.query_params.get('id')
    if not etudiant_id:
        return Response({'erreur': 'ID manquant'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        etudiant = Etudiant.objects.get(pk=etudiant_id)
        serializer = ProfilEtudiantSerializer(etudiant)
        return Response(serializer.data)
    except Etudiant.DoesNotExist:
        return Response({'erreur': 'Étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
def modifier_profil(request):
    etudiant_id = request.query_params.get('id')
    if not etudiant_id:
        return Response({'erreur': 'ID manquant'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        etudiant = Etudiant.objects.get(pk=etudiant_id)
        serializer = ModifierProfilSerializer(etudiant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profil mis à jour avec succès'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Etudiant.DoesNotExist:
        return Response({'erreur': 'Étudiant non trouvé'}, status=status.HTTP_404_NOT_FOUND)


# =========================================================
# GRAPHIQUE STATISTIQUES
# =========================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def emprunts_par_mois(request):
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    
    resultats = DemandeEmprunt.objects.filter(
        statut='accepte'
    ).annotate(
        mois=TruncMonth('date_demande')
    ).values('mois').annotate(
        nombre=Count('id_demande')
    ).order_by('mois')

    data = []
    mois_noms = {
        1: 'Janv.', 2: 'Févr.', 3: 'Mars', 4: 'Avr.',
        5: 'Mai', 6: 'Juin', 7: 'Juil.', 8: 'Août',
        9: 'Sept.', 10: 'Oct.', 11: 'Nov.', 12: 'Déc.'
    }
    for r in resultats:
        data.append({
            'mois': mois_noms.get(r['mois'].month, ''),
            'nombre': r['nombre']
        })

    return Response(data)


# =========================================================
# CONFIGURATION BIBLIOTHEQUE
# =========================================================

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def obtenir_bibliotheque(request):
    if request.method == 'POST':
        nom = request.data.get('nom') or request.data.get('nom_universite')
        logo = request.data.get('logo') or request.data.get('logo_url')

        if not nom:
            return Response({"error": "Le nom de l'université est requis."}, status=400)

        DetailBibliotheque.objects.all().delete()
        biblio = DetailBibliotheque.objects.create(nom=nom, logo=logo or '')
        
        return Response({
            "message": "Bibliothèque créée avec succès !",
            "nom": biblio.nom,
            "logo": biblio.logo
        }, status=201)

    if request.method == 'GET':
        biblio = DetailBibliotheque.objects.first()
        if biblio:
            return Response({
                "nom": biblio.nom,
                "logo": biblio.logo
            }, status=200)
        else:
            return Response({
                "nom": "Université virtuelle UNCHK",
                "logo": "assets/logo-unchk.png"
            }, status=200)


# =========================================================
# LISTE ETUDIANTS POUR NOTIFICATIONS ADMIN
# =========================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_etudiants(request):
    etudiants = Etudiant.objects.all().order_by('-id')
    data = []
    for e in etudiants:
        data.append({
            'id': e.id,
            'nom': e.nom,
            'prenom': e.prenom,
            'email': e.email,
            'numero_carte_etudiant': e.numero_carte_etudiant,
        })
    return Response(data)


# =========================================================
# RELANCES ADMIN
# =========================================================

@api_view(['POST'])
def relancer_etudiant(request, emprunt_id):
    try:
        emprunt = Emprunt.objects.get(id=emprunt_id)
        etudiant = emprunt.etudiant
        
        if not emprunt.date_retour_prevue:
            return Response({'error': "Cet emprunt n'a pas de date de retour fixée."}, status=400)
            
        maintenant = timezone.now()
        
        if isinstance(emprunt.date_retour_prevue, datetime):
            date_retour = emprunt.date_retour_prevue
        else:
            date_retour = timezone.make_aware(datetime.combine(emprunt.date_retour_prevue, datetime.min.time()))

        difference = date_retour - maintenant
        total_secondes = difference.total_seconds()

        if total_secondes > 86400:
            jours = int(total_secondes // 86400)
            message = f"Rappel : Il vous reste {jours} jour(s) pour rendre le livre '{emprunt.livre_titre}'."
        elif 0 < total_secondes <= 86400:
            heures = int(total_secondes // 3600)
            message = f"Attention : Il ne vous reste que {heures} heure(s) pour rendre le livre '{emprunt.livre_titre}' !"
        else:
            jours_retard = abs(int(total_secondes // 86400))
            message = f"Urgent : Vous avez un retard de {jours_retard} jour(s) pour le livre '{emprunt.livre_titre}'. Merci de le restituer."

        Notification.objects.create(
            etudiant=etudiant,
            message=message,
            lue=False,
            date_creation=timezone.now()
        )

        return Response({'success': True, 'message': 'Notification envoyée avec succès !'}, status=200)

    except Emprunt.DoesNotExist:
        return Response({'error': 'Emprunt introuvable.'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)