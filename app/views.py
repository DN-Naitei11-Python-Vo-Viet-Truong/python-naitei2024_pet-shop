import re
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from .forms import SignInForm
from django.contrib.auth import login, authenticate
from django.urls import reverse


def index(request):
    """View function for home page of site."""
    return render(request, "home.html")


def ShopView(request):
    """View function for shop page of site."""
    return render(request, "app/shop.html")


def clean_message(message):
    return re.sub('<[^<]+?>', '', str(message))


def login_view(request):
    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    if user.is_banned:
                        messages.error(request, _(
                            "Your account has been banned."))
                    else:
                        login(request, user)
                        messages.success(request, _(
                            "You have been logged in successfully."))
                        return redirect('index')
                else:
                    request.session['user_id'] = user.id
                    return redirect(reverse('otp_verify'))
            else:
                messages.error(request, _("Invalid username or password."))
        else:
            for error in list(form.errors.values()):
                messages.error(request, clean_message(error))
    else:
        form = SignInForm()

    return render(request, 'registration/sign_in.html', {'form': form})
