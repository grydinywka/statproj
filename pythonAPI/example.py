'''
Приклад роботи с datawiz API
'''

import datetime

from dwapi import datawiz

date_from = datetime.date(2015, 8, 9)
date_to = datetime.date(2015, 9, 12)

# Створення классу для вибору данних:
# datawiz.DW(API_KEY, API_SECRET) 
# якщо де API_KEY, API_SECRET - ключ і підпис користувача, якщо вони не задані то запускаємо для тестового користувача.
dw = datawiz.DW()

print dw.get_products_sale(products = [2855561, 2861880], by='turnover',
						   shops = [601,641,595],
						   date_from = date_from,
						   date_to = date_to,
						   interval = datawiz.WEEKS)
