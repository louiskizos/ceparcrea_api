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
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    Member, ArticleCantine, CreditCantine, 
    LigneCreditCantine, RemboursementCantine
)

# ---------------------------------------------------------
# 1. SERIALIZERS POUR ARTICLES
# ---------------------------------------------------------
class ArticleCantineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCantine
        fields = ['id', 'nom', 'prix_unitaire', 'stock', 'description']


# ---------------------------------------------------------
# 2. SERIALIZERS POUR LA CRÉATION ET LECTURE DU PANIER
# ---------------------------------------------------------
class LigneCreditCantineSerializer(serializers.ModelSerializer):
    """Pour afficher le détail d'un article dans un panier (Lecture)"""
    nom_article = serializers.CharField(source='article.nom', read_only=True)

    class Meta:
        model = LigneCreditCantine
        fields = ['id', 'article', 'nom_article', 'quantite', 'prix_unitaire', 'prix_total']
        read_only_fields = ['prix_unitaire', 'prix_total']


class LigneCreditCantineCreateSerializer(serializers.Serializer):
    """Pour la validation des données d'entrée lors de la création d'un panier (Écriture)"""
    article_id = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)

    def validate_article_id(self, value):
        if not ArticleCantine.objects.filter(id=value).exists():
            raise serializers.ValidationError("Cet article n'existe pas.")
        return value


class CreditCantineCreateSerializer(serializers.Serializer):
    
    membre_id = serializers.IntegerField()
    devise = serializers.ChoiceField(choices=['cdf', 'usd'], default='cdf')
    articles = LigneCreditCantineCreateSerializer(many=True)

    def validate_membre_id(self, value):
        if not Member.objects.filter(id=value).exists():
            raise serializers.ValidationError("Le membre spécifié n'existe pas.")
        return value

    def validate_articles(self, value):
        if not value:
            raise serializers.ValidationError("Le panier ne peut pas être vide.")
        
        # Vérification des stocks disponibles avant validation
        for item in value:
            article = ArticleCantine.objects.get(id=item['article_id'])
            if article.stock < item['quantite']:
                raise serializers.ValidationError(
                    f"Stock insuffisant pour '{article.nom}'. Disponible: {article.stock}, Demandé: {item['quantite']}"
                )
        return value

    def create(self, validated_data):
        membre_id = validated_data['membre_id']
        devise = validated_data.get('devise', 'cdf')
        articles_data = validated_data['articles']

        # Utilisation d'une transaction atomique pour sécuriser la création et le stock
        with transaction.atomic():
            membre = Member.objects.get(id=membre_id)
            credit_cantine = CreditCantine.objects.create(membre=membre, devise=devise)

            for item in articles_data:
                article = ArticleCantine.objects.select_for_update().get(id=item['article_id'])
                
                # Création de la ligne du panier
                LigneCreditCantine.objects.create(
                    credit_cantine=credit_cantine,
                    article=article,
                    quantite=item['quantite']
                )

                # Mise à jour du stock
                article.stock -= item['quantite']
                article.save(update_fields=['stock'])

        return credit_cantine


class CreditCantineDetailSerializer(serializers.ModelSerializer):
    """Pour la lecture complète d'un Crédit Cantine avec ses lignes et remboursements"""
    nom_membre = serializers.CharField(source='membre.nom_complet', read_only=True)
    lignes = LigneCreditCantineSerializer(many=True, read_only=True)

    class Meta:
        model = CreditCantine
        fields = [
            'id', 'membre', 'nom_membre', 'montant_total', 
            'balance', 'devise', 'date', 'lignes'
        ]


# ---------------------------------------------------------
# 3. SERIALIZERS POUR LE DÉTAIL AGRÉGÉ (VOTRE FORMAT DÉSIRÉ)
# ---------------------------------------------------------
class CreditCantineGroupedResponseSerializer(serializers.Serializer):
    """
    Génère le format JSON personnalisé demandé :
    {
       "membre_id_1": {
           "nom_complet": "...",
           "articles": { ... },
           "prix_total": "..."
       }
    }
    """
    def to_representation(self, credits_queryset):
        data = {}

        for credit in credits_queryset:
            membre_key = f"membre_id_{credit.membre.id}"

            if membre_key not in data:
                data[membre_key] = {
                    "nom_complet": credit.membre.nom_complet,
                    "articles": {},
                    "prix_total": 0.00
                }

            # Agrégation des articles
            for ligne in credit.lignes.all():
                article_key = f"article_id_{ligne.article.id}"

                if article_key in data[membre_key]["articles"]:
                    art = data[membre_key]["articles"][article_key]
                    nouvelle_qte = art["quantite"] + ligne.quantite
                    nouveau_sous_total = float(art["sous_total"]) + float(ligne.prix_total)
                    
                    art["quantite"] = nouvelle_qte
                    art["sous_total"] = f"{nouveau_sous_total:.2f}"
                else:
                    data[membre_key]["articles"][article_key] = {
                        "nom_article": ligne.article.nom,
                        "quantite": ligne.quantite,
                        "prix_unitaire": f"{ligne.prix_unitaire:.2f}",
                        "sous_total": f"{ligne.prix_total:.2f}"
                    }

            # Calcul du total global cumulé du membre
            total_actuel = float(data[membre_key]["prix_total"])
            data[membre_key]["prix_total"] = f"{total_actuel + float(credit.montant_total):.2f}"

        return data


# ---------------------------------------------------------
# 4. SERIALIZERS POUR REMBOURSEMENT CANTINE
# ---------------------------------------------------------
class RemboursementCantineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemboursementCantine
        fields = ['id', 'credit_cantine', 'montant', 'devise', 'date']

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))