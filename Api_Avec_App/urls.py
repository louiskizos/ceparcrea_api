from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'utilisateurs', UtilisateurViewSet)
router.register(r'type-membres', TypeMemberViewSet)
router.register(r'membres', MemberViewSet)
router.register(r'adhesions', AdhesionViewSet)
router.register(r'socials', SocialViewSet)
router.register(r'comptes', CompteViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'emprunts', EmpruntViewSet)
router.register(r'remboursements', RemboursementViewSet)
router.register(r'cantine/produits', ProduitCantineViewSet, basename='produit-cantine')
router.register(r'cantine/credits', CreditCantineViewSet, basename='credit-cantine')
router.register(r'cantine/panier', LigneCreditCantineViewSet, basename='ligne-credit-cantine')
router.register(r'cantine/remboursements', RemboursementCantineViewSet, basename='remboursement-cantine')
router.register(r'liste_membres', MemberListViewSet, basename='liste-membres')
router.register(r'liste_adhesions', AdhesionListViewSet, basename='liste-adhesions')
router.register(r'liste_socials', SocialListViewSet, basename='liste-socials')
router.register(r'liste_comptes', CompteListViewSet, basename='liste-comptes')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('statistiques/totaux/', statistiques_totaux, name='statistiques-totaux'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('webhook/deploy/', github_webhook, name='github_webhook'),
]