from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('requests/', views.ticket_list, name='ticket_list'),
    path('requests/new/', views.ticket_create, name='ticket_create'),
    path('requests/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('requests/<int:pk>/attempt/', views.ticket_attempt, name='ticket_attempt'),
    path('requests/<int:pk>/reject/', views.ticket_reject, name='ticket_reject'),
    path('requests/<int:pk>/notes/', views.ticket_notes, name='ticket_notes'),
    path('requests/<int:pk>/complete/', views.ticket_complete, name='ticket_complete'),
    path('requests/<int:pk>/parts/', views.ticket_add_part, name='ticket_add_part'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/new/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('people/', views.user_list, name='user_list'),
    path('people/new/', views.user_create, name='user_create'),
    path('people/<int:pk>/password/', views.user_password, name='user_password'),
    path('people/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),
    path('board/', views.tv_board, name='tv_board'),
    path('preventive/', views.pm_list, name='pm_list'),
    path('preventive/analytics/', views.pm_analytics, name='pm_analytics'),
    path('preventive/upload/', views.pm_upload, name='pm_upload'),
    path('preventive/<int:pk>/', views.pm_detail, name='pm_detail'),
    path('preventive/<int:pk>/complete/', views.pm_complete, name='pm_complete'),
    path('catalog/import/', views.import_categories, name='import_categories'),
    path('catalog/template/', views.download_category_template, name='category_template'),
    path('api/categories/<int:pk>/subcategories/', views.api_subcategories, name='api_subcategories'),
    path('api/subcategories/<int:pk>/assets/', views.api_assets, name='api_assets'),
]
