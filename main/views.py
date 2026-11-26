from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

from .models import (
    Product,
    Cart,
    Order,
    OrderItem,
    Contact,
    Wishlist,
    Review
)


# =========================
# HOME / LANDING
# =========================
def landing(request):
    reviews = Review.objects.select_related(
        'user',
        'product'
    ).order_by('-created_at')[:3]

    featured_products = Product.objects.all().order_by('-created_at')[:4]

    return render(
        request,
        'main/landing.html',
        {
            'reviews': reviews,
            'featured_products': featured_products
        }
    )


# =========================
# ABOUT US
# =========================
def about(request):
    return render(request, 'main/about.html')


# =========================
# PRODUCTS
# =========================
def products(request):
    category = request.GET.get('category')
    search = request.GET.get('search')

    products_queryset = Product.objects.all().order_by('-created_at')

    if category:
        products_queryset = products_queryset.filter(
            category=category
        )

    if search:
        products_queryset = products_queryset.filter(
            name__icontains=search
        )

    for product in products_queryset:
        product.slug = slugify(product.name)

    return render(
        request,
        'main/products.html',
        {
            'products': products_queryset,
            'selected_category': category,
            'search_query': search
        }
    )


# =========================
# PRODUCT DETAIL
# =========================
def product_detail(request, slug):
    product = None

    for item in Product.objects.all():
        if slugify(item.name) == slug:
            product = item
            break

    if not product:
        return redirect('/products/')

    product.slug = slugify(product.name)

    in_wishlist = False

    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

    return render(
        request,
        'main/product_detail.html',
        {
            'product': product,
            'in_wishlist': in_wishlist
        }
    )


# =========================
# ADD TO CART
# =========================
@login_required(login_url='/login/')
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('/cart/')


# =========================
# CART
# =========================
@login_required(login_url='/login/')
def cart(request):
    cart_items = Cart.objects.filter(
        user=request.user
    ).select_related('product')

    total = sum(
        item.total_price()
        for item in cart_items
    )

    return render(
        request,
        'main/cart.html',
        {
            'cart_items': cart_items,
            'total': total,
            'total_price': total
        }
    )


# =========================
# INCREASE QUANTITY
# =========================
@login_required(login_url='/login/')
def increase_quantity(request, id):
    cart_item = Cart.objects.filter(
        id=id,
        user=request.user
    ).first()

    if cart_item:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('/cart/')


# =========================
# DECREASE QUANTITY
# =========================
@login_required(login_url='/login/')
def decrease_quantity(request, id):
    cart_item = Cart.objects.filter(
        id=id,
        user=request.user
    ).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('/cart/')


# =========================
# REMOVE FROM CART
# =========================
@login_required(login_url='/login/')
def remove_from_cart(request, id):
    Cart.objects.filter(
        id=id,
        user=request.user
    ).delete()

    return redirect('/cart/')


# =========================
# CHECKOUT
# =========================
@login_required(login_url='/login/')
def checkout(request):
    cart_items = Cart.objects.filter(
        user=request.user
    ).select_related('product')

    if not cart_items.exists():
        return redirect('/products/')

    total = sum(
        item.total_price()
        for item in cart_items
    )

    return render(
        request,
        'main/checkout.html',
        {
            'cart_items': cart_items,
            'total': total
        }
    )


