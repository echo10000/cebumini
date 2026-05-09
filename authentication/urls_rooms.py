from django.urls import path
from . import views_rooms

app_name = 'rooms'

urlpatterns = [
    # Public views
    path('', views_rooms.room_list_view, name='list'),
    path('search/', views_rooms.room_search_view, name='search'),
    path('<int:room_id>/', views_rooms.room_detail_view, name='detail'),
    
    # Admin views
    path('create/', views_rooms.room_create_view, name='create'),
    path('<int:room_id>/edit/', views_rooms.room_edit_view, name='edit'),
    path('<int:room_id>/delete/', views_rooms.room_delete_view, name='delete'),
    
    # Image management
    path('<int:room_id>/upload-image/', views_rooms.room_image_upload_view, name='upload_image'),
    path('image/<int:image_id>/delete/', views_rooms.room_image_delete_view, name='delete_image'),
]
