from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from dwapi import datawiz
import pandas as pd
import requests_cache

requests_cache.install_cache('test_cache', backend='redis', expire_after=300)


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
        # request.session['name'] = data["dw"]['name']
        request.session['dw_info'] = data["dw"]
        request.session['dw'] = dw

        messages.info(request, "You've loged in")
        return HttpResponseRedirect(reverse('statistics'))

    return render(request, 'statapp/login.html', {})


def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('index'))


def user_info(request):
    if  request.session.has_key('dw_info'):
        dw = request.session['dw_info']

        return render(request, 'statapp/user_info.html', {'dw': dw})

    return HttpResponseRedirect(reverse('index'))


# @cache_page(60 * 15)
def statistics(request):
    if  request.session.has_key('dw_info'):

        if request.method == 'POST' and request.POST.get('get_stat') is not None:
            data= {}

            if request.POST.get('date_from'):
                data['date_from'] = str(request.POST.get('date_from'))
            if request.POST.get('date_to'):
                data['date_to'] = str(request.POST.get('date_to'))
            dw = request.session['dw']
            # print data['date_from']
            pandas_res = dw.get_categories_sale(**data)
            turnover = pandas_res.sum(axis=1)
            dates = pandas_res.index
            result = {}

            return render(request, 'statapp/statistics.html', {'turnover': turnover, 'dates': dates})
        return render(request, 'statapp/statistics.html', {})

    return HttpResponseRedirect(reverse('index'))