# =========================
# PLACE ORDER
# =========================
@login_required(login_url='/login/')
def place_order(request):
    if request.method != 'POST':
        return redirect('/checkout/')

    cart_items = Cart.objects.filter(
        user=request.user
    ).select_related('product')

    if not cart_items.exists():
        return redirect('/products/')

    full_name = request.POST.get('full_name', '').strip()
    mobile = request.POST.get('mobile', '').strip()
    address = request.POST.get('address', '').strip()
    city = request.POST.get('city', '').strip()
    pin_code = request.POST.get('pin_code', '').strip()

    payment_method = request.POST.get(
        'payment_method',
        'Cash on Delivery'
    )

    total = sum(
        item.total_price()
        for item in cart_items
    )

    if payment_method == 'Online Payment':
        payment_status = 'Paid'
    else:
        payment_status = 'Cash on Delivery'

    if not all([
        full_name,
        mobile,
        address,
        city,
        pin_code
    ]):
        return render(
            request,
            'main/checkout.html',
            {
                'cart_items': cart_items,
                'total': total,
                'error': 'Please fill all required fields.'
            }
        )

    # CREATE ORDER
    order = Order.objects.create(
        user=request.user,
        full_name=full_name,
        mobile=mobile,
        address=address,
        city=city,
        pin_code=pin_code,
        payment_method=payment_method,
        payment_status=payment_status,
        status='Confirmed'
    )

    # CREATE ORDER ITEMS
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )

    # CLEAR CART
    cart_items.delete()

    # युजरचा सिरियल नंबर मोजण्यासाठी (उदा. #11)
    user_order_number = Order.objects.filter(
        user=request.user,
        created_at__lte=order.created_at
    ).count()

    # ORDER SUCCESS
    return render(
        request,
        'main/order_success.html',
        {
            'order': order,
            'total': total,
            'order_number': user_order_number,
        }
    )


# =========================
# MY ORDERS
# =========================
@login_required(login_url='/login/')
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items__product'
    ).order_by('-created_at')

    for order in orders:
        order.items_total = sum(
            item.total_price()
            for item in order.items.all()
        )
        order.has_items = order.items.exists()

    return render(
        request,
        'main/my_orders.html',
        {
            'orders': orders
        }
    )


# =========================
# CANCEL ORDER (DIRECT)
# =========================
@login_required(login_url='/login/')
def cancel_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

        if order.status in ['Confirmed', 'Packed']:
            order.status = 'Cancelled'
            order.save()
            messages.success(
                request,
                f'Order #{order.id} has been cancelled.'
            )
        else:
            messages.warning(
                request,
                'This order can no longer be cancelled.'
            )

    return redirect('/my-orders/')


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            next_url = request.POST.get('next')

            if next_url:
                return redirect(next_url)

            return redirect('/')

        return render(
            request,
            'registration/login.html',
            {
                'error': 'Invalid username or password.',
                'next': request.POST.get('next', '')
            }
        )

    next_url = request.GET.get('next', '')

    return render(
        request,
        'registration/login.html',
        {
            'next': next_url
        }
    )


# =========================
# SIGNUP
# =========================
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username or not password:
            return render(
                request,
                'registration/signup.html',
                {
                    'error': 'Username and password are required.'
                }
            )

        if password != confirm_password:
            return render(
                request,
                'registration/signup.html',
                {
                    'error': 'Passwords do not match.'
                }
            )

        if User.objects.filter(
            username=username
        ).exists():
            return render(
                request,
                'registration/signup.html',
                {
                    'error': 'Username already exists.'
                }
            )

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect('/login/')

    return render(
        request,
        'registration/signup.html'
    )


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect('/')


# =========================
# CONTACT
# =========================
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        messages.success(
            request,
            'Your message has been sent successfully! 📩'
        )

        return redirect('contact')

    return render(
        request,
        'main/contact.html'
    )


# =========================
# WISHLIST
# =========================
def add_to_wishlist(request, slug):
    if not request.user.is_authenticated:
        return redirect(
            f'/login/?next=/wishlist/add/{slug}/'
        )

    product = None

    for item in Product.objects.all():
        if slugify(item.name) == slug:
            product = item
            break

    if not product:
        return redirect('/products/')

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect('/wishlist/')


@login_required(login_url='/login/')
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        'product'
    ).order_by('-added_at')

    return render(
        request,
        'main/wishlist.html',
        {
            'wishlist_items': wishlist_items
        }
    )


@login_required(login_url='/login/')
def remove_from_wishlist(request, id):
    Wishlist.objects.filter(
        id=id,
        user=request.user
    ).delete()

    return redirect('/wishlist/')


