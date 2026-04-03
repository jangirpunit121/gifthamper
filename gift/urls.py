from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cart URLs
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('request-return/<int:order_id>/', views.request_return, name='request_return'),
    
    # Admin URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-update-order/<int:order_id>/', views.admin_update_order_status, name='admin_update_order'),
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin-create-product/', views.admin_create_product, name='admin_create_product'),
    path('admin-edit-product/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-delete-product/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    path('admin-returns/', views.admin_returns, name='admin_returns'),
    path('admin-update-return/<int:return_id>/', views.admin_update_return_status, name='admin_update_return'),
]