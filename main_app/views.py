from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import BookingForm, GroupForm, MaintenanceForm, PurchaseForm, RoomForm, SalaryForm
from .models import Booking, Group, Maintenance, Purchase, Room, Salary


def _quick_range_options(url_name, date_from, date_to):
    today = timezone.localdate()
    ranges = [
        ('today', 'Today', today, today),
        ('week', 'This week', today - timedelta(days=today.weekday()), today),
        ('month', 'This month', today.replace(day=1), today),
    ]
    base = reverse(url_name)
    options = []
    for key, label, start, end in ranges:
        options.append({
            'key': key,
            'label': label,
            'url': f'{base}?from={start.isoformat()}&to={end.isoformat()}',
            'active': date_from == start.isoformat() and date_to == end.isoformat(),
        })
    options.append({
        'key': 'all',
        'label': 'All time',
        'url': base,
        'active': not date_from and not date_to,
    })
    return options


@login_required
def dashboard(request):
    rooms_qs = Room.objects.all()
    total_rooms = rooms_qs.count()
    occupied = rooms_qs.filter(status='occupied').count()
    available = rooms_qs.filter(status='available').count()
    occ_rate = round((occupied / total_rooms) * 100) if total_rooms else 0

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    today_total = Purchase.objects.filter(created_at__date=today).aggregate(total=Sum('price'))['total'] or 0
    yesterday_total = Purchase.objects.filter(created_at__date=yesterday).aggregate(total=Sum('price'))['total'] or 0
    purchase_change = round(((today_total - yesterday_total) / yesterday_total) * 100) if yesterday_total else None

    week_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        total = Purchase.objects.filter(created_at__date=day).aggregate(total=Sum('price'))['total'] or 0
        week_days.append({'label': day.strftime('%a'), 'total': total, 'is_today': day == today})
    max_week = max((d['total'] for d in week_days), default=0) or 1
    for d in week_days:
        d['pct'] = round((d['total'] / max_week) * 100)

    activity = []
    for b in Booking.objects.select_related('room').order_by('-check_in')[:6]:
        activity.append({'date': b.check_in, 'text': f'{b.guest_name} checked in — room {b.room.number}'})
    for g in Group.objects.order_by('-check_in')[:6]:
        activity.append({'date': g.check_in, 'text': f'{g.group_name} ({g.members} guests) checked in'})
    for p in Purchase.objects.order_by('-created_at')[:6]:
        activity.append({'date': p.created_at.date(), 'text': f'Purchased {p.item} — Rs {p.price:,.0f}'})
    activity.sort(key=lambda a: a['date'], reverse=True)
    activity = activity[:6]

    context = {
        'total_rooms': total_rooms,
        'occupied': occupied,
        'available': available,
        'occ_rate': occ_rate,
        'today_total': today_total,
        'purchase_change': purchase_change,
        'week_days': week_days,
        'rooms': rooms_qs,
        'activity': activity,
    }
    return render(request, 'main_app/dashboard.html', context)


def _render_rooms(request, room_form=None, booking_form=None, room_modal_open=False, booking_modal_open=False):
    rooms_qs = Room.objects.all()
    bookings_qs = Booking.objects.select_related('room').all()
    available_rooms = rooms_qs.filter(status='available')

    if room_form is None:
        modal_param = request.GET.get('room_modal')
        if modal_param == 'edit' and request.GET.get('id'):
            room = get_object_or_404(Room, pk=request.GET['id'])
            room_form = RoomForm(instance=room)
            room_modal_open = True
        elif modal_param == 'add':
            room_form = RoomForm()
            room_modal_open = True
        else:
            room_form = RoomForm()

    if booking_form is None:
        booking_form = BookingForm(
            available_rooms=available_rooms,
            initial={'check_in': timezone.localdate()},
        )
        if request.GET.get('booking_modal') == '1':
            booking_modal_open = True

    checkout_booking = None
    checkout_id = request.GET.get('checkout')
    if checkout_id:
        checkout_booking = Booking.objects.select_related('room').filter(
            pk=checkout_id
        ).exclude(status='checked_out').first()

    context = {
        'rooms': rooms_qs,
        'bookings': bookings_qs,
        'available_rooms': available_rooms,
        'room_form': room_form,
        'booking_form': booking_form,
        'room_choices': list(zip(booking_form['room'], available_rooms)),
        'room_modal_open': room_modal_open,
        'booking_modal_open': booking_modal_open,
        'checkout_booking': checkout_booking,
    }
    return render(request, 'main_app/rooms.html', context)


