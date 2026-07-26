import uuid
import random
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class Utilisateur(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('agent', 'Agent'),
        
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    
    # Vous pouvez ajouter des champs personnalisés ici si nécessaire
    # Exemple : un numéro de téléphone pour l'admin
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} (Admin)"

    def save(self, *args, **kwargs):
        # Puisque seuls les administrateurs utilisent le système, 
        # on s'assure qu'ils ont par défaut le statut 'staff' pour accéder au backoffice
        if not self.id:
            self.is_staff = True
        super().save(*args, **kwargs)



# 1. TYPE MEMBERS
class TypeMember(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom


# 2. MEMBERS
class Member(models.Model):
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
    ]
    
    nom_complet = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    adresse = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='actif')
    type_member = models.ForeignKey(TypeMember, on_delete=models.PROTECT, related_name='members')

    def __str__(self):
        return self.nom_complet

    def est_en_ordre_adhesion(self, annee=2026):
        """Vérifie si le membre est en ordre d'adhésion pour une année donnée."""
        return self.adhesions.filter(annee=annee).exists()


# 3. ADHESIONS
class Adhesion(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='adhesions')
    annee = models.PositiveIntegerField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)

    class Meta:
        # Index unique pour empêcher de payer deux fois la même année
        unique_together = ('membre', 'annee')

    def __str__(self):
        return f"Adhésion {self.annee} - {self.membre.nom_complet}"


# 4. SOCIALS
class Social(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='socials')
    semaine = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(53)])
    annee = models.PositiveIntegerField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)

    class Meta:
        # Index unique pour empêcher de payer deux fois la même semaine de la même année
        unique_together = ('membre', 'semaine', 'annee')

    def __str__(self):
        return f"Social S{self.semaine}/{self.annee} - {self.membre.nom_complet}"

    @classmethod
    def somme_totale_semaine(cls, semaine, annee):
        """Calcule la somme totale collectée pour le social une semaine donnée."""
        result = cls.objects.filter(semaine=semaine, annee=annee).aggregate(total=models.Sum('montant'))
        return result['total'] or 0.00


# 5. COMPTE (ÉPARGNE)
class Compte(models.Model):
    membre = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='compte')
    numero_compte = models.CharField(max_length=15, unique=True, editable=False)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Compte N° {self.numero_compte} - {self.membre.nom_complet}"

    def save(self,*args,**kwargs):
        # Génération automatique d'un numéro de compte unique à 15 chiffres
        if not self.numero_compte:
            while True:
                numero = "".join([str(random.randint(0, 9)) for _ in range(15)])
                if not Compte.objects.filter(numero_compte=numero).exists():
                    self.numero_compte = numero
                    break
        super().save(*args, **kwargs)


# 6. TRANSACTIONS
class Transaction(models.Model):
    TYPE_TRANSACTION = [
        ('depot', 'Dépôt'),
        ('retrait', 'Retrait'),
    ]
    
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='transactions')
    type_transaction = models.CharField(max_length=10, choices=TYPE_TRANSACTION)
    montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=50, unique=True, editable=False)

    def __str__(self):
        return f"{self.type_transaction.upper()} - {self.montant} ({self.reference})"

    def save(self, *args, **kwargs):
        # Génération d'une référence unique pour la transaction
        if not self.reference:
            self.reference = f"TX-{uuid.uuid4().hex[:10].upper()}"

        # Utilisation d'une transaction SQL atomique pour mettre à jour la balance
        with transaction.atomic():
            # Sélection et verrouillage du compte pour éviter les accès concurrents (Race Conditions)
            compte_lie = Compte.objects.select_for_update().get(id=self.compte.id)

            if self.type_transaction == 'retrait':
                # Vérification de l'ordre d'adhésion avant un retrait
                if not compte_lie.membre.est_en_ordre_adhesion(annee=timezone.now().year):
                    raise ValidationError("Le membre doit être en ordre d'adhésion pour l'année en cours avant d'effectuer un retrait.")
                
                # Vérification du solde suffisant
                if compte_lie.balance < self.montant:
                    raise ValidationError("Solde insuffisant pour effectuer ce retrait.")
                
                compte_lie.balance -= self.montant
            
            elif self.type_transaction == 'depot':
                compte_lie.balance += self.montant

            # Sauvegarde du compte mis à jour
            compte_lie.save()
            # Sauvegarde de la transaction elle-même
            super().save(*args, **kwargs)


# 7. EMPRUNTS
class Emprunt(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='emprunts')
    montant_emprunt = models.DecimalField(max_digits=12, decimal_places=2)
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, help_text="En pourcentage (ex: 5 pour 5%)")
    total_a_payer = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False, help_text="Ce qu'il reste à rembourser")
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Emprunt {self.id} - {self.membre.nom_complet} (Reste: {self.balance})"

    def clean(self):
        # Vérification d'ordre d'adhésion avant de valider l'emprunt
        if not self.membre.est_en_ordre_adhesion(annee=timezone.now().year):
            raise ValidationError("Le membre doit être en ordre d'adhésion pour l'année en cours avant de contracter un emprunt.")

    def save(self,*args, **kwargs):
        self.full_clean() # Force l'exécution de la validation clean()
        if not self.id: # Lors de la création de l'emprunt uniquement
            interet = self.montant_emprunt * (self.taux_interet / 100)
            self.total_a_payer = self.montant_emprunt + interet
            self.balance = self.total_a_payer
        super().save(*args, **kwargs)


# 8. REMBOURSEMENTS
class Remboursement(models.Model):
    emprunt = models.ForeignKey(Emprunt, on_delete=models.CASCADE, related_name='remboursements')
    montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Remboursement de {self.montant} sur Emprunt {self.emprunt.id}"

    def save(self,*args, **kwargs):
        with transaction.atomic():
            # Sélection et verrouillage de l'emprunt pour mettre à jour la balance en toute sécurité
            emprunt_lie = Emprunt.objects.select_for_update().get(id=self.emprunt.id)

            if self.montant > emprunt_lie.balance:
                raise ValidationError(f"Le montant du remboursement ({self.montant}) est supérieur à la dette restante ({emprunt_lie.balance}).")

            # Soustraction du montant remboursé de la balance de l'emprunt
            emprunt_lie.balance -= self.montant
            emprunt_lie.save()

            # Sauvegarde du remboursement
            super().save(*args, **kwargs)