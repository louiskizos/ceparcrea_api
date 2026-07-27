from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import TypeMember, Member, Adhesion, Social, Compte, Transaction, Emprunt, Remboursement, Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'password','role', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True} # Pour ne jamais afficher le mot de passe dans les réponses API
        }

    def create(self, validated_data):
        # Utilisation de la méthode spécifique de Django pour crypter le mot de passe
        user = Utilisateur.objects.create_user(**validated_data)
        return user


from rest_framework import serializers
from .models import TypeMember, Member, Adhesion, Social, Compte, Transaction, Emprunt, Remboursement

class TypeMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeMember
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    type_member_detail = TypeMemberSerializer(source='type_member', read_only=True)

    class Meta:
        model = Member
        fields = '__all__'

class AdhesionSerializer(serializers.ModelSerializer):
    membre_nom = serializers.CharField(source='membre.nom_complet', read_only=True)

    class Meta:
        model = Adhesion
        fields = '__all__'

class SocialSerializer(serializers.ModelSerializer):
    membre_nom = serializers.CharField(source='membre.nom_complet', read_only=True)

    class Meta:
        model = Social
        fields = '__all__'

class CompteSerializer(serializers.ModelSerializer):
    membre_nom = serializers.CharField(source='membre.nom_complet', read_only=True)

    class Meta:
        model = Compte
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('reference', 'created_at')

class EmpruntSerializer(serializers.ModelSerializer):
    membre_nom = serializers.CharField(source='membre.nom_complet', read_only=True)

    class Meta:
        model = Emprunt
        fields = '__all__'
        read_only_fields = ('total_a_payer', 'balance')

class RemboursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remboursement
        fields = '__all__'