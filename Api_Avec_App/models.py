# import uuid
# import random
# from django.db import models, transaction
# from django.core.exceptions import ValidationError
# from django.core.validators import MinValueValidator, MaxValueValidator
# from django.utils import timezone
# from django.contrib.auth.models import AbstractUser
# import datetime



# class Utilisateur(AbstractUser):

#     ROLE_CHOICES = (
#         ('admin', 'Admin'),
#         ('agent', 'Agent'),
        
#     )
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    
#     # Vous pouvez ajouter des champs personnalisés ici si nécessaire
#     # Exemple : un numéro de téléphone pour l'admin
#     telephone = models.CharField(max_length=20, blank=True, null=True)

#     def __str__(self):
#         return f"{self.username} (Admin)"

#     def save(self, *args, **kwargs):
#         # Puisque seuls les administrateurs utilisent le système, 
#         # on s'assure qu'ils ont par défaut le statut 'staff' pour accéder au backoffice
#         if not self.id:
#             self.is_staff = True
#         super().save(*args, **kwargs)



# # 1. TYPE MEMBERS
# class TypeMember(models.Model):
#     nom = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.nom


# # 2. MEMBERS
# class Member(models.Model):
#     STATUS_CHOICES = [
#         ('actif', 'Actif'),
#         ('inactif', 'Inactif'),
#     ]
    
#     nom_complet = models.CharField(max_length=255)
#     phone = models.CharField(max_length=20, unique=True)
#     adresse = models.TextField()
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='actif')
#     type_member = models.ForeignKey(TypeMember, on_delete=models.PROTECT, related_name='members')

#     def __str__(self):
#         return self.nom_complet

#     def est_en_ordre_adhesion(self, annee=2026):
#         """Vérifie si le membre est en ordre d'adhésion pour une année donnée."""
#         return self.adhesions.filter(annee=annee).exists()


# # 3. ADHESIONS
# class Adhesion(models.Model):
#     membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='adhesions')
#     annee = models.PositiveIntegerField()
#     montant = models.DecimalField(max_digits=12, decimal_places=2)
#     devise = models.TextField(default='cdf')
#     date = models.DateField(default=timezone.now)

#     class Meta:
#         # Index unique pour empêcher de payer deux fois la même année
#         unique_together = ('membre', 'annee')

#     def __str__(self):
#         return f"Adhésion {self.annee} - {self.membre.nom_complet}"


# # 4. SOCIALS
# class Social(models.Model):
#     membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='socials')
#     semaine = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(53)])
#     annee = models.PositiveIntegerField()
#     montant = models.DecimalField(max_digits=12, decimal_places=2)
#     devise = models.TextField(default='cdf')
#     date = models.DateField(default=timezone.now)

#     class Meta:
#         # Index unique pour empêcher de payer deux fois la même semaine de la même année
#         unique_together = ('membre', 'semaine', 'annee')

#     def __str__(self):
#         return f"Social S{self.semaine}/{self.annee} - {self.membre.nom_complet}"

#     @classmethod
#     def somme_totale_semaine(cls, semaine, annee):
#         """Calcule la somme totale collectée pour le social une semaine donnée."""
#         result = cls.objects.filter(semaine=semaine, annee=annee).aggregate(total=models.Sum('montant'))
#         return result['total'] or 0.00


# # 5. COMPTE (ÉPARGNE)
# class Compte(models.Model):
#     membre = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='compte')
#     numero_compte = models.CharField(max_length=15, unique=True, editable=False)
#     devise = models.TextField(default='cdf')
#     balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

#     def __str__(self):
#         return f"Compte N° {self.numero_compte} - {self.membre.nom_complet}"

#     def save(self,*args,**kwargs):
#         # Génération automatique d'un numéro de compte unique à 15 chiffres
#         if not self.numero_compte:
#             while True:
#                 numero = "".join([str(random.randint(0, 9)) for _ in range(15)])
#                 if not Compte.objects.filter(numero_compte=numero).exists():
#                     self.numero_compte = numero
#                     break
#         super().save(*args, **kwargs)


# class Transaction(models.Model):

#     reference = models.CharField(max_length=30, unique=True, editable=False)
#     compte = models.ForeignKey('Compte', on_delete=models.CASCADE, related_name='transactions')
#     montant = models.DecimalField(max_digits=12, decimal_places=2)
#     type_transaction = models.CharField(max_length=20) # ex: DEPOT, RETRAIT
#     created_at = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         if not self.reference:
#             today_str = datetime.date.today().strftime('%Y%m%d')
#             prefix = f"TRX-{today_str}-"
            
#             # Compte le nombre de transactions aujourd'hui pour incrémenter le numéro
#             last_trx = Transaction.objects.filter(reference__startswith=prefix).order_by('-id').first()
#             if last_trx:
#                 last_number = int(last_trx.reference.split('-')[-1])
#                 new_number = last_number + 1
#             else:
#                 new_number = 1
                
