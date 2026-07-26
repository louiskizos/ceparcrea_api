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
    est_en_ordre = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = '__all__'

    def get_est_en_ordre(self, obj):
        # Vérifie si le membre est en ordre pour l'année en cours
        annee_courante = timezone.now().year
        return obj.est_en_ordre_adhesion(annee=annee_courante)


class AdhesionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adhesion
        fields = '__all__'


class SocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Social
        fields = '__all__'


class CompteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compte
        fields = ['id', 'membre', 'numero_compte', 'balance']
        read_only_fields = ['numero_compte', 'balance']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'compte', 'type_transaction', 'montant', 'date', 'reference']
        read_only_fields = ['reference', 'date']

    def validate(self, data):
        compte = data['compte']
        type_tx = data['type_transaction']
        montant = data['montant']
        annee_courante = timezone.now().year

        if type_tx == 'retrait':
            # 1. Vérifier si le membre est en ordre d'adhésion
            if not compte.membre.est_en_ordre_adhesion(annee=annee_courante):
                raise serializers.ValidationError(
                    f"Le membre doit être en ordre d'adhésion pour l'année {annee_courante} avant d'effectuer un retrait."
                )
            
            # 2. Vérifier si le solde est suffisant
            if compte.balance < montant:
                raise serializers.ValidationError("Solde insuffisant pour effectuer ce retrait.")
        
        return data


class EmpruntSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emprunt
        fields = ['id', 'membre', 'montant_emprunt', 'taux_interet', 'total_a_payer', 'balance', 'date']
        read_only_fields = ['total_a_payer', 'balance']

    def validate(self, data):
        membre = data['membre']
        annee_courante = timezone.now().year

        # Vérifier si le membre est en ordre d'adhésion avant l'emprunt
        if not membre.est_en_ordre_adhesion(annee=annee_courante):
            raise serializers.ValidationError(
                f"Le membre doit être en ordre d'adhésion pour l'année {annee_courante} avant d'emprunter."
            )
        return data


class RemboursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remboursement
        fields = '__all__'

    def validate(self, data):
        emprunt = data['emprunt']
        montant = data['montant']

        # Vérifier si le remboursement ne dépasse pas la dette restante
        if montant > emprunt.balance:
            raise serializers.ValidationError(
                f"Le montant ({montant}) dépasse la dette restante ({emprunt.balance})."
            )
        return data