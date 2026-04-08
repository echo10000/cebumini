from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Room, RoomImage, RoomType
from .forms_rooms import RoomForm, RoomImageForm, RoomFilterForm
from .views_recommendations import get_recommendations_context


@require_http_methods(["GET"])
def room_list_view(request):
    """List all rooms with filtering"""
    rooms = Room.objects.all()
    
    # Filter by room type
    room_type = request.GET.get('room_type')
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price:
        rooms = rooms.filter(price_per_night__gte=min_price)
    if max_price:
        rooms = rooms.filter(price_per_night__lte=max_price)
    
    # Filter by capacity
    capacity = request.GET.get('capacity')
    if capacity:
        rooms = rooms.filter(capacity__gte=capacity)
    
    # Filter by availability
    available_only = request.GET.get('available_only')
    if available_only:
        rooms = rooms.filter(is_available=True)
    
    # Search by room number
    search = request.GET.get('search')
    if search:
        rooms = rooms.filter(Q(room_number__icontains=search) | 
                           Q(description__icontains=search))
    
    # Pagination
    paginator = Paginator(rooms, 12)
    page_number = request.GET.get('page')
    rooms = paginator.get_page(page_number)
    
    # Get filter form
    filter_form = RoomFilterForm(request.GET or None)
    
    # Get recommendations for logged-in users
    recommendations_context = get_recommendations_context(request, limit=3)
    
    context = {
        'rooms': rooms,
        'filter_form': filter_form,
        'room_types': RoomType.choices,
        'recommendations': recommendations_context['recommendations'],
        'has_recommendations': recommendations_context['has_recommendations'],
    }
    return render(request, 'rooms/room_list.html', context)


@require_http_methods(["GET"])
def room_detail_view(request, room_id):
    """Display room details"""
    room = get_object_or_404(Room, id=room_id)
    images = room.images.all()
    
    # Get similar rooms (same type, different room)
    similar_rooms = Room.objects.filter(
        room_type=room.room_type,
        is_available=True
    ).exclude(id=room_id)[:3]
    
    context = {
        'room': room,
        'images': images,
        'similar_rooms': similar_rooms,
    }
    return render(request, 'rooms/room_detail.html', context)


# Admin views (require admin role)

@login_required(login_url='auth:login')
@require_http_methods(["GET", "POST"])
def room_create_view(request):
    """Create new room (admin only)"""
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to add rooms.')
        return redirect('rooms:list')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room {room.room_number} created successfully!')
            return redirect('rooms:detail', room_id=room.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RoomForm()
    
    context = {'form': form, 'title': 'Add New Room'}
    return render(request, 'rooms/room_form.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["GET", "POST"])
def room_edit_view(request, room_id):
    """Edit room (admin only)"""
    room = get_object_or_404(Room, id=room_id)
    
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to edit rooms.')
        return redirect('rooms:detail', room_id=room.id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room {room.room_number} updated successfully!')
            return redirect('rooms:detail', room_id=room.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RoomForm(instance=room)
    
    images = room.images.all()
    context = {
        'form': form,
        'room': room,
        'images': images,
        'title': f'Edit Room {room.room_number}'
    }
    return render(request, 'rooms/room_form.html', context)


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
def room_delete_view(request, room_id):
    """Delete room (admin only)"""
    room = get_object_or_404(Room, id=room_id)
    
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to delete rooms.')
        return redirect('rooms:detail', room_id=room.id)
    
    room_number = room.room_number
    room.delete()
    messages.success(request, f'Room {room_number} deleted successfully!')
    return redirect('rooms:list')


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
def room_image_upload_view(request, room_id):
    """Upload image for room (admin only)"""
    room = get_object_or_404(Room, id=room_id)
    
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to upload images.')
        return redirect('rooms:detail', room_id=room.id)
    
    form = RoomImageForm(request.POST, request.FILES)
    if form.is_valid():
        image = form.save(commit=False)
        image.room = room
        image.save()
        messages.success(request, 'Image uploaded successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('rooms:detail', room_id=room.id)


@login_required(login_url='auth:login')
@require_http_methods(["POST"])
def room_image_delete_view(request, image_id):
    """Delete room image (admin only)"""
    image = get_object_or_404(RoomImage, id=image_id)
    room_id = image.room.id
    
    if not request.user.is_admin():
        messages.error(request, 'You do not have permission to delete images.')
        return redirect('rooms:detail', room_id=room_id)
    
    image.delete()
    messages.success(request, 'Image deleted successfully!')
    return redirect('rooms:detail', room_id=room_id)
