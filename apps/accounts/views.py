from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import StudentProfile, ProviderProfile
from .serializers import (
    UserRegisterSerializer,
    LoginSerializer,
    StudentProfileSerializer,
    ProviderProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


# ─── Helpers ────────────────────────────────────────────────────────────────

def get_tokens_for_user(user):
    """Returns a dict with refresh and access JWT tokens for a given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ─── Auth Views ─────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """
    POST /api/accounts/register/
    Registers a new user (student or provider).
    Creates the corresponding profile automatically.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "Account created successfully.",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                    },
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/accounts/login/
    Logs in a user with email and password.
    Returns JWT access and refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "Login successful.",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                    },
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/accounts/logout/
    Blacklists the refresh token to log the user out.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(APIView):
    """
    POST /api/accounts/change-password/
    Allows a logged-in user to change their password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Student Profile Views ───────────────────────────────────────────────────

class StudentProfileView(APIView):
    """
    GET  /api/accounts/student/profile/  — retrieve own profile
    PUT  /api/accounts/student/profile/  — update own profile
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return StudentProfile.objects.get(user=self.request.user)
        except StudentProfile.DoesNotExist:
            return None

    def get(self, request):
        profile = self.get_object()
        if not profile:
            return Response(
                {"error": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StudentProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        profile = self.get_object()
        if not profile:
            return Response(
                {"error": "Student profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StudentProfileSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicStudentProfileView(APIView):
    """
    GET /api/accounts/student/<int:pk>/
    Public view of a student profile — visible to anyone.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related("user").get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response(
                {"error": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StudentProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Provider Profile Views ──────────────────────────────────────────────────

class ProviderProfileView(APIView):
    """
    GET  /api/accounts/provider/profile/  — retrieve own profile
    PUT  /api/accounts/provider/profile/  — update own profile
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return ProviderProfile.objects.get(user=self.request.user)
        except ProviderProfile.DoesNotExist:
            return None

    def get(self, request):
        profile = self.get_object()
        if not profile:
            return Response(
                {"error": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProviderProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        profile = self.get_object()
        if not profile:
            return Response(
                {"error": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProviderProfileSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicProviderProfileView(APIView):
    """
    GET /api/accounts/provider/<int:pk>/
    Public view of a provider profile — visible to anyone.
    Shows the provider's info and is used on the course listing page.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            profile = ProviderProfile.objects.select_related("user").get(pk=pk)
        except ProviderProfile.DoesNotExist:
            return Response(
                {"error": "Provider not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProviderProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)