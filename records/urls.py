from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_records, name='records_list'),
    path('add/', views.add_record, name='record_add'),
    path('<int:record_id>/edit/', views.edit_record, name='record_edit'),
    path('add-sale/', views.add_sale, name='sale_add'),
    path('edit-sale/<int:sale_id>/', views.edit_sale, name='sale_edit'),
    path("update_manual_stock/<int:record_id>/", views.update_manual_stock, name="update_manual_stock"),
]
