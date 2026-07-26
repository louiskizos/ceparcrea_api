from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TypeMemberViewSet, MemberViewSet, AdhesionViewSet, 
    SocialViewSet, CompteViewSet, TransactionViewSet, 
    EmpruntViewSet, RemboursementViewSet, UtilisateurViewSet,
    LoginAPIView
)

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

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPIView.as_view(), name='api-login'),
]