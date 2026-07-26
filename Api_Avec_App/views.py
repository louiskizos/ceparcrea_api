from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from .models import TypeMember, Member, Adhesion, Social, Compte, Transaction, Emprunt, Remboursement, Utilisateur
from .serializers import (
    TypeMemberSerializer, MemberSerializer, AdhesionSerializer, 
    SocialSerializer, CompteSerializer, TransactionSerializer, 
    EmpruntSerializer, RemboursementSerializer, UtilisateurSerializer
)



class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAdminUser] # Seul un admin déjà connecté peut gérer les autres utilisateurs



class LoginAPIView(APIView):
    # Cette vue doit être accessible à tout le monde pour pouvoir se connecter
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




class TypeMemberViewSet(viewsets.ModelViewSet):
    queryset = TypeMember.objects.all()
    serializer_class = TypeMemberSerializer
    permission_classes = [IsAdminUser] # Seul l'administrateur y a accès


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
   # permission_classes = [IsAdminUser]

    @action(detail=True, methods=['get'], url_path='statut-adhesion')
    def verifier_adhesion(self, request, pk=None):
        """Permet de vérifier via API si un membre est en ordre pour une année spécifique (par défaut l'année en cours)."""
        membre = self.get_object()
        annee = request.query_params.get('annee', timezone.now().year)
        en_ordre = membre.est_en_ordre_adhesion(annee=int(annee))
        return Response({'membre': membre.nom_complet, 'annee': annee, 'en_ordre': en_ordre})


class AdhesionViewSet(viewsets.ModelViewSet):
    queryset = Adhesion.objects.all()
    serializer_class = AdhesionSerializer
    permission_classes = [IsAdminUser]


class SocialViewSet(viewsets.ModelViewSet):
    queryset = Social.objects.all()
    serializer_class = SocialSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'], url_path='point-semaine')
    def point_semaine(self, request):
        """Fait le point de la caisse 'Social' pour une semaine et une année données."""
        semaine = request.query_params.get('semaine')
        annee = request.query_params.get('annee', timezone.now().year)

        if not semaine:
            return Response({'error': "Le paramètre 'semaine' est obligatoire (1 à 53)."}, status=status.HTTP_400_BAD_REQUEST)

        total = Social.somme_totale_semaine(semaine=int(semaine), annee=int(annee))
        return Response({
            'semaine': semaine,
            'annee': annee,
            'total_collecte': total
        })


class CompteViewSet(viewsets.ModelViewSet):
    queryset = Compte.objects.all()
    serializer_class = CompteSerializer
    permission_classes = [IsAdminUser]


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]


class EmpruntViewSet(viewsets.ModelViewSet):
    queryset = Emprunt.objects.all()
    serializer_class = EmpruntSerializer
    permission_classes = [IsAdminUser]


class RemboursementViewSet(viewsets.ModelViewSet):
    queryset = Remboursement.objects.all()
    serializer_class = RemboursementSerializer
    permission_classes = [IsAdminUser]





# ======================= Git Pull  ==========================

import subprocess
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

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