#             self.reference = f"{prefix}{new_number:04d}" # Résultat: TRX-20260727-0001
#         super().save(*args, **kwargs)


# # 7. EMPRUNTS
# class Emprunt(models.Model):
#     membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='emprunts')
#     montant_emprunt = models.DecimalField(max_digits=12, decimal_places=2)
#     devise = models.TextField(default='cdf')
#     taux_interet = models.DecimalField(max_digits=5, decimal_places=2, help_text="En pourcentage (ex: 5 pour 5%)")
#     total_a_payer = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
#     balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False, help_text="Ce qu'il reste à rembourser")
#     date = models.DateField(default=timezone.now)

#     def __str__(self):
#         return f"Emprunt {self.id} - {self.membre.nom_complet} (Reste: {self.balance})"

#     def clean(self):
#         # Vérification d'ordre d'adhésion avant de valider l'emprunt
#         if not self.membre.est_en_ordre_adhesion(annee=timezone.now().year):
#             raise ValidationError("Le membre doit être en ordre d'adhésion pour l'année en cours avant de contracter un emprunt.")

#     def save(self,*args, **kwargs):
#         self.full_clean() # Force l'exécution de la validation clean()
#         if not self.id: # Lors de la création de l'emprunt uniquement
#             interet = self.montant_emprunt * (self.taux_interet / 100)
#             self.total_a_payer = self.montant_emprunt + interet
#             self.balance = self.total_a_payer
#         super().save(*args, **kwargs)


# # 8. REMBOURSEMENTS
# class Remboursement(models.Model):
#     emprunt = models.ForeignKey(Emprunt, on_delete=models.CASCADE, related_name='remboursements')
#     montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
#     devise = models.TextField(default='cdf')
#     date = models.DateField(default=timezone.now)

#     def __str__(self):
#         return f"Remboursement de {self.montant} sur Emprunt {self.emprunt.id}"

#     def save(self,*args, **kwargs):
        
#         with transaction.atomic():
#             # Sélection et verrouillage de l'emprunt pour mettre à jour la balance en toute sécurité
#             emprunt_lie = Emprunt.objects.select_for_update().get(id=self.emprunt.id)

#             if self.montant > emprunt_lie.balance:
#                 raise ValidationError(f"Le montant du remboursement ({self.montant}) est supérieur à la dette restante ({emprunt_lie.balance}).")

#             # Soustraction du montant remboursé de la balance de l'emprunt
#             emprunt_lie.balance -= self.montant
#             emprunt_lie.save()

#             # Sauvegarde du remboursement
#             super().save(*args, **kwargs)


import uuid
import random
import datetime
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


DEVISE_CHOICES = (
    ('cdf', 'CDF'),
    ('usd', 'USD'),
)

# ---------------------------------------------------------
# 1. UTILISATEUR & MEMBRES
# ---------------------------------------------------------
class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('agent', 'Agent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.is_staff = True
        super().save(*args, **kwargs)


class TypeMember(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom


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

    def est_en_ordre_adhesion(self, annee=None):
        if annee is None:
            annee = timezone.now().year
        return self.adhesions.filter(annee=annee).exists()


# ---------------------------------------------------------
# 2. ADHESIONS & SOCIALS
# ---------------------------------------------------------
class Adhesion(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='adhesions')
    annee = models.PositiveIntegerField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('membre', 'annee')

    def __str__(self):
        return f"Adhésion {self.annee} - {self.membre.nom_complet}"


class Social(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='socials')
    semaine = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(53)])
    annee = models.PositiveIntegerField()
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('membre', 'semaine', 'annee')

    def __str__(self):
        return f"Social S{self.semaine}/{self.annee} - {self.membre.nom_complet}"

    @classmethod
    def somme_totale_semaine(cls, semaine, annee):
        result = cls.objects.filter(semaine=semaine, annee=annee).aggregate(total=models.Sum('montant'))
        return result['total'] or 0.00


# ---------------------------------------------------------
# 3. COMPTE & TRANSACTIONS
# ---------------------------------------------------------
class Compte(models.Model):
    membre = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='compte')
    numero_compte = models.CharField(max_length=15, unique=True, editable=False)
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Compte N° {self.numero_compte} - {self.membre.nom_complet}"

    def save(self, *args, **kwargs):
        if not self.numero_compte:
            while True:
                numero = "".join([str(random.randint(0, 9)) for _ in range(15)])
                if not Compte.objects.filter(numero_compte=numero).exists():
                    self.numero_compte = numero
                    break
        super().save(*args, **kwargs)


class Transaction(models.Model):
    reference = models.CharField(max_length=36, unique=True, editable=False)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='transactions')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    type_transaction = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            today_str = datetime.date.today().strftime('%Y%m%d')
            self.reference = f"TRX-{today_str}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


