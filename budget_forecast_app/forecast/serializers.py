from django.contrib.auth.models import User
from rest_framework import serializers
from .models import CloudIntegration, ForecastDataset


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
    # Optuna fields
    tune_hyperparameters = serializers.BooleanField(default=False)
    tuning_trials = serializers.IntegerField(default=20, min_value=1, max_value=100, required=False)

class CloudIntegrationSerializer:
    """
        Serializer for CloudIntegration model.
        Handles secure serialization/deserialization of cloud credentials.
    """
    # A read-only helper field so the React frontend knows if credentials exist
    is_configured = serializers.SerializerMethodField(read_only=True)

    # Allows the frontend to pass 'dataset_id': 'uuid-123' directly in the POST payload
    dataset_id = serializers.PrimaryKeyRelatedField(
        queryset=ForecastDataset.objects.all(),
        source='dataset',
        write_only=True
    )

    class Meta:
        model = CloudIntegration
        # Note: Adjust these field names to match exactly what is in your models.py
        fields = [
            'id',
            'dataset_id',  # Maps to the dataset ForeignKey
            'provider',
            'account_id',
            'is_active',
            'last_synced_at',  # Crucial for the frontend status indicator
            'is_configured',

            # Credential fields matching models.py exact names:
            'access_key',  # Used for Azure Client ID
            'secret_key',  # Used for Azure Client Secret
            'role_arn',  # Used for AWS Role ARN
            'tenant_id',  # Used for Azure Tenant ID
            'gcp_service_account_json',
            'gcp_table_id'  # Required for GCP BigQuery queries
        ]

        # CRUCIAL SECURITY MEASURE:
        # Ensure sensitive fields are NEVER returned in GET requests to the browser.
        # The frontend can write to them via POST/PUT/PATCH, but cannot read them back.
        extra_kwargs = {
            'access_key': {'write_only': True, 'required': False},
            'secret_key': {'write_only': True, 'required': False},
            'role_arn': {'write_only': True, 'required': False},
            'tenant_id': {'write_only': True, 'required': False},
            'gcp_service_account_json': {'write_only': True, 'required': False},
            'provider': {'required': True},
            'account_id': {'required': True},
        }

    def get_is_configured(self, obj):
        """
        Evaluates whether the integration has the minimum required credentials saved.
        """
        provider = str(obj.provider).upper()

        if provider == 'AWS' and obj.role_arn:
            return True
        if provider == 'AZURE' and obj.tenant_id and obj.access_key and obj.secret_key:
            return True
        if provider == 'GCP' and obj.gcp_service_account_json and obj.gcp_table_id:
            return True

        return False

    def validate(self, data):
        """
        Object-level validation to ensure the correct credentials are provided
        based on the selected cloud provider.
        """
        # If this is a partial update (PATCH), 'provider' might not be in 'data'.
        # We fall back to the existing object's provider.
        provider = data.get('provider', getattr(self.instance, 'provider', None))

        if not provider:
            raise serializers.ValidationError({"provider": "Provider type is required."})

        provider = str(provider).upper()

        if provider == 'AZURE':
            # Azure needs all three pieces to form a connection
            tenant = data.get('azure_tenant_id') or getattr(self.instance, 'azure_tenant_id', None)
            client = data.get('azure_client_id') or getattr(self.instance, 'azure_client_id', None)
            secret = data.get('azure_client_secret') or getattr(self.instance, 'azure_client_secret', None)

            if not all([tenant, client, secret]):
                raise serializers.ValidationError(
                    "Azure integrations require Tenant ID, Client ID, and Client Secret."
                )

        elif provider == 'AWS':
            arn = data.get('aws_role_arn') or getattr(self.instance, 'aws_role_arn', None)
            if not arn:
                raise serializers.ValidationError("AWS integrations require a Cross-Account Role ARN.")

        elif provider == 'GCP':
            json_file = data.get('gcp_service_account_json') or getattr(self.instance, 'gcp_service_account_json', None)
            if not json_file:
                raise serializers.ValidationError("GCP integrations require the Service Account JSON.")

        return data
