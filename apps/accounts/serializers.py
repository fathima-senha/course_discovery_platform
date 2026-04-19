from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from .models import StudentProfile, ProviderProfile

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Handles registration for both students and providers.
    Automatically creates the correct profile after user is saved.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "username", "password", "role"]

    def validate_role(self, value):
        # Admin accounts cannot be created via the API
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot register as admin.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Auto-create the correct profile based on role
        if user.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=user)
        elif user.role == User.Role.PROVIDER:
            ProviderProfile.objects.create(user=user, company_name=user.username)

        return user


class LoginSerializer(serializers.Serializer):
    """
    Validates email and password and returns the authenticated user.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        data["user"] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Validates old password and sets a new one.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializes the StudentProfile.
    Includes basic user info (email, username) from the related User.
    """
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "email", "username",
            "bio", "avatar", "location", "website",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "username", "updated_at"]


class ProviderProfileSerializer(serializers.ModelSerializer):
    """
    Serializes the ProviderProfile.
    Includes basic user info from the related User.
    """
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ProviderProfile
        fields = [
            "id", "email", "company_name", "website",
            "description", "logo", "is_verified",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "is_verified", "updated_at"]