# =========================
# PRODUCT REVIEWS & RATINGS
# =========================
def add_review(request, slug):
    if not request.user.is_authenticated:
        return redirect(
            f'/login/?next=/product/{slug}/'
        )

    product = None

    for item in Product.objects.all():
        if slugify(item.name) == slug:
            product = item
            break

    if not product:
        return redirect('/products/')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        photo = request.FILES.get('photo')

        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=int(rating),
                comment=comment,
                photo=photo
            )

    return redirect(f'/product/{slug}/')


# =========================
# DASHBOARD
# =========================
@login_required(login_url='/login/')
def dashboard(request):
    total_orders = Order.objects.filter(
        user=request.user
    ).count()

    confirmed_orders = Order.objects.filter(
        user=request.user,
        status='Confirmed'
    ).count()

    delivered_orders = Order.objects.filter(
        user=request.user,
        status='Delivered'
    ).count()

    wishlist_count = Wishlist.objects.filter(
        user=request.user
    ).count()

    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'total_orders': total_orders,
        'confirmed_orders': confirmed_orders,
        'delivered_orders': delivered_orders,
        'wishlist_count': wishlist_count,
        'recent_orders': recent_orders,
    }

    return render(
        request,
        'main/dashboard.html',
        context
    )


# =========================
# SMART CROP RECOMMENDATION
# =========================
def crop_recommendation(request):
    recommendation = None
    reason = None
    recommended_products = []

    if request.method == 'POST':
        season = request.POST.get('season')
        soil = request.POST.get('soil')
        water = request.POST.get('water')

        if season == 'Kharif':
            if soil == 'Black Soil' and water in ['Medium', 'High']:
                recommendation = 'Cotton'
                reason = 'Cotton is suitable for Black Soil and Kharif season.'
            elif soil == 'Loamy Soil' and water == 'High':
                recommendation = 'Rice'
                reason = 'Rice requires good water availability and grows well in Kharif season.'
            elif soil == 'Sandy Soil':
                recommendation = 'Groundnut'
                reason = 'Groundnut can perform well in Sandy Soil during Kharif season.'
            else:
                recommendation = 'Soybean'
                reason = 'Soybean is a suitable Kharif crop for a wide range of soils.'

        elif season == 'Rabi':
            if soil == 'Black Soil' and water in ['Medium', 'High']:
                recommendation = 'Wheat'
                reason = 'Wheat grows well in Black Soil during Rabi season.'
            elif soil == 'Loamy Soil':
                recommendation = 'Chickpea'
                reason = 'Chickpea is suitable for Loamy Soil during Rabi season.'
            elif soil == 'Sandy Soil':
                recommendation = 'Mustard'
                reason = 'Mustard can grow well in lighter soils during Rabi season.'
            else:
                recommendation = 'Chickpea'
                reason = 'Chickpea is a suitable Rabi crop.'

        elif season == 'Summer':
            if water == 'High':
                recommendation = 'Watermelon'
                reason = 'Watermelon requires good water availability during summer.'
            elif soil == 'Sandy Soil' and water == 'Medium':
                recommendation = 'Groundnut'
                reason = 'Groundnut can perform well in Sandy Soil with moderate water.'
            else:
                recommendation = 'Moong'
                reason = 'Moong is a short-duration crop suitable for summer cultivation.'

        if recommendation:
            keywords = []
            if recommendation == 'Cotton':
                keywords = ['cotton', 'fertilizer']
            elif recommendation == 'Rice':
                keywords = ['rice', 'fertilizer']
            elif recommendation == 'Groundnut':
                keywords = ['groundnut', 'fertilizer']
            elif recommendation == 'Soybean':
                keywords = ['soybean', 'fertilizer']
            elif recommendation == 'Wheat':
                keywords = ['wheat', 'fertilizer']
            elif recommendation == 'Chickpea':
                keywords = ['chickpea', 'fertilizer']
            elif recommendation == 'Mustard':
                keywords = ['mustard', 'fertilizer']
            elif recommendation == 'Watermelon':
                keywords = ['watermelon', 'fertilizer']
            elif recommendation == 'Moong':
                keywords = ['moong', 'fertilizer']

            for product in Product.objects.all():
                product_name = product.name.lower()
                if any(keyword in product_name for keyword in keywords):
                    product.slug = slugify(product.name)
                    recommended_products.append(product)

    return render(
        request,
        'main/crop_recommendation.html',
        {
            'recommendation': recommendation,
            'reason': reason,
            'recommended_products': recommended_products
        }
    )


