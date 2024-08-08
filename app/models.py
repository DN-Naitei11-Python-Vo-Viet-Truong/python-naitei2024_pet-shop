from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone
from datetime import timedelta
from django.db.models import Min
from .constants import (
    GENDER_CHOICES, SIZE_CHOICES, PAYMENT_METHOD_CHOICES,
    PAYMENT_STATUS_CHOICES, DEFAULT_USER_AVATAR, MAX_LENGTH_NAME,
    MAX_LENGTH_PHONENUM, MAX_LENGTH_OTP_SCRET, MAX_LENGTH_CHOICES
)
import pyotp


class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=MAX_LENGTH_NAME,
        unique=True,
        validators=[MinLengthValidator(3)],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
        verbose_name=_('username')
    )
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
        verbose_name=_('email')
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_NAME, verbose_name=_('first name'))
    last_name = models.CharField(
        max_length=MAX_LENGTH_NAME, verbose_name=_('last name'))
    gender = models.CharField(
        max_length=MAX_LENGTH_CHOICES,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('gender')
    )
    avatar = CloudinaryField(
        _('avatar'), default=DEFAULT_USER_AVATAR)
    default_address = models.TextField(
        blank=False, null=False, verbose_name=_('default address'))
    default_phone_number = models.CharField(
        max_length=MAX_LENGTH_PHONENUM,
        validators=[
            RegexValidator(
                regex=r'^0\d{9}$',
                message=_("Phone number must be 10 digits and start with 0.")
            )
        ],
        blank=False,
        null=False,
        verbose_name=_('default phone number')
    )
    is_banned = models.BooleanField(
        default=False,
        verbose_name=_('banned status')
    )
    otp_secret = models.CharField(
        max_length=MAX_LENGTH_OTP_SCRET,
        blank=True,
        null=True,
        default=pyotp.random_base32,
        verbose_name=_('OTP secret')
    )
    otp_created_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('OTP created at')
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name

    def generate_otp(self):
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
        self.otp_created_at = timezone.now()
        self.save()
        totp = pyotp.TOTP(self.otp_secret)
        return totp.now()

    def clean(self):
        super().clean()
        if self.email and not self.email.endswith('@gmail.com'):
            raise ValidationError(_('Email must end with @gmail.com'))
        if self.email and self.username and self.email.split(
                '@')[0] == self.username:
            raise ValidationError(
                _('Email prefix cannot be the same as username prefix.'))

    def is_otp_expired(self):
        now = timezone.now()
        return now > self.otp_created_at + timedelta(minutes=3)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class Category(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        unique=True,
        verbose_name=_('name'),
        help_text=_('Enter the name of the category.'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('created at'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('updated at'),
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']


class Product(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_NAME, verbose_name=_('name'))
    image = CloudinaryField(_('image'))
    category = models.ForeignKey(
        'Category', on_delete=models.CASCADE, verbose_name=_('category'))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name=_('price'),
        null=True,
        blank=True)
    description = models.TextField(verbose_name=_('description'))
    average_rating = models.FloatField(verbose_name=_('average rating'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def update_price(self):
        min_price = self.productdetail_set.aggregate(Min('price'))[
            'price__min']
        if (min_price is not None):
            self.price = min_price
            self.save()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.pk])

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['name']


class ProductDetail(models.Model):
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, verbose_name=_('product'))
    image = CloudinaryField(
        _('image'),
        default="image/upload/v1723015712/byvk6iveofgnb1xf7dsz.jpg")
    size = models.CharField(
        max_length=MAX_LENGTH_CHOICES,
        choices=SIZE_CHOICES,
        verbose_name=_('size'),
        null=True,
        blank=True)
    color = models.CharField(
        max_length=MAX_LENGTH_CHOICES,
        verbose_name=_('color'),
        null=True,
        blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=0, verbose_name=_('price'))
    remain_quantity = models.IntegerField(verbose_name=_('remaining quantity'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'{self.product.name} - {self.size}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_price()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.product.update_price()

    class Meta:
        verbose_name = _('product detail')
        verbose_name_plural = _('product details')
        ordering = ['product']


class Bill(models.Model):
    user = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, verbose_name=_('user'))
    address = models.TextField(verbose_name=_('address'), null=False)
    phone_number = models.CharField(
        max_length=MAX_LENGTH_PHONENUM,
        verbose_name=_('phone number'),
        null=False)
    voucher = models.ForeignKey(
        'Voucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('voucher'))
    status = models.CharField(
        max_length=MAX_LENGTH_CHOICES,
        choices=PAYMENT_STATUS_CHOICES,
        verbose_name=_('status'))
    note_content = models.TextField(
        blank=True, null=True, verbose_name=_('note content'))
    total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_('total'), null=False)
    payment_method = models.CharField(
        max_length=MAX_LENGTH_CHOICES,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name=_('payment method'),
        null=False)
    expired_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_('expired at'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'Bill {self.id} - {self.user.username}'

    def get_absolute_url(self):
        return reverse('bill_detail', args=[self.pk])

    class Meta:
        verbose_name = _('bill')
        verbose_name_plural = _('bills')


class BillDetail(models.Model):
    bill = models.ForeignKey(
        'Bill', on_delete=models.CASCADE, verbose_name=_('bill'))
    product_detail = models.ForeignKey(
        'ProductDetail',
        on_delete=models.CASCADE,
        verbose_name=_('product detail'))
    quantity = models.IntegerField(verbose_name=_('quantity'), null=False)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'Bill {self.bill.id} - {self.product_detail.product.name}'

    class Meta:
        verbose_name = _('bill detail')
        verbose_name_plural = _('bill details')
        ordering = ['bill']


class Comment(models.Model):
    user = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, verbose_name=_('user'))
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, verbose_name=_('product'))
    content = models.TextField(verbose_name=_('content'), null=False)
    star = models.IntegerField(verbose_name=_('star'), null=False)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'Comment {self.id} by {self.user.username}'

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')


class Voucher(models.Model):
    discount = models.FloatField(verbose_name=_('discount'))
    started_at = models.DateTimeField(verbose_name=_('started at'))
    ended_at = models.DateTimeField(verbose_name=_('ended at'))
    category = models.ManyToManyField(
        'Category',
        blank=True,
        verbose_name=_('categories'),
        help_text=_('Categories this condition applies to.')
    )
    min_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        blank=True,
        default=0,
        verbose_name=_('minimum amount'),
        help_text=_('Minimum amount required to apply this voucher.')
    )
    is_global = models.BooleanField(default=False, verbose_name=_('is global'))
    user = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('user'),
        help_text=_('User to whom this voucher is assigned.'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'Voucher {self.id} - {self.discount}%'

    def clean(self) -> None:
        super().clean()
        if self.started_at and self.ended_at and (
                self.ended_at <= self.started_at):
            raise ValidationError(
                _("Date ended must be after date started."))
        if not self.is_global and not self.user:
            raise ValidationError(
                _("A non-global voucher must have an assigned user."))
        if self.is_global and self.user:
            raise ValidationError(
                _("A global voucher can't be assigned to a customer."))

    def get_absolute_url(self):
        return reverse('voucher_detail', args=[self.pk])

    class Meta:
        verbose_name = _('voucher')
        verbose_name_plural = _('vouchers')


class VoucherHistory(models.Model):
    user = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, verbose_name=_('user'))
    voucher = models.ForeignKey(
        'Voucher', on_delete=models.CASCADE, verbose_name=_('voucher'))

    def __str__(self):
        return f'Voucher history {self.id} - {self.user.username}'

    class Meta:
        verbose_name = _('voucher history')
        verbose_name_plural = _('voucher histories')


class Cart(models.Model):
    user = models.ForeignKey(
        'CustomUser', on_delete=models.CASCADE, verbose_name=_('user'))
    total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_('total'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'Cart {self.id} - {self.user.username}'

    def get_absolute_url(self):
        return reverse('cart_detail', args=[self.pk])

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')


class CartDetail(models.Model):
    cart = models.ForeignKey(
        'Cart', on_delete=models.CASCADE, verbose_name=_('cart'))
    product_detail = models.ForeignKey(
        'ProductDetail',
        on_delete=models.CASCADE,
        verbose_name=_('product detail'))
    quantity = models.IntegerField(verbose_name=_('quantity'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))

    def __str__(self):
        return f'Cart {self.cart.id} - {self.product_detail.product.name}'

    class Meta:
        verbose_name = _('cart detail')
        verbose_name_plural = _('cart details')
