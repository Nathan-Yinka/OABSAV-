from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.list_records, name='records_list'),
    path('add/', views.add_record, name='record_add'),
    path('<int:record_id>/edit/', views.edit_record, name='record_edit'),
    path('add-sale/', views.add_sale, name='sale_add'),
    path('edit-sale/<int:sale_id>/', views.edit_sale, name='sale_edit'),
    path("update_manual_stock/<int:record_id>/", views.update_manual_stock, name="update_manual_stock"),

    
    # Login page
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),

    # Logout page (redirects to login after logout)
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('add-crates-pieces/', views.add_crates_pieces, name='add_crates_pieces'),
    path('view-only-crates/<str:date_str>/', views.view_crates_pieces_summary, name='view_crates_pieces_summary'),

    path('submit-crates-pieces/', views.add_crates_pieces, name='submit_crates_pieces'),  # Form posts here
    
    # Production summary page
    path('production-summary/<int:year>/<int:month>/', views.production_summary, name='production_summary'),
    path('production-summary/', views.production_summary, name='production_summary_default'),  # Default to September 2025
]
