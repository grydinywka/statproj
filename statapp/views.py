from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from dwapi import datawiz


def index(request):
    if request.session.has_key('key'):
        return HttpResponseRedirect(reverse('statistics'))
    return render(request, 'statapp/index.html', {})


def login(request):
    if request.session.has_key('key'):
        return HttpResponseRedirect(reverse('statistics'))
    if request.method == 'POST' and request.POST.get('submit_button') is not None:
        errors = {}

        data = {
            'MyClientID': request.POST.get('login'),
            'MyClientSecret': request.POST.get('password')
        }

        try:
            dw = datawiz.DW(data["MyClientID"], data["MyClientSecret"])
            data['dw'] = dw.get_client_info()
        except Exception:
            messages.error(request, "Please, type correct key and secret")
            errors['login'] = 'check key'
            errors['password'] = 'check secret'
            return render(request, 'statapp/login.html', {'errors': errors})

        request.session['key'] = data["MyClientID"]
        request.session['secret'] = data["MyClientSecret"]
        request.session['name'] = data["dw"]['name']

        messages.info(request, "You've loged in")
        return HttpResponseRedirect(reverse('statistics'))

    return render(request, 'statapp/login.html', {})


def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('index'))


def statistics(request):
    if cache.get('foo'):
        result = cache.get('foo')
    else:
        cache.set('foo', 'bar2', 30)
        result = 'nofoo'
    return render(request, 'statapp/statistics.html', {'result': result})