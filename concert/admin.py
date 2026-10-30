from django.contrib import admin
from .models import Concert, ConcertAttending

@admin.register(Concert)
class ConcertAdmin(admin.ModelAdmin):
    list_display = ('concert_name', 'city', 'date', 'duration')
    list_filter = ('city', 'date')
    search_fields = ('concert_name', 'city')

admin.site.register(ConcertAttending)
