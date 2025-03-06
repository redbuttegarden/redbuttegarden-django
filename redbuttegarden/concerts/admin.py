from django.contrib import admin

from .models import Ticket, OAuth2Token


class TicketAdmin(admin.ModelAdmin):
    pass

@admin.register(OAuth2Token)
class OAuth2TokenAdmin(admin.ModelAdmin):
    pass


admin.site.register(Ticket)
