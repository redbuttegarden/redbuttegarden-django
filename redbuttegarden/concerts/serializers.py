from rest_framework import serializers

from concerts.models import Concert, ConcertDonorClubPackage, ConcertDonorClubMember
from custom_user.serializers import CustomUserSerializer


class ConcertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concert
        fields = ['name', 'year']


class ConcertDonorClubPackageSerializer(serializers.ModelSerializer):
    concerts = ConcertSerializer()

    class Meta:
        model = ConcertDonorClubPackage
        fields = ['name', 'year', 'concerts']


class ConcertDonorClubMemberSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    packages = ConcertDonorClubPackageSerializer()
    additional_concerts = ConcertSerializer()

    class Meta:
        model = ConcertDonorClubMember
        fields = ['user', 'packages', 'additional_concerts']
