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


class ForecastTriggerSerializer(serializers.Serializer):
    """Validates incoming HTTP data for a standard forecast trigger."""
    # Using CharField instead of UUIDField just in case dataset_id is sometimes a string ID
    dataset_id = serializers.CharField(required=True)
    forecast_type = serializers.CharField(default="overall_aggregate")
    granularity = serializers.CharField(default="monthly")

    # Optional cascading filters
    account_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    service_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    bu_code = serializers.IntegerField(required=False, allow_null=True)
    segment_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class CustomScenarioSerializer(serializers.Serializer):
    """Validates incoming HTTP data for a custom hyperparameter scenario."""
    dataset_id = serializers.CharField(required=True)

    # User selects which algorithm to use
    model_name = serializers.ChoiceField(
        choices=["prophet", "catboost", "xgboost"],
        default="prophet"
    )

    # Accepts an arbitrary dictionary of settings!
    hyperparameters = serializers.JSONField(default=dict)

    forecast_type = serializers.CharField(default="overall_aggregate")
    granularity = serializers.CharField(default="monthly")

    # Optional cascading filters (Crucial for tree-based models on specific slices)
    account_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    service_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    bu_code = serializers.IntegerField(required=False, allow_null=True)
    segment_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
