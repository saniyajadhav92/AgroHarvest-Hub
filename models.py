from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):

    CATEGORY_CHOICES = [
        ('Seeds', 'Seeds'),
        ('Fertilizer', 'Fertilizer'),
        ('Tools', 'Tools'),
        ('Irrigation', 'Irrigation'),
    ]

    # =========================
    # PRODUCT BASIC DETAILS
    # =========================

    name = models.CharField(max_length=200)

    # Marathi and Hindi Product Names
    name_mr = models.CharField(
        max_length=200,
        blank=True
    )

    name_hi = models.CharField(
        max_length=200,
        blank=True
    )

    description = models.TextField()

    # Marathi and Hindi Descriptions
    description_mr = models.TextField(
        blank=True
    )

    description_hi = models.TextField(
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Seeds'
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Cart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Order(models.Model):

    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=200)

    mobile = models.CharField(max_length=15)

    address = models.TextField()

    city = models.CharField(max_length=100)

    pin_code = models.CharField(max_length=10)

    payment_method = models.CharField(
        max_length=50,
        default='Cash on Delivery'
    )

    payment_status = models.CharField(
        max_length=20,
        default='Pending'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Confirmed'
    )

    estimated_delivery = models.CharField(
        max_length=50,
        default='3–5 Business Days'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


# =========================
# ORDER ITEMS
# =========================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.order} - {self.product.name}"


class Contact(models.Model):

    name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(max_length=200)

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Wishlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# =========================
# PRODUCT REVIEW & RATING
# =========================

class Review(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.PositiveIntegerField()

    comment = models.TextField()

    # Customer uploaded product photo
    photo = models.ImageField(
        upload_to='reviews/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.rating} ⭐"