# =========================
# PLANT DISEASE DETECTION
# =========================
def disease_detection(request):
    if request.method == 'POST':
        crop = request.POST.get('crop')
        disease = request.POST.get('disease')
        plant_image = request.FILES.get('plant_image')
        image_url = None

        if plant_image:
            fs = FileSystemStorage()
            filename = fs.save(
                plant_image.name,
                plant_image
            )
            image_url = fs.url(filename)

        symptoms = (
            "Brown spots and dark lesions may appear "
            "on the plant leaves."
        )

        treatment = (
            "Remove affected leaves, maintain proper air circulation "
            "and use suitable crop protection treatment."
        )

        if crop == "Tomato":
            if disease == "Early Blight":
                symptoms = (
                    "Brown circular spots with dark rings may appear "
                    "on older tomato leaves. Leaves may gradually turn yellow."
                )
                treatment = (
                    "Remove infected leaves, avoid overhead watering, "
                    "maintain proper air circulation and use suitable "
                    "fungicide as recommended by an agricultural expert."
                )
            elif disease == "Late Blight":
                symptoms = (
                    "Dark water-soaked spots may appear on leaves and "
                    "stems. In humid conditions the disease can spread quickly."
                )
                treatment = (
                    "Remove severely affected plant parts, avoid excess "
                    "moisture on leaves and use suitable crop protection "
                    "treatment."
                )
            elif disease == "Leaf Mold":
                symptoms = (
                    "Yellow patches may appear on the upper surface of "
                    "leaves with olive-green or brown fungal growth underneath."
                )
                treatment = (
                    "Improve ventilation, reduce leaf moisture and remove "
                    "severely affected leaves."
                )

        elif crop == "Potato":
            if disease == "Early Blight":
                symptoms = (
                    "Dark brown spots with concentric rings may appear "
                    "on potato leaves."
                )
                treatment = (
                    "Remove affected leaves, maintain proper field hygiene "
                    "and use suitable fungicide according to expert advice."
                )
            elif disease == "Late Blight":
                symptoms = (
                    "Large dark brown or black patches may appear on "
                    "potato leaves and stems."
                )
                treatment = (
                    "Remove infected plant material, avoid excessive moisture "
                    "and use recommended disease-control treatment."
                )

        elif crop == "Cotton":
            if disease == "Leaf Spot":
                symptoms = (
                    "Small brown or dark spots may develop on cotton leaves "
                    "and can increase in size over time."
                )
                treatment = (
                    "Remove severely affected leaves, maintain field hygiene "
                    "and use suitable crop protection treatment."
                )
            elif disease == "Bacterial Blight":
                symptoms = (
                    "Water-soaked or dark lesions may appear on cotton leaves. "
                    "The affected areas may become brown and dry."
                )
                treatment = (
                    "Remove severely affected plant parts, maintain good field "
                    "hygiene and follow recommended bacterial disease management."
                )

        recommended_products = []

        if crop == "Tomato":
            keywords = ["tomato", "fertilizer", "seed"]
        elif crop == "Potato":
            keywords = ["potato", "fertilizer", "seed"]
        elif crop == "Cotton":
            keywords = ["cotton", "fertilizer", "seed"]
        else:
            keywords = ["fertilizer"]

        for product in Product.objects.all():
            product_name = product.name.lower()
            if any(keyword in product_name for keyword in keywords):
                recommended_products.append(product)

        return render(
            request,
            'main/disease_result.html',
            {
                'image_url': image_url,
                'crop': crop,
                'disease': disease,
                'symptoms': symptoms,
                'treatment': treatment,
                'recommended_products': recommended_products,
            }
        )

    return render(
        request,
        'main/disease_detection.html'
    )


