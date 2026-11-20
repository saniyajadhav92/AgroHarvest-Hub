from django.contrib import admin

from .models import (
    Product,
    Cart,
    Order,
    OrderItem,
    Contact,
    Wishlist,
    Review,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'price',
        'created_at',
    )

    list_filter = (
        'category',
    )

    search_fields = (
        'name',
        'description',
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'quantity',
        'added_at',
    )

    list_filter = (
        'added_at',
    )

    search_fields = (
        'user__username',
        'product__name',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'full_name',
        'mobile',
        'city',
        'payment_method',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'payment_method',
        'created_at',
    )

    search_fields = (
        'full_name',
        'mobile',
        'city',
        'user__username',
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product',
        'quantity',
        'price',
    )

    search_fields = (
        'product__name',
        'order__user__username',
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'subject',
        'created_at',
    )

    search_fields = (
        'name',
        'email',
        'subject',
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'added_at',
    )

    search_fields = (
        'user__username',
        'product__name',
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'user',
        'rating',
        'created_at',
    )

    list_filter = (
        'rating',
        'created_at',
    )

    search_fields = (
        'product__name',
        'user__username',
        'comment',
    )