from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),

    path('products/', views.products, name='products'),

    path('crop-recommendation/', views.crop_recommendation, name='crop_recommendation'),

    path('disease-detection/', views.disease_detection, name='disease_detection'),

    path('about/', views.about, name='about'),

    path('contact/', views.contact, name='contact'),

    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('product/<slug:slug>/review/', views.add_review, name='add_review'),

    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),

    path('wishlist/', views.wishlist, name='wishlist'),

    path('reviews/', views.reviews, name='reviews'),

    path('wishlist/add/<slug:slug>/', views.add_to_wishlist, name='add_to_wishlist'),

    path('wishlist/remove/<int:id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('cart/', views.cart, name='cart'),

    path('increase/<int:id>/', views.increase_quantity, name='increase_quantity'),

    path('decrease/<int:id>/', views.decrease_quantity, name='decrease_quantity'),

    path('remove-cart/<int:id>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),

    path('place-order/', views.place_order, name='place_order'),

    path('my-orders/', views.my_orders, name='my_orders'),

    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('login/', views.login_view, name='login'),

    path('signup/', views.signup_view, name='signup'),

    path('logout/', views.logout_view, name='logout'),

    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
]