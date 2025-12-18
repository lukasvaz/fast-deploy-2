# from django.contrib.auth.models import Group
# from rest_framework import serializers
# from users.models import User


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ("username", "email", "first_name", "last_name")


# class GroupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Group
#         fields = ("name",)


# class RegisterSerializer(serializers.ModelSerializer):
#     password2 = serializers.CharField(write_only=True, required=True)

#     def validate_data(self, data):
#         try:
#             user = User.objects.filter(username=data.get("username"))
#             if len(user) > 0:
#                 raise serializers.ValidationError("Username already exists")
#         except User.DoesNotExist:
#             pass

#         if not data.get("password") or not data.get("password2"):
#             raise serializers.ValidationError("Empty Password")

#         if data.get("password") != data.get("password2"):
#             raise serializers.ValidationError("Mismatch")

#         return data

#     def create(self, validated_data):
#         user = User.objects.create(
#             username=validated_data["username"],
#         )

#         user.set_password(validated_data["password"])
#         user.save()

#         return user

#     class Meta:
#         model = User
#         fields = (
#             "username",
#             "first_name",
#             "last_name",
#             "password",
#             "password2",
#         )
