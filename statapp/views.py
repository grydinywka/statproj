from datetime import datetime

import requests_cache
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from dwapi import datawiz

# requests_cache.install_cache('test_cache', backend='redis', expire_after=300)


def split_df(index_df, df, df_qty, pd_receipt_qty, span):
    length = len(index_df)

    value_span = length / span
    tail = length % span
    if tail > 0:
        value_span += 1
    list_df = []
    i = 0
    j = i + span
    while j <= length:
        list_df.append((index_df[i:j], df[i:j], df_qty[i:j], pd_receipt_qty[i:j]))
        i = j
        j += span

    if tail > 0:
        list_df.append((index_df[i:], df[i:], df_qty[i:], pd_receipt_qty[i:]))

    return list_df


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
            if data["MyClientID"] and data["MyClientSecret"]:
                dw = datawiz.DW(data["MyClientID"], data["MyClientSecret"])
            else:
                dw = datawiz.DW()
            data['dw'] = dw.get_client_info()
        except Exception as e:
            messages.error(request, "Please, type correct key and secret, %s" % e)
            errors['login'] = 'check key'
            errors['password'] = 'check secret'
            return render(request, 'statapp/login.html', {'errors': errors})

        request.session['key'] = data["MyClientID"] or 'anonim'
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
    if request.session.has_key('dw_info'):

        if request.method == 'POST' and request.POST.get('get_stat') is not None:
            form_data = request.POST
            data= {}
            errors = {}

            if form_data.get('date_from'):
                data['date_from'] = str(form_data.get('date_from').strip())
                try:
                    datetime.strptime(data['date_from'], '%Y-%m-%d')
                except Exception:
                    errors['date_from'] = 'Input date at YYYY-MM-DD format or left blank.'
            if form_data.get('date_to'):
                data['date_to'] = str(form_data.get('date_to').strip())
                try:
                    datetime.strptime(data['date_to'], '%Y-%m-%d')
                except Exception:
                    errors['date_to'] = 'Input date at YYYY-MM-DD format or left blank.'

            if form_data.getlist('shops'):
                data['shops'] = form_data.getlist('shops')
                for shop in form_data.getlist('shops'):
                    if not int(shop) in request.session['dw_info']['shops'].keys():
                        errors['shops'] = 'some shop is not available for you %s' % (shop)

            if errors:
                messages.error(request, 'Please correct errors!')
                return render(request, 'statapp/statistics.html', {'errors': errors, "shops1": form_data.getlist('shops')})
            dw = request.session['dw']
            # print data['date_from']
            try:
                pandas_res_by_turnover = dw.get_categories_sale(**data)
                pandas_res_by_qty = dw.get_categories_sale(by='qty', **data)
                pandas_res_by_receipt_qty = dw.get_categories_sale(by='receipts_qty', **data)
            except Exception:
                messages.error(request, 'Try again because datawiz does not response!')
                return render(request, 'statapp/statistics.html', {})

            # turnover = pandas_res.sum(axis=1)
            # dates = pandas_res.index
            result = split_df(pandas_res_by_turnover.index, pandas_res_by_turnover.sum(axis=1),
                              pandas_res_by_qty.sum(axis=1), pandas_res_by_receipt_qty.sum(axis=1), 4)
            # print pandas_res
            # print result


            return render(request, 'statapp/statistics.html', {'show_tables':
                True, 'pandas_list': result})
        return render(request, 'statapp/statistics.html', {})

    return HttpResponseRedirect(reverse('index'))