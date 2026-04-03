from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from urllib.parse import quote
from .models import Product, Cart, Order, OrderItem, ReturnRequest, CustomUser

# ==================== PUBLIC VIEWS ====================

def home(request):
    products = Product.objects.all().order_by('-created_at')
    cart_count = 0
    if request.user.is_authenticated and not request.user.is_staff:
        cart_count = Cart.objects.filter(user=request.user).count()
    return render(request, 'gift/home.html', {'products': products, 'cart_count': cart_count})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('signup')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('signup')
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            mobile=mobile
        )
        login(request, user)
        messages.success(request, 'Signup successful! Welcome to The Hamper Hub!')
        return redirect('home')
    
    return render(request, 'gift/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Admin hardcoded login
        if username == 'admin' and password == 'admin123':
            try:
                admin_user = CustomUser.objects.get(username='admin')
                if not admin_user.is_staff:
                    admin_user.is_staff = True
                    admin_user.is_superuser = True
                    admin_user.save()
            except CustomUser.DoesNotExist:
                admin_user = CustomUser.objects.create_superuser(
                    username='admin',
                    email='admin@thehamperhub.com',
                    password='admin123',
                    mobile='9999999999'
                )
            login(request, admin_user)
            messages.success(request, 'Admin logged in successfully!')
            return redirect('admin_dashboard')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'gift/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

# ==================== CART VIEWS ====================

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.error(request, f'Sorry, {product.name} is out of stock!')
        return redirect('home')
    
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        if cart_item.quantity + 1 <= product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Added another {product.name} to cart!')
        else:
            messages.error(request, f'Sorry, only {product.stock} items available!')
    else:
        messages.success(request, f'{product.name} added to cart!')
    
    return redirect('cart')

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'gift/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0 and quantity <= cart_item.product.stock:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated!')
        elif quantity > cart_item.product.stock:
            messages.error(request, f'Sorry, only {cart_item.product.stock} items available!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart')

# ==================== CHECKOUT & ORDERS ====================

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('cart')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        
        # Validation
        if not all([full_name, email, mobile, address, city, pincode]):
            messages.error(request, 'Please fill all fields!')
            return redirect('checkout')
        
        total_amount = sum(item.total_price() for item in cart_items)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            mobile=mobile,
            address=address,
            city=city,
            pincode=pincode,
            total_amount=total_amount,
            status='pending'
        )
        
        # Create order items and reduce stock
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()
        
        # Clear cart
        cart_items.delete()
        
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('my_orders')
    
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'gift/checkout.html', {'cart_items': cart_items, 'total': total})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'gift/my_orders.html', {'orders': orders})

# ==================== RETURN REQUESTS ====================

@login_required
def request_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order is delivered
    if order.status != 'delivered':
        messages.error(request, 'Return request can only be raised for delivered orders!')
        return redirect('my_orders')
    
    # Check if return request already exists
    if ReturnRequest.objects.filter(order=order).exists():
        messages.error(request, 'Return request already submitted for this order!')
        return redirect('my_orders')
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        ReturnRequest.objects.create(
            order=order, 
            user=request.user, 
            reason=reason,
            status='pending'
        )
        messages.success(request, 'Return request submitted successfully! Our team will contact you soon.')
        return redirect('my_orders')
    
    return render(request, 'gift/request_return.html', {'order': order})

# ==================== ADMIN VIEWS ====================

@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_products = Product.objects.count()
    total_users = CustomUser.objects.count()
    pending_returns = ReturnRequest.objects.filter(status='pending').count()
    
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    context = {
        'todays_orders': todays_orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'total_users': total_users,
        'pending_returns': pending_returns,
        'recent_orders': recent_orders,
    }
    return render(request, 'gift/admin_dashboard.html', context)

@staff_member_required
def admin_users(request):
    users = CustomUser.objects.all()
    return render(request, 'gift/admin_users.html', {'users': users})

@staff_member_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'gift/admin_orders.html', {'orders': orders})

@staff_member_required
def admin_update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        old_status = order.status
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        
        # Send WhatsApp message when order is delivered
        if new_status == 'delivered' and old_status != 'delivered':
            send_whatsapp_delivery_message(order)
            messages.success(request, f'Order #{order.id} status updated to {new_status} and WhatsApp notification sent!')
        else:
            messages.success(request, f'Order #{order.id} status updated to {new_status}!')
    
    return redirect('admin_orders')

@staff_member_required
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'gift/admin_products.html', {'products': products})

@staff_member_required
def admin_create_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        stock = request.POST.get('stock', 0)
        image = request.FILES.get('image')
        
        if name and price and description:
            Product.objects.create(
                name=name,
                price=price,
                description=description,
                stock=stock,
                image=image
            )
            messages.success(request, 'Product created successfully!')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please fill all required fields!')
    
    return render(request, 'gift/admin_create_product.html')

@staff_member_required
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        product.stock = request.POST.get('stock')
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('admin_products')
    
    return render(request, 'gift/admin_edit_product.html', {'product': product})

@staff_member_required
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully!')
    return redirect('admin_products')

@staff_member_required
def admin_returns(request):
    returns = ReturnRequest.objects.all().order_by('-created_at')
    return render(request, 'gift/admin_returns.html', {'returns': returns})

@staff_member_required
def admin_update_return_status(request, return_id):
    return_req = get_object_or_404(ReturnRequest, id=return_id)
    if request.method == 'POST':
        return_req.status = request.POST.get('status')
        return_req.save()
        messages.success(request, f'Return request #{return_req.id} status updated to {return_req.status}!')
    return redirect('admin_returns')

# ==================== WHATSAPP MESSAGE FUNCTIONS ====================

def send_whatsapp_delivery_message(order):
    """Send WhatsApp message to customer when order is delivered"""
    customer_name = order.full_name
    customer_mobile = order.mobile
    order_id = order.id
    order_date = order.created_at.strftime("%d %B %Y")
    total_amount = order.total_amount
    
    # Create WhatsApp message
    message = f"""Dear {customer_name},

🎉 *Great News!* 🎉

Your Order #{order_id} has been *DELIVERED* successfully! 

📦 *Order Details:*
• Order Date: {order_date}
• Total Amount: ₹{total_amount}

Thank you for shopping with *The Hamper Hub*! 

We hope you love your purchase. If you have any feedback or issues, please contact us:
📞 Call: {settings.ADMIN_PHONE}
💬 WhatsApp: {settings.ADMIN_PHONE}

Rate your experience: ⭐⭐⭐⭐⭐

*The Hamper Hub Team* ❤️"""
    
    # Encode message for URL
    encoded_message = quote(message)
    whatsapp_url = f"https://wa.me/91{customer_mobile}?text={encoded_message}"
    
    # Log for debugging
    print(f"WhatsApp URL for order #{order_id}: {whatsapp_url}")
    
    return whatsapp_url

# ==================== HELPER FUNCTIONS ====================

def get_cart_count(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return Cart.objects.filter(user=request.user).count()
    return 0