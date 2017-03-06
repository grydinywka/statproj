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
                         pd.index[limit],
                         pd.index[0],
                         'Difference, %',
                         'Difference'
                     ]
    # table['INDEX'] = [
    #                      datetime.strftime(pd.index[limit], '%d-%m-%Y'),
    #                      datetime.strftime(pd.index[0], '%d-%m-%Y'),
    #                      'Difference, %',
    #                      'Difference'
    #                  ]
    table = table.set_index('INDEX')

    # table = pandas.DataFrame(table.values,
    #                          index=[datetime.strftime(pd.index[limit], '%d-%m-%Y'),
    #                                 datetime.strftime(pd.index[0], '%d-%m-%Y'),
    #                                 'Difference, %',
    #                                 'Difference'],
    #                          columns=list(table))

    return table


def get_table2(request, dw, data, pandas_res_by_turnover, cat_num):
    try:
        date_from = request.session['dw_info']['date_from']
        date_to = request.session['dw_info']['date_to']

        len_cat = len(pandas_res_by_turnover.columns)
        # categ = [item for item in pandas_res_by_turnover.columns[0:len_cat-4]]
        # categ = [item for item in pandas_res_by_turnover.columns[len_cat-4:len_cat]]
        categ = pandas_res_by_turnover.columns[cat_num]
        name_category = dw.get_category(categories=[categ])['category_name']
        # print name_category
        if data.has_key('date_from'):
            pandas_prod_turn1 = dw.get_products_sale(date_from=data['date_from'], date_to=data['date_from'],
                                                     categories=categ, show="name")
            pandas_prod_qty1 = dw.get_products_sale(by='qty', date_from=data['date_from'], date_to=data['date_from'],
                                                  categories=categ, show="name")
        else:
            pandas_prod_turn1 = dw.get_products_sale(date_from=date_from, date_to=date_from,
                                                     categories=categ, show="name")
            pandas_prod_qty1 = dw.get_products_sale(by='qty', date_from=date_from, date_to=date_from,
                                                  categories=categ, show="name")
        if data.has_key('date_to'):
            pandas_prod_turn2 = dw.get_products_sale(date_from=data['date_to'],date_to=data['date_to'],
                                                     categories=categ, show="name")
            pandas_prod_qty2 = dw.get_products_sale(by='qty', date_from=data['date_to'], date_to=data['date_to'],
                                                  categories=categ, show="name")
        else:
            pandas_prod_turn2 = dw.get_products_sale(date_from=date_to,date_to=date_to,
                                                     categories=categ, show="name")
            pandas_prod_qty2 = dw.get_products_sale(by="qty",date_from=date_to,date_to=date_to,
                                                  categories=categ, show="name")
    except Exception as e:
        messages.error(request, str(e))
        # messages.error(request, 'Try again because datawiz does not response! ' + str(e))
        return render(request, 'statapp/stat_form.html', {})

    if pandas_prod_turn1.sum().sum() == 0 and pandas_prod_turn2.sum().sum() == 0:
        return pandas.DataFrame().to_html(), pandas.DataFrame().to_html(), name_category
    elif pandas_prod_turn1.sum().sum() == 0:
        report = pandas.DataFrame(pandas_prod_qty2.columns, columns=['product'])
        report['change selling'] = pandas_prod_qty2.values[0]
        # report = pandas.DataFrame(pandas_prod_qty2, index=pandas_prod_qty2.columns, columns=['change selling'])
        report['turnover`s change'] = pandas_prod_turn2.values[0]
        report = report.fillna(0)
        report = report.loc[(report != 0).any(1)]
        return report.to_html(index=False, classes="table table-hover table-striped",
                          float_format=lambda x: '%.2f' % x), pandas.DataFrame().to_html(), name_category
    elif pandas_prod_turn2.sum().sum() == 0:
        report = pandas.DataFrame(pandas_prod_qty1.columns, columns=['product'])
        report['change selling'] = pandas_prod_qty1
        # report = pandas.DataFrame(pandas_prod_qty1, index=pandas_prod_qty1.columns, columns=['change selling'])
        report['turnover`s change'] = pandas_prod_turn1.values[0]
        report = report.fillna(0)
        report = report.loc[(report != 0).any(1)]
        return pandas.DataFrame().to_html(), report.to_html(index=False, classes="table table-hover table-striped",
                          float_format=lambda x: '%.2f' % x), name_category
    else:
        concat_df_turn = pandas.concat([pandas_prod_turn1,pandas_prod_turn2,pandas_prod_qty1,pandas_prod_qty2])
        concat_df_turn = concat_df_turn.fillna(0)

        report = pandas.DataFrame(concat_df_turn.columns, columns=['product'])
        report['change selling'] = concat_df_turn.values[3]-concat_df_turn.values[2]
        # report = pandas.DataFrame(concat_df_turn.values[3]-concat_df_turn.values[2],
        #                           index=concat_df_turn.columns, columns=['change selling'])
        report['turnover`s change'] = concat_df_turn.values[1]-concat_df_turn.values[0]
    report.index.name = 'product'
    report = report.loc[(report != 0).any(1)] # drop zero row

    # report = report.sort_values(by="change selling",ascending=0)
    report_inc = report.loc[report['change selling'] > 0]
    report_dec = report.loc[report['change selling'] < 0]

    return report_inc.to_html(classes="table table-hover table-striped", index=False,
                          float_format=lambda x: '%.2f' % x
                          ),\
           report_dec.to_html(classes="table table-hover table-striped", index=False,
                          float_format=lambda x: '%.2f' % x
                          ), name_category


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
            if data["MyClientID"] or data["MyClientSecret"]:
                dw = datawiz.DW(data["MyClientID"], data["MyClientSecret"])
            else:
                dw = datawiz.DW()
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


