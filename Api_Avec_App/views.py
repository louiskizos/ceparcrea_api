from rest_framework import  viewsets, status,filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from django.db.models.functions import ExtractYear
import subprocess
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .serializers import *
from .pagination import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    inline_serializer,
)
from rest_framework import serializers







# =============================================================
# AUTHENTICATION & UTILISATEURS
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister tous les utilisateurs", tags=["Utilisateurs"]),
    retrieve=extend_schema(summary="Détails d'un utilisateur", tags=["Utilisateurs"]),
    create=extend_schema(summary="Créer un utilisateur", tags=["Utilisateurs"]),
    update=extend_schema(summary="Modifier un utilisateur", tags=["Utilisateurs"]),
    partial_update=extend_schema(summary="Modifier partiellement un utilisateur", tags=["Utilisateurs"]),
    destroy=extend_schema(summary="Supprimer un utilisateur", tags=["Utilisateurs"]),
)
class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAdminUser]


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentification"],
        summary="Connexion administrateur",
        description="Authentifie un utilisateur administrateur et retourne son token d'accès.",
        request=inline_serializer(
            name="LoginRequest",
            fields={
                "username": serializers.CharField(required=True),
                "password": serializers.CharField(required=True, write_only=True),
            }
        ),
        responses={
            200: inline_serializer(
                name="LoginSuccessResponse",
                fields={
                    "token": serializers.CharField(),
                    "user_id": serializers.IntegerField(),
                    "username": serializers.CharField(),
                    "email": serializers.EmailField(),
                }
            ),
            400: inline_serializer(
                name="LoginError400",
                fields={"error": serializers.CharField()}
            ),
            403: inline_serializer(
                name="LoginError403",
                fields={"error": serializers.CharField()}
            ),
        }
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Veuillez fournir un nom d’utilisateur et un mot de passe.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is not None:
            if not user.is_staff:
                return Response(
                    {'error': 'Accès refusé. Seuls les administrateurs peuvent se connecter.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_200_OK)
        
        else:
            return Response(
                {'error': 'Identifiants invalides.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Authentification"],
        summary="Déconnexion de l'utilisateur",
        description="Révoque le token d'authentification courant.",
        request=None,
        responses={
            200: inline_serializer(
                name="LogoutSuccessResponse",
                fields={"message": serializers.CharField()}
            ),
            400: inline_serializer(
                name="LogoutErrorResponse",
                fields={"error": serializers.CharField()}
            ),
        }
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response(
                {'message': 'Déconnexion réussie.'}, 
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Une erreur est survenue lors de la déconnexion.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# =============================================================
# 1. TYPE MEMBER
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les types de membres (paginé)", tags=["Types de Membres"]),
    retrieve=extend_schema(summary="Obtenir un type de membre par ID", tags=["Types de Membres"]),
    create=extend_schema(summary="Créer un type de membre", tags=["Types de Membres"]),
    update=extend_schema(summary="Modifier un type de membre", tags=["Types de Membres"]),
    partial_update=extend_schema(summary="Modifier partiellement un type de membre", tags=["Types de Membres"]),
    destroy=extend_schema(summary="Supprimer un type de membre", tags=["Types de Membres"]),
)
class TypeMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = TypeMember.objects.all()
    serializer_class = TypeMemberSerializer
    pagination_class = StandardResultsSetPagination


# =============================================================
# 2. MEMBER
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les membres (paginé, recherchable)", tags=["Membres"]),
    retrieve=extend_schema(summary="Détails d'un membre", tags=["Membres"]),
    create=extend_schema(summary="Créer un membre", tags=["Membres"]),
    update=extend_schema(summary="Modifier un membre", tags=["Membres"]),
    partial_update=extend_schema(summary="Modifier partiellement un membre", tags=["Membres"]),
    destroy=extend_schema(summary="Supprimer un membre", tags=["Membres"]),
)
class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom_complet']


@extend_schema_view(
    list=extend_schema(summary="Lister tous les membres (sans pagination)", tags=["Membres"]),
    retrieve=extend_schema(summary="Détails d'un membre (liste non-paginée)", tags=["Membres"]),
)
class MemberListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser] 
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    pagination_class = None
    filter_backends = []


# =============================================================
# 3. ADHESION
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les adhésions (paginé)", tags=["Adhésions"]),
    retrieve=extend_schema(summary="Détails d'une adhésion", tags=["Adhésions"]),
    create=extend_schema(summary="Créer une adhésion", tags=["Adhésions"]),
    update=extend_schema(summary="Modifier une adhésion", tags=["Adhésions"]),
    partial_update=extend_schema(summary="Modifier partiellement une adhésion", tags=["Adhésions"]),
    destroy=extend_schema(summary="Supprimer une adhésion", tags=["Adhésions"]),
)
class AdhesionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Adhesion.objects.all().select_related('membre')
    serializer_class = AdhesionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['membre__nom_complet']


@extend_schema_view(
    list=extend_schema(summary="Lister toutes les adhésions (sans pagination)", tags=["Adhésions"]),
    retrieve=extend_schema(summary="Détails d'une adhésion (liste non-paginée)", tags=["Adhésions"]),
)
class AdhesionListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser] 
    queryset = Adhesion.objects.all().select_related('membre')
    serializer_class = AdhesionSerializer
    pagination_class = None
    filter_backends = []