@login_required
def rooms(request):
    return _render_rooms(request)


@login_required
def room_save(request):
    if request.method != 'POST':
        return redirect('rooms')

    room_id = request.POST.get('room_id')
    room = get_object_or_404(Room, pk=room_id) if room_id else None
    form = RoomForm(request.POST, instance=room)
    if form.is_valid():
        form.save()
        messages.success(request, 'Room updated.' if room else 'Room added.')
        return redirect('rooms')

    messages.error(request, 'Could not save the room — please fix the errors below.')
    return _render_rooms(request, room_form=form, room_modal_open=True)


@login_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        if room.bookings.exclude(status='checked_out').exists():
            messages.error(request, 'Cannot delete — this room has an active booking.')
        else:
            room.delete()
            messages.success(request, 'Room deleted.')
    return redirect('rooms')


@login_required
def booking_save(request):
    if request.method != 'POST':
        return redirect('rooms')

    available_rooms = Room.objects.filter(status='available')
    form = BookingForm(request.POST, available_rooms=available_rooms)
    if form.is_valid():
        booking = form.save(commit=False)
        booking.rate_per_night = booking.room.rate
        booking.save()
        booking.room.status = 'occupied'
        booking.room.save(update_fields=['status'])
        messages.success(request, 'Booking created.')
        return redirect('rooms')

    messages.error(request, 'Could not create the booking — please fix the errors below.')
    return _render_rooms(request, booking_form=form, booking_modal_open=True)


