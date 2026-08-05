from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Enregistrement des ViewSets
router = DefaultRouter()
router.register(r'livres', views.LivreViewSet)
router.register(r'emprunts', views.EmpruntViewSet)
router.register(r'demande-emprunt', views.DemandeViewSet, basename='demandeemprunt_api')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/stats/', views.stats),
    path('api/inscription/', views.inscription_etudiant, name='inscription'),
    path('api/login/', views.connexion_etudiant, name='login'),
    path('api/profil/', views.get_profil, name='profil'),
    path('api/profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('api/etudiants/', views.get_etudiants, name='etudiants'),
    path('api/emprunts-en-cours/', views.emprunts_en_cours_admin, name='emprunts-en-cours-admin'),
    path('api/emprunts/<int:emprunt_id>/relancer/', views.relancer_etudiant, name='relancer-etudiant'),
    
    # 🟢 LIGNE ACTIVÉE ET CORRIGÉE POUR ANGULAR :
    path('api/bibliotheque/', views.obtenir_bibliotheque, name='api-bibliotheque'),
     # 👇 Ajoute ces 2 lignes
    path('api/notifications/', views.get_notifications, name='notifications'),
    path('api/notifications/<int:pk>/lue/', views.marquer_notification_lue, name='notif-lue'),
    path('api/emprunts-par-mois/', views.emprunts_par_mois, name='emprunts-par-mois'),

    # Liens pour les statistiques si besoin :
    # path('api/statistiques/', views.obtenir_statistiques, name='api-statistiques'),
]