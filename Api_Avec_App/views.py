from rest_framework import generics, viewsets, status,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from .models import TypeMember, Member, Adhesion, Social, Compte, Transaction, Emprunt, Remboursement, Utilisateur
from .serializers import *
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import ExtractYear
import subprocess
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .models import *
from .serializers import *
from .pagination import StandardResultsSetPagination



class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAdminUser] 


class LoginAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # 1. Vérifier si les champs sont fournis
        if not username or not password:
            return Response(
                {'error': 'Veuillez fournir un nom d’utilisateur et un mot de passe.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Authentifier l'utilisateur
        user = authenticate(username=username, password=password)

        if user is not None:
            # 3. Vérifier que l'utilisateur est bien un membre du personnel/admin
            if not user.is_staff:
                return Response(
                    {'error': 'Accès refusé. Seuls les administrateurs peuvent se connecter.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 4. Récupérer ou créer un jeton (Token) pour cet utilisateur
            token, created = Token.objects.get_or_create(user=user)
            
            # 5. Renvoyer la réponse avec le jeton et les infos de l'utilisateur
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_200_OK)
        
        else:
            # Identifiants incorrects
            return Response(
                {'error': 'Identifiants invalides.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


from rest_framework.permissions import IsAuthenticated

class LogoutAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

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
        


# 1. TYPE MEMBER

class TypeMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = TypeMember.objects.all()
    serializer_class = TypeMemberSerializer
    pagination_class = StandardResultsSetPagination




# 2. MEMBER
class MemberViewSet(viewsets.ModelViewSet):
   # permission_classes = [IsAdminUser]
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom_complet']


# 3. ADHESION
class AdhesionViewSet(viewsets.ModelViewSet):
    #permission_classes = [IsAdminUser]
    queryset = Adhesion.objects.all().select_related('membre')
    serializer_class = AdhesionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['membre__nom_complet']


# 4. SOCIAL
class SocialViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Social.objects.all().select_related('membre')
    serializer_class = SocialSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['membre__nom_complet']


# 5. COMPTE
class CompteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Compte.objects.all().select_related('membre')
    serializer_class = CompteSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['numero_compte']

    @action(detail=False, methods=['get'], url_path='par-numero/(?P<numero>[^/.]+)')
    def get_par_numero(self, request, numero=None):
        try:
            compte = self.queryset.get(numero_compte=numero)
            serializer = self.get_serializer(compte)
            return Response(serializer.data)
        except Compte.DoesNotExist:
            return Response({'error': 'Compte non trouvé'}, status=status.HTTP_404_NOT_FOUND)


# 6. TRANSACTION
class TransactionViewSet(viewsets.ModelViewSet):

    #permission_classes = [IsAdminUser]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['compte__numero_compte']

    @action(detail=False, methods=['get'], url_path='compte/(?P<numero_compte>[^/.]+)')
    def liste_par_compte(self, request, numero_compte=None):
        transactions = self.queryset.filter(compte__numero_compte=numero_compte)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='par-annee')
    def liste_par_annee(self, request):
        annees = Transaction.objects.annotate(annee=ExtractYear('created_at')).values_list('annee', flat=True).distinct()
        data = {}
        for annee in annees:
            if annee is not None:
                trx_annee = Transaction.objects.filter(created_at__year=annee)
                data[annee] = TransactionSerializer(trx_annee, many=True).data
        return Response(data)


# 7. EMPRUNT
class EmpruntViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Emprunt.objects.all().select_related('membre')
    serializer_class = EmpruntSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['membre__nom_complet']

    @action(detail=False, methods=['get'], url_path='par-annee')
    def liste_par_annee(self, request):
        annees = Emprunt.objects.annotate(annee=ExtractYear('date')).values_list('annee', flat=True).distinct()
        data = {}
        for annee in annees:
            if annee is not None:
                emprunts_annee = Emprunt.objects.filter(date__year=annee)
                data[annee] = EmpruntSerializer(emprunts_annee, many=True).data
        return Response(data)


# 8. REMBOURSEMENT
class RemboursementViewSet(viewsets.ModelViewSet):
    
    permission_classes = [IsAdminUser]
    queryset = Remboursement.objects.all().select_related('emprunt__membre')
    serializer_class = RemboursementSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['emprunt__membre__nom_complet']

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

@api_view(['GET'])
def statistiques_totaux(request):
    """Retourne l'ensemble des sommes totales demandées."""
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




from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ArticleCantine, CreditCantine, RemboursementCantine
from .serializers import (
    ArticleCantineSerializer,
    CreditCantineDetailSerializer,
    CreditCantineCreateSerializer,
    CreditCantineGroupedResponseSerializer,
    RemboursementCantineSerializer
)

class ArticleCantineViewSet(viewsets.ModelViewSet):
    queryset = ArticleCantine.objects.all()
    serializer_class = ArticleCantineSerializer


class CreditCantineViewSet(viewsets.ModelViewSet):
    queryset = CreditCantine.objects.select_related('membre').prefetch_related('lignes__article')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreditCantineCreateSerializer
        return CreditCantineDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_validate(raise_exception=True)
        credit = serializer.save()
        
        # Retourne les détails du crédit créé
        response_serializer = CreditCantineDetailSerializer(credit)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # Action personnalisée pour obtenir la réponse groupée au format spécifique
    @action(detail=False, methods=['get'], url_path='groupes-par-membre')
    def groupes_par_membre(self, request):
        credits = self.get_queryset()
        serializer = CreditCantineGroupedResponseSerializer()
        return Response({"data": serializer.to_representation(credits)})


class RemboursementCantineViewSet(viewsets.ModelViewSet):
    queryset = RemboursementCantine.objects.all()
    serializer_class = RemboursementCantineSerializer



# ======================= Git Pull  ==========================


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