@login_required
def booking_checkout(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST' and booking.status != 'checked_out':
        payment_status = request.POST.get('payment_status')
        if payment_status in ('paid', 'due'):
            booking.payment_status = payment_status
        booking.status = 'checked_out'
        booking.save(update_fields=['status', 'payment_status'])
        booking.room.status = 'available'
        booking.room.save(update_fields=['status'])
        messages.success(request, 'Guest checked out.')
    return redirect('rooms')


@login_required
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        if booking.status != 'checked_out':
            booking.room.status = 'available'
            booking.room.save(update_fields=['status'])
        booking.delete()
        messages.success(request, 'Booking removed.')
    return redirect('rooms')


def _render_groups(request, group_form=None, group_modal_open=False):
    groups_qs = Group.objects.prefetch_related('rooms').all()
    available_rooms = Room.objects.filter(status='available')

    if group_form is None:
        group_form = GroupForm(
            available_rooms=available_rooms,
            initial={'check_in': timezone.localdate()},
        )
        if request.GET.get('group_modal') == '1':
            group_modal_open = True

    checkout_group = None
    checkout_id = request.GET.get('checkout')
    if checkout_id:
        checkout_group = Group.objects.prefetch_related('rooms').filter(
            pk=checkout_id
        ).exclude(status='checked_out').first()

    context = {
        'groups': groups_qs,
        'available_rooms': available_rooms,
        'group_form': group_form,
        'group_room_choices': list(zip(group_form['rooms'], available_rooms)),
        'group_modal_open': group_modal_open,
        'checkout_group': checkout_group,
    }
    return render(request, 'main_app/groups.html', context)


@login_required
def groups(request):
    return _render_groups(request)


@login_required
def group_save(request):
    if request.method != 'POST':
        return redirect('groups')

    available_rooms = Room.objects.filter(status='available')
    form = GroupForm(request.POST, available_rooms=available_rooms)
    if form.is_valid():
        group = form.save()
        group.rooms.all().update(status='occupied')
        messages.success(request, 'Group booking added.')
        return redirect('groups')

    messages.error(request, 'Could not add the group — please fix the errors below.')
    return _render_groups(request, group_form=form, group_modal_open=True)


@login_required
def group_checkout(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST' and group.status != 'checked_out':
        payment_status = request.POST.get('payment_status')
        if payment_status in ('paid', 'due'):
            group.payment_status = payment_status
        group.status = 'checked_out'
        group.save(update_fields=['status', 'payment_status'])
        group.rooms.all().update(status='available')
        messages.success(request, 'Group checked out.')
    return redirect('groups')


@login_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        if group.status != 'checked_out':
            group.rooms.all().update(status='available')
        group.delete()
        messages.success(request, 'Group booking removed.')
    return redirect('groups')


@login_required
def reports(request):
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    bookings = Booking.objects.select_related('room').all()
    groups_qs = Group.objects.all()
    purchases = Purchase.objects.all()
    salaries = Salary.objects.all()
    maintenances = Maintenance.objects.all()

    if date_from:
        bookings = bookings.filter(check_in__gte=date_from)
        groups_qs = groups_qs.filter(check_in__gte=date_from)
        purchases = purchases.filter(created_at__date__gte=date_from)
        salaries = salaries.filter(created_at__date__gte=date_from)
        maintenances = maintenances.filter(created_at__date__gte=date_from)
    if date_to:
        bookings = bookings.filter(check_in__lte=date_to)
        groups_qs = groups_qs.filter(check_in__lte=date_to)
        purchases = purchases.filter(created_at__date__lte=date_to)
        salaries = salaries.filter(created_at__date__lte=date_to)
        maintenances = maintenances.filter(created_at__date__lte=date_to)

    room_revenue = sum((b.total for b in bookings), 0)
    group_revenue = sum((g.total for g in groups_qs), 0)
    total_revenue = room_revenue + group_revenue

    paid_revenue = (
        sum((b.total for b in bookings if b.payment_status == 'paid'), 0)
        + sum((g.total for g in groups_qs if g.payment_status == 'paid'), 0)
    )
    due_revenue = total_revenue - paid_revenue

    purchase_total = purchases.aggregate(total=Sum('price'))['total'] or 0
    salary_total = salaries.aggregate(total=Sum('amount'))['total'] or 0
    maintenance_total = maintenances.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = purchase_total + salary_total + maintenance_total
    purchase_count = purchases.count()

    profit = total_revenue - total_expense
    margin = round((profit / total_revenue) * 100) if total_revenue > 0 else 0
    max_val = max(total_revenue, total_expense, 1)

    filter_params = {k: v for k, v in {'from': date_from, 'to': date_to}.items() if v}

    purchases_url = reverse('purchases')
    expenses_url = reverse('expenses')
    if filter_params:
        purchases_url += '?' + urlencode(filter_params)
        expenses_url += '?' + urlencode(filter_params)

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'quick_ranges': _quick_range_options('reports', date_from, date_to),
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'profit': profit,
        'margin': margin,
        'room_revenue': room_revenue,
        'group_revenue': group_revenue,
        'paid_revenue': paid_revenue,
        'due_revenue': due_revenue,
        'revenue_bar_pct': round((total_revenue / max_val) * 100),
        'expense_bar_pct': round((total_expense / max_val) * 100),
        'paid_pct': round((paid_revenue / total_revenue) * 100) if total_revenue else 0,
        'due_pct': round((due_revenue / total_revenue) * 100) if total_revenue else 0,
        'purchase_total': purchase_total,
        'purchase_count': purchase_count,
        'purchases_url': purchases_url,
        'salary_total': salary_total,
        'maintenance_total': maintenance_total,
        'expenses_url': expenses_url,
    }
    return render(request, 'main_app/reports.html', context)


PURCHASE_SORT_FIELDS = {
    'item': 'item',
    'date': 'created_at',
    'price': 'price',
}


def _render_purchases(request, form=None, modal_open=False):
    if form is None:
        modal_param = request.GET.get('purchase_modal')
        if modal_param == 'edit' and request.GET.get('id'):
            purchase = get_object_or_404(Purchase, pk=request.GET['id'])
            form = PurchaseForm(instance=purchase)
            modal_open = True
        elif modal_param == 'add':
            form = PurchaseForm()
            modal_open = True
        else:
            form = PurchaseForm()

    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    sort = request.GET.get('sort', '-date')
    sort_key = sort.lstrip('-')
    sort_field = PURCHASE_SORT_FIELDS.get(sort_key, 'created_at')
    order_by = f'-{sort_field}' if sort.startswith('-') else sort_field

    purchase_list = Purchase.objects.all()
    if date_from:
        purchase_list = purchase_list.filter(created_at__date__gte=date_from)
    if date_to:
        purchase_list = purchase_list.filter(created_at__date__lte=date_to)
    purchase_list = purchase_list.order_by(order_by)

    filtered_total = purchase_list.aggregate(total=Sum('price'))['total'] or 0
    today_total = Purchase.objects.filter(
        created_at__date=timezone.localdate()
    ).aggregate(total=Sum('price'))['total'] or 0

    def sort_url(column):
        next_sort = f'-{column}' if sort == column else column
        params = request.GET.copy()
        params['sort'] = next_sort
        return '?' + params.urlencode()

    context = {
        'form': form,
        'purchases': purchase_list,
        'date_from': date_from,
        'date_to': date_to,
        'quick_ranges': _quick_range_options('purchases', date_from, date_to),
        'filtered_total': filtered_total,
        'today_total': today_total,
        'modal_open': modal_open,
        'sort': sort,
        'sort_key': sort_key,
        'sort_url_item': sort_url('item'),
        'sort_url_date': sort_url('date'),
        'sort_url_price': sort_url('price'),
    }
    return render(request, 'main_app/purchases.html', context)


@login_required
def purchases(request):
    return _render_purchases(request)


@login_required
def purchase_save(request):
    if request.method != 'POST':
        return redirect('purchases')

    purchase_id = request.POST.get('purchase_id')
    purchase = get_object_or_404(Purchase, pk=purchase_id) if purchase_id else None
    form = PurchaseForm(request.POST, instance=purchase)
    if form.is_valid():
        form.save()
        messages.success(request, 'Purchase updated.' if purchase else 'Purchase logged.')
        return redirect('purchases')

    messages.error(request, 'Could not save the purchase — please fix the errors below.')
    return _render_purchases(request, form=form, modal_open=True)


@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        purchase.delete()
        messages.success(request, 'Purchase removed.')
    return redirect('purchases')


def _render_expenses(request, salary_form=None, maintenance_form=None,
                      salary_modal_open=False, maintenance_modal_open=False):
    if salary_form is None:
        salary_form = SalaryForm()
        if request.GET.get('salary_modal') == '1':
            salary_modal_open = True
    if maintenance_form is None:
        maintenance_form = MaintenanceForm()
        if request.GET.get('maintenance_modal') == '1':
            maintenance_modal_open = True

    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    salaries = Salary.objects.all()
    maintenances = Maintenance.objects.all()
    if date_from:
        salaries = salaries.filter(created_at__date__gte=date_from)
        maintenances = maintenances.filter(created_at__date__gte=date_from)
    if date_to:
        salaries = salaries.filter(created_at__date__lte=date_to)
        maintenances = maintenances.filter(created_at__date__lte=date_to)

    salary_total = salaries.aggregate(total=Sum('amount'))['total'] or 0
    maintenance_total = maintenances.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'salary_form': salary_form,
        'maintenance_form': maintenance_form,
        'salaries': salaries,
        'maintenances': maintenances,
        'date_from': date_from,
        'date_to': date_to,
        'quick_ranges': _quick_range_options('expenses', date_from, date_to),
        'salary_total': salary_total,
        'maintenance_total': maintenance_total,
        'combined_total': salary_total + maintenance_total,
        'salary_modal_open': salary_modal_open,
        'maintenance_modal_open': maintenance_modal_open,
    }
    return render(request, 'main_app/expenses.html', context)


@login_required
def expenses(request):
    return _render_expenses(request)


@login_required
def salary_save(request):
    if request.method != 'POST':
        return redirect('expenses')

    form = SalaryForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Salary logged.')
        return redirect('expenses')

    messages.error(request, 'Could not save the salary entry — please fix the errors below.')
    return _render_expenses(request, salary_form=form, salary_modal_open=True)


@login_required
def salary_delete(request, pk):
    salary = get_object_or_404(Salary, pk=pk)
    if request.method == 'POST':
        salary.delete()
        messages.success(request, 'Salary entry removed.')
    return redirect('expenses')


@login_required
def maintenance_save(request):
    if request.method != 'POST':
        return redirect('expenses')

    form = MaintenanceForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Maintenance logged.')
        return redirect('expenses')

    messages.error(request, 'Could not save the maintenance entry — please fix the errors below.')
    return _render_expenses(request, maintenance_form=form, maintenance_modal_open=True)


@login_required
def maintenance_delete(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    if request.method == 'POST':
        maintenance.delete()
        messages.success(request, 'Maintenance entry removed.')
    return redirect('expenses')
