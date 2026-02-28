from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control."""

    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('cashier', 'Cashier'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='cashier')

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin_user(self):
        return self.role == 'admin'
