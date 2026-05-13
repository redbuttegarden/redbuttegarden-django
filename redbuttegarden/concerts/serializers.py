from rest_framework import serializers

from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember, Ticket
from custom_user.serializers import CustomUserSerializer


class ConcertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concert
        fields = [
            'etix_id',
            'name',
            'begin',
            'end',
            'doors_before_event_time_minutes',
            'image_url',
        ]


class ConcertDonorClubPackageSerializer(serializers.ModelSerializer):
    concerts = ConcertSerializer(many=True)

    class Meta:
        model = ConcertDonorClubPackage
        fields = ['id', 'name', 'year', 'concerts']


class ConcertDonorClubMemberSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    packages = ConcertDonorClubPackageSerializer(many=True, allow_null=True)

    class Meta:
        model = ConcertDonorClubMember
        fields = ['id', 'user', 'phone_number', 'packages', 'active']


class TicketOwnerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = ConcertDonorClubMember
        fields = ['id', 'user', 'active']


class TicketSerializer(serializers.ModelSerializer):
    owner = TicketOwnerSerializer(partial=True)
    concert = ConcertSerializer()

    class Meta:
        model = Ticket
        fields = ['pk', 'owner', 'concert', 'package', 'order_id', 'etix_id', 'barcode']