# =========================
# REVIEWS
# =========================
def reviews(request):
    reviews = Review.objects.select_related(
        'product',
        'user'
    ).order_by('-created_at')

    return render(
        request,
        'main/reviews.html',
        {'reviews': reviews}
    )


def _call_gemini_rest(api_key: str, model: str, prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 450,
            "temperature": 0.4,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=18) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    candidates = body.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
    return "".join(texts).strip()


# =========================
# AI ASSISTANT
# =========================
def ai_assistant(request):
    answer = None
    question = ""
    chat_history = request.session.get("ai_chat_history", [])[-2:]

    if request.method == "POST" and "clear_chat" in request.POST:
        request.session["ai_chat_history"] = []
        request.session.modified = True
        return render(
            request,
            "main/ai_assistant.html",
            {
                "answer": None,
                "question": "",
                "chat_history": [],
            }
        )

    if request.method == "POST":
        question = request.POST.get("question", "").strip()

        if question:
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()

            if not api_key:
                error_msg = (
                    "GEMINI_API_KEY सेट केलेली नाही. कृपया Render च्या Environment Variables मध्ये "
                    "GEMINI_API_KEY जोडून सेवा पुन्हा सुरू करा."
                )
                chat_history.append({"question": question, "answer": error_msg})
                request.session["ai_chat_history"] = chat_history[-2:]
                request.session.modified = True

                return render(
                    request,
                    "main/ai_assistant.html",
                    {
                        "answer": error_msg,
                        "question": question,
                        "chat_history": chat_history,
                    }
                )

            product_rows = Product.objects.values_list("name", "category", "price")[:12]
            product_list = "\n".join(
                f"- {name} | {category} | ₹{price}"
                for name, category, price in product_rows
            )

            prompt = f"""You are AgroHarvest AI, a smart farming assistant for AgroHarvest Hub.
Reply in Marathi if the question is in Marathi, Hindi if in Hindi, English if in English, or match mixed language.
Give concise, clear, practical agriculture answers.
Recommend at most 3 relevant products only from this list (exact name and price):
{product_list}

Do not invent products, prices, or unsafe chemical dosages.

Question: {question}"""

            try:
                answer = _call_gemini_rest(
                    api_key=api_key,
                    model="gemini-3.8-flash",
                    prompt=prompt,
                )
                if not answer:
                    answer = "उत्तर जनरेट होऊ शकले नाही. कृपया पुन्हा प्रश्न विचारा."

            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                if e.code == 503 or "UNAVAILABLE" in err_body:
                    answer = "सध्या AI सर्व्हरवर खूप जास्त मागणी आहे. कृपया काही सेकंदांनी पुन्हा प्रयत्न करा."
                else:
                    answer = f"AI उत्तर देताना तांत्रिक अडचण आली आहे. तपशील: HTTP {e.code} {err_body[:150]}"

            except Exception as e:
                print("GEMINI ERROR:", repr(e))
                err_msg = str(e)
                if "timed out" in err_msg.lower():
                    answer = "उत्तर येण्यास वेळ लागत आहे. कृपया काही सेकंदांनी पुन्हा प्रयत्न करा."
                else:
                    answer = f"AI उत्तर देताना तांत्रिक अडचण आली आहे. तपशील: {err_msg[:180]}"

            chat_history.append({"question": question, "answer": answer})
            request.session["ai_chat_history"] = chat_history[-2:]
            request.session.modified = True

    return render(
        request,
        "main/ai_assistant.html",
        {
            "answer": answer,
            "question": question,
            "chat_history": chat_history,
        }
    )
