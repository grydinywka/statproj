from datetime import datetime

import requests_cache
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from dwapi import datawiz
import pandas
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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


# def boundsReport(objects, valObjOnPage, request):
#     allObjects = len(objects)
#     if allObjects <= valObjOnPage and allObjects > 0:
#         valObjOnPage = allObjects
#     valPage = allObjects/valObjOnPage
#     valStudOnLastPage = allObjects % valObjOnPage
#     if valStudOnLastPage != 0:
#         valPage += 1
#
#     page = request.GET.get('page', 1)
#     print 'page =', page
#     try:
#         page = int(float(page))
#     except ValueError:
#         page = 1
#     if page > valPage:
#         page = valPage
#     if  page < 1:
#         page = 1
#
#     if page == valPage:
#         large = allObjects
#         if valStudOnLastPage > 0:
#             little = large - valStudOnLastPage
#         else:
#             little = large - valObjOnPage
#     else:
#         large = valObjOnPage*page
#         little = large - valObjOnPage
#
#     if little < 0:
#         little = 0
#     if large < 0:
#         large = 0
#
#     return little, large

def get_table2(request, dw, data, pandas_res_by_turnover, df_qty2):
    try:
        date_from = request.session['dw_info']['date_from']
        date_to = request.session['dw_info']['date_to']
        if data.has_key('date_from'):
            pandas_prod_turn1 = dw.get_products_sale(date_from=data['date_from'], date_to=data['date_from'], categories=pandas_res_by_turnover.columns[0])
            pandas_prod_qty1 = dw.get_products_sale(by='qty', date_from=data['date_from'], date_to=data['date_from'],
                                                  categories=pandas_res_by_turnover.columns[0])
        else:
            pandas_prod_turn1 = dw.get_products_sale(date_from=date_from, date_to=date_from, categories=pandas_res_by_turnover.columns[0])
            pandas_prod_qty1 = dw.get_products_sale(by='qty', date_from=date_from, date_to=date_from,
                                                  categories=pandas_res_by_turnover.columns[0])
        if data.has_key('date_to'):
            pandas_prod_turn2 = dw.get_products_sale(date_from=data['date_to'],date_to=data['date_to'], categories=pandas_res_by_turnover.columns[0])
            pandas_prod_qty2 = dw.get_products_sale(by='qty', date_from=data['date_to'], date_to=data['date_to'],
                                                  categories=pandas_res_by_turnover.columns[0])
        else:
            pandas_prod_turn2 = dw.get_products_sale(date_from=date_to,date_to=date_to, categories=pandas_res_by_turnover.columns[0])
            pandas_prod_qty2 = dw.get_products_sale(by="qty",date_from=date_to,date_to=date_to,
                                                  categories=pandas_res_by_turnover.columns[0])
    except Exception:
        messages.error(request, 'Try again because datawiz does not response!')
        return render(request, 'statapp/stat_form.html', {})

    concat_df_turn = pandas.concat([pandas_prod_turn1,pandas_prod_turn2,pandas_prod_qty1,pandas_prod_qty2])
    concat_df_turn = concat_df_turn.fillna(0)
    # concat_df_qty = pandas.concat([pandas_prod_qty1,pandas_prod_qty2])
    # concat_df_qty = concat_df_qty.fillna(0)
    limit = len(concat_df_turn) - 1
    report = pandas.DataFrame(concat_df_turn.values[1]-concat_df_turn.values[0],
                              index=concat_df_turn.columns, columns=['turnover`s change'])
    report['change selling'] = concat_df_turn.values[limit]-concat_df_turn.values[2]
    report = report.loc[(report != 0).any(1)] # drop zero row
    # print report[:]
    # pagination

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
        return render(request, 'statapp/stat_form.html', {})

    return HttpResponseRedirect(reverse('index'))


# @cache_page(900)
def reports_stat(request):
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
            pandas_res_by_turnover = dw.get_categories_sale(show='id', **data)
            pandas_res_by_qty = dw.get_categories_sale(by='qty', **data)
            pandas_res_by_receipt_qty = dw.get_categories_sale(by='receipts_qty', **data)
            #   by products
            # date_from = request.session['dw_info']['date_from']
            # date_to = request.session['dw_info']['date_to']
            # if data.has_key('date_from'):
            #     pandas_prod_turn1 = dw.get_products_sale(date_from=data['date_from'], date_to=data['date_from'], categories=pandas_res_by_turnover.columns[0])
            # else:
            #     pandas_prod_turn1 = dw.get_products_sale(date_from=date_from, date_to=date_from, categories=pandas_res_by_turnover.columns[0])
            # if data.has_key('date_to'):
            #     pandas_prod_turn2 = dw.get_products_sale(date_from=data['date_to'],date_to=data['date_to'], categories=pandas_res_by_turnover.columns[0])
            # else:
            #     pandas_prod_turn2 = dw.get_products_sale(date_from=date_to,date_to=date_to, categories=pandas_res_by_turnover.columns[0])
        except Exception:
            messages.error(request, 'Try again because datawiz does not response!')
            return render(request, 'statapp/stat_form.html', {})

        # turnover = pandas_res.sum(axis=1)
        # dates = pandas_res.index
        # result = split_df(pandas_res_by_turnover.index, pandas_res_by_turnover.sum(axis=1),
        #                   pandas_res_by_qty.sum(axis=1), pandas_res_by_receipt_qty.sum(axis=1), 4)
        table1 = stat_table1(pandas_res_by_turnover, pandas_res_by_qty,
                                         pandas_res_by_receipt_qty)
        table2 = get_table2(request, dw, data, pandas_res_by_turnover, pandas_res_by_qty)

        return render(request, 'statapp/reports_stat.html', {
                        'show_tables': True, 'table1': table1.T.to_html(
                            classes="table table-hover table-striped",
                            float_format=lambda x: '%.2f' % x
                        ),
                        "shops": form_data.getlist('shops'),
                        "table2": table2
        })
    return HttpResponseRedirect(reverse('stat_form'))


def form(request):
    return render(request, 'statapp/form.html', {})