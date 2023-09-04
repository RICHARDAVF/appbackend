from rest_framework import serializers

from .models import UsuarioCredencial
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioCredencial
        fields = '__all__'