def date_trunc(date):
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


# @cache_page(900)
def reports_stat(request):
    if request.method == 'POST' and request.POST.get('get_stat') is not None:
        form_data = request.POST
        data= {}
        errors = {}
        # dw = request.session['dw']
        dw = datawiz.DW()

        cat_num = form_data.get('cat_num', '1')
        # print "CAT_NAME", name_category

        if form_data.get('date_from'):
            try:
                data['date_from'] = datetime.strptime(form_data.get('date_from').strip(), '%d-%m-%Y')
            except Exception:
                errors['date_from'] = 'Input date at DD-MM-YYYY format or left blank.'
            else:
                if date_trunc(data['date_from']) > date_trunc(request.session['dw_info']['date_to']):
                    errors['date_from'] = '`Date from` do not allow be more than %s' % (datetime.strftime(
                        request.session['dw_info']['date_to'], '%d-%m-%Y')
                    )
                elif date_trunc(data['date_from']) < date_trunc(request.session['dw_info']['date_from']):
                    errors['date_from'] = '`Date from` do not allow be less than %s' % (datetime.strftime(
                        request.session['dw_info']['date_from'], '%d-%m-%Y')
                    )
        else:
            errors['date_from'] = 'Date from field is required!'

        if form_data.get('date_to'):
            try:
                data['date_to'] = datetime.strptime(form_data.get('date_to').strip(), '%d-%m-%Y')
            except Exception:
                errors['date_to'] = 'Input date at DD-MM-YYYY format or left blank.'
            else:
                if date_trunc(data['date_to']) < date_trunc(request.session['dw_info']['date_from']):
                    errors['date_to'] = '`Date to` do not allow be less than %s' % (datetime.strftime(
                        request.session['dw_info']['date_from'], '%d-%m-%Y'),
                    )
                elif date_trunc(data['date_to']) > date_trunc(request.session['dw_info']['date_to']):
                    errors['date_to'] = '`Date to` do not allow be more than %s' % (datetime.strftime(
                        request.session['dw_info']['date_to'], '%d-%m-%Y')
                    )
        else:
            errors['date_to'] = 'Date to field is required!'

        if form_data.get('date_from') and form_data.get('date_to'):
            if data['date_to'] < data['date_from']:
                if errors.has_key('date_from'):
                    errors['date_from'] += '. Date from must more or equal to Date to'
                else:
                    errors['date_from'] = 'Date from must more or equal to Date to'

        if form_data.getlist('shops') and form_data.getlist('shops') != [u'']:

            data['shops'] = form_data.getlist('shops')
            # print data['shops'], "DATASHOP"
            for shop in form_data.getlist('shops'):
                if not int(shop) in request.session['dw_info']['shops'].keys():
                    errors['shops'] = 'some shop is not available for you %s' % (shop)
        else:
            print form_data.get('shops'), "DATASHOP"

        if errors:
            messages.error(request, 'Please correct errors!')
            return render(request, 'statapp/stat_form.html', {'errors': errors, "shops1": form_data.getlist(
                'shops')})

        try:
            pandas_res_by_turnover = dw.get_categories_sale(show='id', **data)
            pandas_res_by_qty = dw.get_categories_sale(by='qty', **data)
            pandas_res_by_receipt_qty = dw.get_categories_sale(by='receipts_qty', **data)

        except Exception as e:
            # messages.error(request, 'Try again because datawiz does not response! ' + str(e))
            messages.error(request, str(e) + '1')
            return render(request, 'statapp/stat_form.html', {})

        table1 = stat_table1(pandas_res_by_turnover, pandas_res_by_qty,
                                         pandas_res_by_receipt_qty)
        table2, table3, name_category = get_table2(request, dw, data, pandas_res_by_turnover, int(cat_num))

        cat_val = len(pandas_res_by_turnover.columns)

        # end_loading = False
        # cat_num = int(cat_num) + 1
        # if cat_num >= cat_val:
        #     end_loading = True

        return render(request, 'statapp/reports_stat.html', {
                        'show_tables': True, 'table1': table1.T.to_html(
                            classes="table table-hover table-striped",
                            float_format=lambda x: '%.2f' % x
                        ),
                        "shops": form_data.getlist('shops'),
                        "table2": table2, "table3": table3, 'cat_val': cat_val-1,
                        "name_category": name_category
        })
    return HttpResponseRedirect(reverse('stat_form'))


def form(request):
    return render(request, 'statapp/form.html', {})