# =============================================================
# 4. SOCIAL
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les cotisations sociales (paginé)", tags=["Social"]),
    retrieve=extend_schema(summary="Détails d'une cotisation sociale", tags=["Social"]),
    create=extend_schema(summary="Enregistrer une cotisation sociale", tags=["Social"]),
    update=extend_schema(summary="Modifier une cotisation sociale", tags=["Social"]),
    partial_update=extend_schema(summary="Modifier partiellement une cotisation sociale", tags=["Social"]),
    destroy=extend_schema(summary="Supprimer une cotisation sociale", tags=["Social"]),
)
class SocialViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Social.objects.all().select_related('membre')
    serializer_class = SocialSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['membre__nom_complet']


@extend_schema_view(
    list=extend_schema(summary="Lister toutes les cotisations sociales (sans pagination)", tags=["Social"]),
    retrieve=extend_schema(summary="Détails d'une cotisation (liste non-paginée)", tags=["Social"]),
)
class SocialListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser] 
    queryset = Social.objects.all().select_related('membre')
    serializer_class = SocialSerializer
    pagination_class = None
    filter_backends = []


# =============================================================
# 5. COMPTE
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les comptes (paginé)", tags=["Comptes"]),
    retrieve=extend_schema(summary="Détails d'un compte", tags=["Comptes"]),
    create=extend_schema(summary="Créer un compte", tags=["Comptes"]),
    update=extend_schema(summary="Modifier un compte", tags=["Comptes"]),
    partial_update=extend_schema(summary="Modifier partiellement un compte", tags=["Comptes"]),
    destroy=extend_schema(summary="Supprimer un compte", tags=["Comptes"]),
)
class CompteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Compte.objects.all().select_related('membre')
    serializer_class = CompteSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['numero_compte']

    @extend_schema(
        tags=["Comptes"],
        summary="Rechercher un compte par son numéro",
        parameters=[
            OpenApiParameter(
                name="numero",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Numéro exact du compte recherché"
            )
        ],
        responses={
            200: CompteSerializer,
            404: inline_serializer(name="CompteNotFound", fields={"error": serializers.CharField()})
        }
    )
    @action(detail=False, methods=['get'], url_path='par-numero/(?P<numero>[^/.]+)')
    def get_par_numero(self, request, numero=None):
        try:
            compte = self.queryset.get(numero_compte=numero)
            serializer = self.get_serializer(compte)
            return Response(serializer.data)
        except Compte.DoesNotExist:
            return Response({'error': 'Compte non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema_view(
    list=extend_schema(summary="Lister tous les comptes (sans pagination)", tags=["Comptes"]),
    retrieve=extend_schema(summary="Détails d'un compte (liste non-paginée)", tags=["Comptes"]),
)
class CompteListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Compte.objects.all().select_related('membre')
    serializer_class = CompteSerializer
    pagination_class = None
    filter_backends = []

    @extend_schema(
        tags=["Comptes"],
        summary="Rechercher un compte par son numéro (liste non-paginée)",
        parameters=[
            OpenApiParameter(
                name="numero",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Numéro exact du compte recherché"
            )
        ],
        responses={
            200: CompteSerializer,
            404: inline_serializer(name="CompteNotFoundReadOnly", fields={"error": serializers.CharField()})
        }
    )
    @action(detail=False, methods=['get'], url_path='par-numero/(?P<numero>[^/.]+)')
    def get_par_numero(self, request, numero=None):
        try:
            compte = self.queryset.get(numero_compte=numero)
            serializer = self.get_serializer(compte)
            return Response(serializer.data)
        except Compte.DoesNotExist:
            return Response({'error': 'Compte non trouvé'}, status=status.HTTP_404_NOT_FOUND)


# =============================================================
# 6. TRANSACTION
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les transactions (paginé)", tags=["Transactions"]),
    retrieve=extend_schema(summary="Détails d'une transaction", tags=["Transactions"]),
    create=extend_schema(summary="Créer une transaction", tags=["Transactions"]),
    update=extend_schema(summary="Modifier une transaction", tags=["Transactions"]),
    partial_update=extend_schema(summary="Modifier partiellement une transaction", tags=["Transactions"]),
    destroy=extend_schema(summary="Supprimer une transaction", tags=["Transactions"]),
)
class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['compte__numero_compte']

    @extend_schema(
        tags=["Transactions"],
        summary="Lister les transactions d'un compte spécifique",
        parameters=[
            OpenApiParameter(
                name="numero_compte",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Numéro du compte pour filtrer les transactions"
            )
        ],
        responses={200: TransactionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='compte/(?P<numero_compte>[^/.]+)')
    def liste_par_compte(self, request, numero_compte=None):
        transactions = self.queryset.filter(compte__numero_compte=numero_compte)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Transactions"],
        summary="Grouper les transactions par année",
        description="Retourne un dictionnaire regroupant la liste des transactions pour chaque année d'enregistrement.",
        responses={
            200: inline_serializer(
                name="TransactionsParAnneeResponse",
                fields={
                    "2025": TransactionSerializer(many=True),
                    "2026": TransactionSerializer(many=True),
                }
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='par-annee')
    def liste_par_annee(self, request):
        annees = Transaction.objects.annotate(annee=ExtractYear('created_at')).values_list('annee', flat=True).distinct()
        data = {}
        for annee in annees:
            if annee is not None:
                trx_annee = Transaction.objects.filter(created_at__year=annee)
                data[annee] = TransactionSerializer(trx_annee, many=True).data
        return Response(data)


# =============================================================
# 7. EMPRUNT
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les emprunts (paginé)", tags=["Emprunts"]),
    retrieve=extend_schema(summary="Détails d'un emprunt", tags=["Emprunts"]),
    create=extend_schema(summary="Enregistrer un emprunt", tags=["Emprunts"]),
    update=extend_schema(summary="Modifier un emprunt", tags=["Emprunts"]),
    partial_update=extend_schema(summary="Modifier partiellement un emprunt", tags=["Emprunts"]),
    destroy=extend_schema(summary="Supprimer un emprunt", tags=["Emprunts"]),
)
class EmpruntViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Emprunt.objects.all().select_related('membre')
    serializer_class = EmpruntSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['membre__nom_complet']

    @extend_schema(
        tags=["Emprunts"],
        summary="Grouper les emprunts par année",
        responses={
            200: inline_serializer(
                name="EmpruntsParAnneeResponse",
                fields={
                    "2025": EmpruntSerializer(many=True),
                    "2026": EmpruntSerializer(many=True),
                }
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='par-annee')
    def liste_par_annee(self, request):
        annees = Emprunt.objects.annotate(annee=ExtractYear('date')).values_list('annee', flat=True).distinct()
        data = {}
        for annee in annees:
            if annee is not None:
                emprunts_annee = Emprunt.objects.filter(date__year=annee)
                data[annee] = EmpruntSerializer(emprunts_annee, many=True).data
        return Response(data)


# =============================================================
# 8. REMBOURSEMENT
# =============================================================

@extend_schema_view(
    list=extend_schema(summary="Lister les remboursements (paginé)", tags=["Remboursements"]),
    retrieve=extend_schema(summary="Détails d'un remboursement", tags=["Remboursements"]),
    create=extend_schema(summary="Enregistrer un remboursement", tags=["Remboursements"]),
    update=extend_schema(summary="Modifier un remboursement", tags=["Remboursements"]),
    partial_update=extend_schema(summary="Modifier partiellement un remboursement", tags=["Remboursements"]),
    destroy=extend_schema(summary="Supprimer un remboursement", tags=["Remboursements"]),
)
class RemboursementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Remboursement.objects.all().select_related('emprunt__membre')
    serializer_class = RemboursementSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['emprunt__membre__nom_complet']

    @extend_schema(
        tags=["Remboursements"],
        summary="Grouper les remboursements par année",
        responses={
            200: inline_serializer(
                name="RemboursementsParAnneeResponse",
                fields={
                    "2025": RemboursementSerializer(many=True),
                    "2026": RemboursementSerializer(many=True),
                }
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='par-annee')
    def liste_par_annee(self, request):
        annees = Remboursement.objects.annotate(annee=ExtractYear('date')).values_list('annee', flat=True).distinct()
        data = {}
        for annee in annees:
            if annee is not None:
                remboursements_annee = Remboursement.objects.filter(date__year=annee)
                data[annee] = RemboursementSerializer(remboursements_annee, many=True).data
        return Response(data)


# -------------------------------------------------------------
# ENDPOINTS SPÉCIFIQUES (Statistiques & Totaux)
# -------------------------------------------------------------

@extend_schema(
    tags=["Statistiques"],
    summary="Récupérer la synthèse des totaux financiers",
    description="Calcule et retourne la somme globale de l'épargne, du fonds social, des emprunts, des remboursements et des adhésions.",
    responses={
        200: inline_serializer(
            name="StatistiquesTotauxResponse",
            fields={
                "somme_totale_compte_epargne": serializers.FloatField(),
                "somme_totale_social": serializers.FloatField(),
                "somme_totale_emprunt": serializers.FloatField(),
                "somme_totale_remboursement": serializers.FloatField(),
                "somme_totale_adhesion": serializers.FloatField(),
            }
        )
    }
)
@api_view(['GET'])
def statistiques_totaux(request):
    total_epargne = Compte.objects.aggregate(total=Sum('balance')).get('total') or 0.00
    total_social = Social.objects.aggregate(total=Sum('montant')).get('total') or 0.00
    total_emprunt = Emprunt.objects.aggregate(total=Sum('montant_emprunt')).get('total') or 0.00
    total_remboursement = Remboursement.objects.aggregate(total=Sum('montant')).get('total') or 0.00
    total_adhesion = Adhesion.objects.aggregate(total=Sum('montant')).get('total') or 0.00

    return Response({
        'somme_totale_compte_epargne': total_epargne,
        'somme_totale_social': total_social,
        'somme_totale_emprunt': total_emprunt,
        'somme_totale_remboursement': total_remboursement,
        'somme_totale_adhesion': total_adhesion,
    })


# -------------------------------------------------------------
# CANTINE - PRODUITS & CRÉDITS
# -------------------------------------------------------------

@extend_schema_view(
    list=extend_schema(summary="Lister les produits de la cantine", tags=["Cantine - Produits"]),
    retrieve=extend_schema(summary="Détails d'un produit de la cantine", tags=["Cantine - Produits"]),
    create=extend_schema(summary="Créer un produit de la cantine", tags=["Cantine - Produits"]),
    update=extend_schema(summary="Modifier un produit", tags=["Cantine - Produits"]),
    partial_update=extend_schema(summary="Modifier partiellement un produit", tags=["Cantine - Produits"]),
    destroy=extend_schema(summary="Supprimer un produit", tags=["Cantine - Produits"]),
)
class ProduitCantineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ProduitCantine.objects.all()
    serializer_class = ProduitCantineSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['nom']


@extend_schema_view(
    list=extend_schema(summary="Lister les crédits cantine", tags=["Cantine - Crédits"]),
    retrieve=extend_schema(summary="Détails d'un crédit cantine", tags=["Cantine - Crédits"]),
    create=extend_schema(summary="Créer une commande à crédit", tags=["Cantine - Crédits"]),
    update=extend_schema(summary="Modifier un crédit cantine", tags=["Cantine - Crédits"]),
    partial_update=extend_schema(summary="Modifier partiellement un crédit", tags=["Cantine - Crédits"]),
    destroy=extend_schema(summary="Supprimer un crédit cantine", tags=["Cantine - Crédits"]),
)
class CreditCantineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = CreditCantine.objects.all().order_by('-date')
    serializer_class = CreditCantineSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['membre', 'devise']
    search_fields = ['membre__nom_complet']

    @extend_schema(
        tags=["Cantine - Crédits"],
        summary="Ajouter une ligne de produit à une commande à crédit",
        description="Associe un produit et sa quantité à une fiche de crédit cantine existante.",
        request=inline_serializer(
            name="AjouterProduitCreditRequest",
            fields={
                "produit": serializers.IntegerField(help_text="ID du produit cantine à ajouter"),
                "quantite": serializers.IntegerField(default=1, help_text="Quantité commandée"),
            }
        ),
        responses={
            201: CreditCantineSerializer,
            400: inline_serializer(
                name="AjouterProduitCreditError",
                fields={"produit": serializers.ListField(child=serializers.CharField())}
            )
        }
    )
    @action(detail=True, methods=['post'], url_path='ajouter-produit')
    def ajouter_produit(self, request, pk=None):
        credit = self.get_object()
        serializer = LigneCreditCantineSerializer(data={
            'credit_cantine': credit.id,
            'produit': request.data.get('produit'),
            'quantite': request.data.get('quantite', 1)
        })
        
        if serializer.is_valid():
            serializer.save()
            credit_serializer = self.get_serializer(credit)
            return Response(credit_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(summary="Lister les lignes de crédits cantine", tags=["Cantine - Lignes de Crédit"]),
    retrieve=extend_schema(summary="Détails d'une ligne de crédit", tags=["Cantine - Lignes de Crédit"]),
    create=extend_schema(summary="Créer une ligne de crédit", tags=["Cantine - Lignes de Crédit"]),
    update=extend_schema(summary="Modifier une ligne de crédit", tags=["Cantine - Lignes de Crédit"]),
    partial_update=extend_schema(summary="Modifier partiellement une ligne de crédit", tags=["Cantine - Lignes de Crédit"]),
    destroy=extend_schema(summary="Supprimer une ligne de crédit", tags=["Cantine - Lignes de Crédit"]),
)
class LigneCreditCantineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LigneCreditCantine.objects.all()
    serializer_class = LigneCreditCantineSerializer
    filterset_fields = ['credit_cantine']


@extend_schema_view(
    list=extend_schema(summary="Lister les remboursements de cantine", tags=["Cantine - Remboursements"]),
    retrieve=extend_schema(summary="Détails d'un remboursement cantine", tags=["Cantine - Remboursements"]),
    create=extend_schema(summary="Enregistrer un remboursement de cantine", tags=["Cantine - Remboursements"]),
    update=extend_schema(summary="Modifier un remboursement", tags=["Cantine - Remboursements"]),
    partial_update=extend_schema(summary="Modifier partiellement un remboursement", tags=["Cantine - Remboursements"]),
    destroy=extend_schema(summary="Supprimer un remboursement", tags=["Cantine - Remboursements"]),
)
class RemboursementCantineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = RemboursementCantine.objects.all().order_by('-date')
    serializer_class = RemboursementCantineSerializer
    filterset_fields = ['credit_cantine']


# ======================= Git Webhook ==========================

@extend_schema(
    exclude=True  # Exclut le Webhook GitHub de la documentation Swagger publique
)
@csrf_exempt
def github_webhook(request):
    if request.method == 'POST':
        repo_dir = '/home/c2798164c/repositories/ceparcrea_api'
        target_dir = '/home/c2798164c/ceparcea'

        try:
            # 1. Faire le git pull dans le dépôt source
            subprocess.run(['git', '-C', repo_dir, 'pull', 'origin', 'main'], check=True)
            
            # 2. Copier les fichiers vers le répertoire cible
            subprocess.run(f"cp -R {repo_dir}/* {target_dir}/", shell=True, check=True)

            # 3. Réaliser les migrations si nécessaire et redémarrer la WSGI
            subprocess.run(f"touch {target_dir}/tmp/restart.txt", shell=True)

            return HttpResponse("Deployment successful", status=200)
        except Exception as e:
            return HttpResponse(f"Deployment failed: {str(e)}", status=500)
    
    return HttpResponseForbidden("Method not allowed")