from django import template

register = template.Library()

def pandas_index_sum(object):

    return object.sum(axis=1)

register.filter('pandas_index_sum', pandas_index_sum)