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
# 5. CREDIT CANTINE & ACHATS EN PANIER
# ---------------------------------------------------------
class ProduitCantine(models.Model):
    nom = models.CharField(max_length=150)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nom} - {self.prix_unitaire} {self.devise.upper()} (Stock: {self.stock})"


class CreditCantine(models.Model):
    membre = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='credits_cantine')
    acompte_initial = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        validators=[MinValueValidator(0.00)],
        help_text="Montant déposé au départ avant de retirer les produits"
    )
    montant_total_panier = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, editable=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, editable=False, help_text="Reste à payer")
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Crédit Cantine {self.id} - {self.membre.nom_complet} (Reste: {self.balance})"

    def clean(self):
        if not self.pk:
            annee_credit = self.date.year if self.date else timezone.now().year
            if not self.membre.est_en_ordre_adhesion(annee=annee_credit):
                raise ValidationError("Le membre doit être en ordre d'adhésion pour l'année concernée.")

    def update_totals(self):
        """ Recalcule le total du panier et la balance restante. """
        total = sum(item.sous_total for item in self.lignes.all())
        self.montant_total_panier = total
        
        # Total déjà remboursé en plus de l'acompte
        total_rembourse = sum(r.montant for r in self.remboursements_cantine.all())
        
        self.balance = (self.montant_total_panier - self.acompte_initial) - total_rembourse
        if self.balance < 0:
            self.balance = 0.00
        
        self.save()


class LigneCreditCantine(models.Model):
    credit_cantine = models.ForeignKey(CreditCantine, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(ProduitCantine, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    prix_unitaire_applique = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    sous_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def clean(self):
        # Vérification du stock disponible
        if not self.pk and self.produit.stock < self.quantite:
            raise ValidationError(f"Stock insuffisant pour {self.produit.nom}. Disponible: {self.produit.stock}")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.pk:
                self.full_clean()
                # Déduire du stock du produit
                self.produit.stock -= self.quantite
                self.produit.save()
                
                # Figer le prix au moment de l'achat
                self.prix_unitaire_applique = self.produit.prix_unitaire

            self.sous_total = self.prix_unitaire_applique * self.quantite
            super().save(*args, **kwargs)
            
            # Mettre à jour la balance globale du panier
            self.credit_cantine.update_totals()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # Remettre la quantité en stock si la ligne est supprimée
            self.produit.stock += self.quantite
            self.produit.save()
            super().delete(*args, **kwargs)
            self.credit_cantine.update_totals()


class RemboursementCantine(models.Model):
    credit_cantine = models.ForeignKey(CreditCantine, on_delete=models.CASCADE, related_name='remboursements_cantine')
    montant = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    devise = models.CharField(max_length=3, choices=DEVISE_CHOICES, default='cdf')
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Remboursement Cantine de {self.montant} sur Crédit #{self.credit_cantine.id}"

    def clean(self):
        if self.montant > self.credit_cantine.balance:
            raise ValidationError(f"Le montant dépasse la balance restante du crédit cantine ({self.credit_cantine.balance}).")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.full_clean()
            super().save(*args, **kwargs)
            self.credit_cantine.update_totals()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            super().delete(*args, **kwargs)
            self.credit_cantine.update_totals()