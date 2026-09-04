from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

admin.site.register(User, UserAdmin)
# admin.site.register(Utilisateur)
# admin.site.register(TypeMember)
# admin.site.register(Member)
# admin.site.register(Adhesion)
# admin.site.register(Social)
# admin.site.register(Compte) 
# admin.site.register(Transaction)
# admin.site.register(Emprunt)
# admin.site.register(Remboursement)
