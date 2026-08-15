from django.db import models

PAYMENT_CHOICES = [
    ('due', 'Due'),
    ('paid', 'Paid'),
]


class Purchase(models.Model):
    item = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.item


class Room(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ]

    number = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=50)
    rate = models.DecimalField(max_digits=10, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.number


class Booking(models.Model):
    STATUS_CHOICES = [
        ('checked_in', 'Checked in'),
        ('checked_out', 'Checked out'),
    ]

    guest_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(default=1)
    rate_per_night = models.DecimalField(max_digits=10, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='checked_in')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='due')

    class Meta:
        ordering = ['status', '-check_in']

    def __str__(self):
        return f'{self.guest_name} — {self.room.number}'

    @property
    def nights(self):
        return max((self.check_out - self.check_in).days, 1)

    @property
    def total(self):
        return self.nights * self.rate_per_night


class Group(models.Model):
    STATUS_CHOICES = [
        ('checked_in', 'Checked in'),
        ('checked_out', 'Checked out'),
    ]

    group_name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    members = models.PositiveIntegerField(default=1)
    rate_per_person = models.DecimalField(max_digits=10, decimal_places=0)
    check_in = models.DateField()
    check_out = models.DateField()
    rooms = models.ManyToManyField(Room, related_name='groups', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='checked_in')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='due')

    class Meta:
        ordering = ['status', '-check_in']

    def __str__(self):
        return self.group_name

    @property
    def nights(self):
        return max((self.check_out - self.check_in).days, 1)

    @property
    def total(self):
        return self.nights * self.rate_per_person * self.members
