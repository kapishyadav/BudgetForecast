from django.contrib.auth.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    # We define 'name' here to catch the "Full Name" field from your React form
    name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('email', 'password', 'name')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        # Check if a user already exists with this email (either in the email OR username column)
        if User.objects.filter(email=value).exists() or User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value

    def create(self, validated_data):
        # We use create_user() because it automatically hashes the password safely!
        # Never use User.objects.create() for users, or passwords will be saved as plain text.
        user = User.objects.create_user(
            username=validated_data['email'], # Use email as the username
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('name', '') # Save the full name into the first_name field
        )
        return user