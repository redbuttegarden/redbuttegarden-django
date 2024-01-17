from rest_framework import serializers

from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember, Ticket
from custom_user.serializers import CustomUserSerializer


class ConcertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concert
        fields = '__all__'


class ConcertDonorClubPackageSerializer(serializers.ModelSerializer):
    concerts = ConcertSerializer(many=True)

    class Meta:
        model = ConcertDonorClubPackage
        fields = '__all__'


class ConcertDonorClubMemberSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    packages = ConcertDonorClubPackageSerializer(many=True, allow_null=True)
    additional_concerts = ConcertSerializer(many=True, allow_null=True)

    class Meta:
        model = ConcertDonorClubMember
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
    owner = ConcertDonorClubMemberSerializer(partial=True)
    concert = ConcertSerializer()

    class Meta:
        model = Ticket
        fields = '__all__'
