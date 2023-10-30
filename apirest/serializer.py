from rest_framework import serializers

from .models import UsuarioCredencial,VersionApp
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioCredencial
        fields = '__all__'
class VersionAppSerialiser(serializers.ModelSerializer):
    class Meta:
        model = VersionApp
        fields = '__all__'