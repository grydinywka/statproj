from datetime import datetime

import requests_cache
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from dwapi import datawiz
import pandas

requests_cache.install_cache('test_cache', backend='memory', expire_after=300)


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


def diff(x, y):
    return 100 - (y*100/x)


def diffabs(x, y):
    return x-y


def stat_table1(pd, pd_qty, pd_receipt_qty):
    limit = len(pd)-1
    table = pandas.DataFrame({
                            'TURNOVER': [pd.values[limit].sum(), pd.values[0].sum()],
                          })
    table['PRODUCTS QYANTITY'] = [pd_qty.values[limit].sum(), pd_qty.values[0].sum()]
    table['RECEIPTS QYANTITY'] = [pd_receipt_qty.values[limit].sum(), pd_receipt_qty.values[0].sum()]
    table['AVERAGE RECEIPT'] = table['TURNOVER']/table['RECEIPTS QYANTITY']

    pre_len_table = len(table)
    len_table = pre_len_table + 1
    for name in table.columns:
        table = table.set_value(pre_len_table, name, diff(table.loc[0,name], table.loc[1,name]))
        table = table.set_value(len_table, name, diffabs(table.loc[0,name], table.loc[1,name]))
    table['INDEX'] = [
                         datetime.strftime(pd.index[limit], '%d-%m-%Y'),
                         datetime.strftime(pd.index[0], '%d-%m-%Y'),
                         'Difference, %',
                         'Difference'
                     ]
    table = table.set_index('INDEX')

    # table = pandas.DataFrame(table.values,
    #                          index=[datetime.strftime(pd.index[limit], '%d-%m-%Y'),
    #                                 datetime.strftime(pd.index[0], '%d-%m-%Y'),
    #                                 'Difference, %',
    #                                 'Difference'],
    #                          columns=list(table))

    return table


def get_table2(df, df_qty):
    limit_df = len(df) - 1
    report = pandas.DataFrame(df.values[limit_df]-df.values[0], index=df.columns, columns=['turnover`s change'])

    return report.to_html(classes="table table-hover table-striped",
                          float_format=lambda x: '%.2f' % x
                          )


def index(request):
    if request.session.has_key('key'):
        return HttpResponseRedirect(reverse('stat_form'))
    return render(request, 'statapp/index.html', {})


def login(request):
    if request.session.has_key('key'):
        return HttpResponseRedirect(reverse('stat_form'))
    if request.method == 'POST' and request.POST.get('submit_button') is not None:
        errors = {}

        data = {
            'MyClientID': request.POST.get('login'),
            'MyClientSecret': request.POST.get('password')
        }

        try:
            # if data["MyClientID"] and data["MyClientSecret"]:
            dw = datawiz.DW(data["MyClientID"], data["MyClientSecret"])
            # else:
            #     dw = datawiz.DW()
            data['dw'] = dw.get_client_info()
        except Exception as e:
            messages.error(request, "Please, type correct key and secret, %s" % e)
            errors['login'] = 'check key'
            errors['password'] = 'check secret'
            return render(request, 'statapp/login.html', {'errors': errors})

        request.session['key'] = data["MyClientID"]
        request.session['secret'] = data["MyClientSecret"]
        # request.session['name'] = data["dw"]['name']
        request.session['dw_info'] = data["dw"]
        request.session['dw'] = dw

        messages.info(request, "You've loged in")
        return HttpResponseRedirect(reverse('stat_form'))

    return render(request, 'statapp/login.html', {})


def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('index'))


def user_info(request):
    if  request.session.has_key('dw_info'):
        dw = request.session['dw_info']

        return render(request, 'statapp/user_info.html', {'dw': dw})

    return HttpResponseRedirect(reverse('index'))


def stat_form(request):
    if request.session.has_key('dw_info'):

        if request.method == 'POST' and request.POST.get('get_stat') is not None:
            form_data = request.POST
            data= {}
            errors = {}

            if form_data.get('date_from'):
                try:
                    data['date_from'] = datetime.strptime(form_data.get('date_from').strip(), '%d-%m-%Y')
                except Exception:
                    errors['date_from'] = 'Input date at DD-MM-YYYY format or left blank.'
            if form_data.get('date_to'):
                try:
                    data['date_to'] = datetime.strptime(form_data.get('date_to').strip(), '%d-%m-%Y')
                except Exception:
                    errors['date_to'] = 'Input date at DD-MM-YYYY format or left blank.'

            if form_data.getlist('shops'):
                data['shops'] = form_data.getlist('shops')

                for shop in form_data.getlist('shops'):
                    if not int(shop) in request.session['dw_info']['shops'].keys():
                        errors['shops'] = 'some shop is not available for you %s' % (shop)

            if errors:
                messages.error(request, 'Please correct errors!')
                return render(request, 'statapp/stat_form.html', {'errors': errors, "shops1": form_data.getlist(
                    'shops')})

            dw = request.session['dw']
            try:
                pandas_res_by_turnover = dw.get_categories_sale(**data)
                pandas_res_by_qty = dw.get_categories_sale(by='qty', **data)
                pandas_res_by_receipt_qty = dw.get_categories_sale(by='receipts_qty', **data)
            except Exception:
                messages.error(request, 'Try again because datawiz does not response!')
                return render(request, 'statapp/stat_form.html', {})

            # turnover = pandas_res.sum(axis=1)
            # dates = pandas_res.index
            # result = split_df(pandas_res_by_turnover.index, pandas_res_by_turnover.sum(axis=1),
            #                   pandas_res_by_qty.sum(axis=1), pandas_res_by_receipt_qty.sum(axis=1), 4)
            table1 = stat_table1(pandas_res_by_turnover, pandas_res_by_qty,
                                             pandas_res_by_receipt_qty)
            table2 = get_table2(df=pandas_res_by_turnover, df_qty=pandas_res_by_qty)

            return render(request, 'statapp/reports_stat.html', {
                            'show_tables': True, 'table1': table1.T.to_html(
                                classes="table table-hover table-striped",
                                float_format=lambda x: '%.2f' % x
                            ),
                            "shops": form_data.getlist('shops'),
                            "table2": table2})
        return render(request, 'statapp/stat_form.html', {})

    return HttpResponseRedirect(reverse('index'))


def reports_stat(request):
    return render(request, 'statapp/reports_stat.html', {})

def form(request):
    return render(request, 'statapp/form.html', {})