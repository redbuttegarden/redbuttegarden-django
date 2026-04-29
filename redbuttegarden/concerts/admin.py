from django.contrib import admin

from .models import ConcertDonorClubWelcomeListAdd, Ticket, OAuth2Token


class TicketAdmin(admin.ModelAdmin):
    pass

@admin.register(OAuth2Token)
class OAuth2TokenAdmin(admin.ModelAdmin):
    pass


@admin.register(ConcertDonorClubWelcomeListAdd)
class ConcertDonorClubWelcomeListAddAdmin(admin.ModelAdmin):
    list_display = ("member", "list_id", "status", "source", "created_at", "attempted_at", "added_at")
    list_filter = ("status", "source", "list_id")
    search_fields = ("member__user__username", "member__user__email", "list_id", "contact_id")
    readonly_fields = ("created_at", "updated_at", "attempted_at", "added_at")


admin.site.register(Ticket)
