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


class TypeMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeMember
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    
    type_member_nom = serializers.ReadOnlyField(source='type_member.nom')

    type_member = serializers.PrimaryKeyRelatedField(
        queryset=TypeMember.objects.all()
    )

    class Meta:
        model = Member
        fields = [
            'id', 
            'type_member_nom',
            'type_member',
            'nom_complet', 
            'phone', 
            'adresse', 
            'status'
        ]



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
        read_only_fields = ('reference', 'compte.numero_compte','created_at')

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


from rest_framework import serializers
from .models import (
    Member, ProduitCantine, CreditCantine, 
    LigneCreditCantine, RemboursementCantine
)


class ProduitCantineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitCantine
        fields = '__all__'


class LigneCreditCantineSerializer(serializers.ModelSerializer):
    nom_produit = serializers.ReadOnlyField(source='produit.nom')

    class Meta:
        model = LigneCreditCantine
        fields = [
            'id', 'credit_cantine', 'produit', 'nom_produit', 
            'quantite', 'prix_unitaire_applique', 'sous_total'
        ]
        read_only_fields = ['prix_unitaire_applique', 'sous_total']


class RemboursementCantineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemboursementCantine
        fields = '__all__'


class CreditCantineSerializer(serializers.ModelSerializer):
    # Lecture détaillée des lignes du panier et des remboursements associés
    lignes = LigneCreditCantineSerializer(many=True, read_only=True)
    remboursements_cantine = RemboursementCantineSerializer(many=True, read_only=True)
    nom_membre = serializers.ReadOnlyField(source='membre.nom_complet')

    class Meta:
        model = CreditCantine
        fields = [
            'id', 'membre', 'nom_membre', 'acompte_initial', 
            'montant_total_panier', 'balance', 'devise', 'date', 
            'lignes', 'remboursements_cantine'
        ]
        read_only_fields = ['montant_total_panier', 'balance']