# ---------------------------------------------------------
# 4. EMPRUNTS ET REMBOURSEMENTS FINANCIERS
# ---------------------------------------------------------
class Emprunt(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='emprunts')
    montant_emprunt = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    taux_interet = models.DecimalField(max_digits=5, decimal_places=2, help_text="En pourcentage (ex: 5 pour 5%)")
    total_a_payer = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False, help_text="Ce qu'il reste à rembourser")
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Emprunt {self.id} - {self.membre.nom_complet} (Reste: {self.balance})"

    def clean(self):
        if not self.pk:
            annee_emprunt = self.date.year if self.date else timezone.now().year
            if not self.membre.est_en_ordre_adhesion(annee=annee_emprunt):
                raise ValidationError("Le membre doit être en ordre d'adhésion pour l'année concernée.")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.full_clean()
            interet = self.montant_emprunt * (self.taux_interet / 100)
            self.total_a_payer = self.montant_emprunt + interet
            self.balance = self.total_a_payer
        super().save(*args, **kwargs)


class Remboursement(models.Model):
    emprunt = models.ForeignKey(Emprunt, on_delete=models.CASCADE, related_name='remboursements')
    montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Remboursement de {self.montant} sur Emprunt {self.emprunt.id}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            emprunt_lie = Emprunt.objects.select_for_update().get(id=self.emprunt_id)
            if self.pk:
                ancien_remboursement = Remboursement.objects.get(pk=self.pk)
                delta = self.montant - ancien_remboursement.montant
            else:
                delta = self.montant

            if delta > emprunt_lie.balance:
                raise ValidationError(f"Le montant du remboursement dépasse la balance restante ({emprunt_lie.balance}).")

            emprunt_lie.balance -= delta
            emprunt_lie.save()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            emprunt_lie = Emprunt.objects.select_for_update().get(id=self.emprunt_id)
            emprunt_lie.balance += self.montant
            emprunt_lie.save()
            super().delete(*args, **kwargs)


# ---------------------------------------------------------
# 5. CANTINE (ARTICLES, CREDIT CANTINE, REMBOURSEMENT)
# ---------------------------------------------------------
class ArticleCantine(models.Model):
    nom = models.CharField(max_length=150)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nom} - {self.prix_unitaire}"


class CreditCantine(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='credits_cantine')
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, editable=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, editable=False, help_text="Reste à payer")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Crédit Cantine N°{self.id} - {self.membre.nom_complet} (Reste: {self.balance})"

    def recalculer_totaux(self):
        """Met à jour le montant total du panier et réajuste la balance."""
        totaux = self.lignes.aggregate(total=models.Sum('prix_total'))['total'] or 0.00
        somme_remboursements = self.remboursements.aggregate(total=models.Sum('montant'))['total'] or 0.00
        
        self.montant_total = totaux
        self.balance = totaux - somme_remboursements
        self.save(update_fields=['montant_total', 'balance'])


class LigneCreditCantine(models.Model):
    """Représente chaque article présent dans le panier de crédit cantine."""
    credit_cantine = models.ForeignKey(CreditCantine, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(ArticleCantine, on_delete=models.PROTECT, related_name='lignes_credit')
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    prix_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Fixe le prix unitaire au prix actuel de l'article au moment du crédit
            self.prix_unitaire = self.article.prix_unitaire
        
        self.prix_total = self.prix_unitaire * self.quantite
        super().save(*args, **kwargs)
        # Met à jour automatiquement la balance du crédit cantine parent
        self.credit_cantine.recalculer_totaux()

    def delete(self, *args, **kwargs):
        credit = self.credit_cantine
        super().delete(*args, **kwargs)
        credit.recalculer_totaux()


class RemboursementCantine(models.Model):
    credit_cantine = models.ForeignKey(CreditCantine, on_delete=models.CASCADE, related_name='remboursements')
    montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Remboursement Cantine de {self.montant} sur Crédit N°{self.credit_cantine.id}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            credit_lie = CreditCantine.objects.select_for_update().get(id=self.credit_cantine_id)
            if self.pk:
                ancien_remboursement = RemboursementCantine.objects.get(pk=self.pk)
                delta = self.montant - ancien_remboursement.montant
            else:
                delta = self.montant

            if delta > credit_lie.balance:
                raise ValidationError(f"Le montant dépasse la dette de cantine restante ({credit_lie.balance}).")

            credit_lie.balance -= delta
            credit_lie.save(update_fields=['balance'])
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            credit_lie = CreditCantine.objects.select_for_update().get(id=self.credit_cantine_id)
            credit_lie.balance += self.montant
            credit_lie.save(update_fields=['balance'])
            super().delete(*args, **kwargs)