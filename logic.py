__author__ = 'arya'

"""
This is where I kept all the 'logic' helper functions. This is where most
of the boring converting data happens, and I didn't want to crowd the view with them.
"""

import requests
import json
import os
import datetime
from django.conf import settings


class GMPProduct:
    #Stores information about a GMP week's sales
    def __init__(self,name,price,iden):
        self.name=name
        self.price=float(price)
        self.sales=0
        self.iden=iden
        self.weeksales = [0 for x in range(7)] #initializes 0 sales per day of week

class Week:
    def __init__(self,date,pname):
        self.date = date
        self.name = "Week of "+date.ctime()
        self.sales=[0 for x in range(7)]
        self.productname=pname

class Product:
    """Stores information about a cetain product"""
    def __init__(self,name,price,iden):
        self.name=name
        self.price=float(price)
        self.sales=0
        self.iden=iden

def last_sunday(date):
    """
    Given a date, it returns the date rolled back to the last sunday
    """
    dt = datetime.timedelta(days=1)
    while date.weekday()!=6:
        date=date-dt
    return date

def last_wednesday(date):
    """
    Given a date, it returns the date rolled back to the last wednesday
    This is useful because the meal plans for GMP begin sales on wednesday
    """
    dt = datetime.timedelta(days=1)
    while date.weekday()!=2:
        date=date-dt
    return date

def day_to_string(date):
    """
    Given a date, it returns the string that the gmp uses to convey that date
    """
    ms = {0: '', 1: 'January', 2: 'February', 3: 'March', 4:
          'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
          9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    return str(ms[date.month])+" "+str(date.day)+" "+str(date.year)

def day_to_string2(date):
    """
    Similar to 1st method, but sometimes gmp has 2 digits for the date
    even if it's a single digit day, this accounts for that
    """
    d = str(date.day)
    if len(d)==1: d="0"+d #extra 0 in front of single digit date
    ms = {0: '', 1: 'January', 2: 'February', 3: 'March', 4:
          'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
          9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    return str(ms[date.month])+" "+d+" "+str(date.year)

def gmp_sales_data(filter, weeks_to_check):
    """
    Because the meal plans
    :param filter: either 'individual' or 'family' (pertaining to the type of meal plan)
    :param weeks_to_check: How many weeks should be displayed on the chart
    :return: Dictionary of number of sales
    """

    sales = {} #accounts for # of sales
    days_to_check = [] #stores the days to check
    temp = datetime.date(1,1,1) #Random date to find today with
    today = temp.today()
    wednesday = last_wednesday(today) #the wednesday before Today

    one_week  = datetime.timedelta(weeks=1) #difference in time of 1 week
    for i in range(weeks_to_check):
        #for 8 weeks store the date and then roll back a week
        days_to_check.append(wednesday)
        wednesday = wednesday-one_week

    #List of strings to check for dates
    #both naming conventions are used because the meal plans are named differently
    daystocheck1 = [day_to_string(i) for i in days_to_check]
    daystocheck2 = [day_to_string2(i) for i in days_to_check]

    days_to_check = daystocheck1+daystocheck2


    DPD_API_PASSWORD=settings.DPD_API_PASSWORD
    DPD_API_USERNAME=settings.DPD_API_USERNAME
    dpd_api_uri = 'https://api.getdpd.com/v2/'
    dpd_purchases = "https://api.getdpd.com/v2/purchases"
    dpd_products = "https://api.getdpd.com/v2/products"
    credentials = (DPD_API_USERNAME,DPD_API_PASSWORD)

    json_sales_data = requests.get(dpd_products, auth=credentials, params=None)
    sales_data=json.loads(json_sales_data.text) #JSON for each product (now in a dict)
    for product in sales_data:
        if product['storefront_id'] == 17244: #If it is in the gmp store
            product_name = product['name']
            L = product_name.split(" ")[-3:] #last 3 tokens of product name (the date)
            meal_plan_date = " ".join(L) #Just takes the date part of the string
            if ((meal_plan_date in days_to_check) and (filter in product_name.lower())):
            #Filter is the type of meal plan (family vs individual)

                i = product['id']
                #Adds it to sales dictionary
                sales[i]=GMPProduct(product_name,product['price'],i)

    for pid in sales.keys():
        #For each of the products we were told to check
        payload = {'storefront_id': "17244", 'product_id':pid} #gets all purchases of product
        dpd_customer_data = requests.get(dpd_purchases, auth=credentials, params=payload)
        dpd_customer_sales = json.loads(dpd_customer_data.text) #JSON to list of dicts of the products
        for sale in dpd_customer_sales:
            try:
                if sale['status']=='ACT': #If the sale is active (not returned)
                    date_created = (datetime.datetime.fromtimestamp(int(sale['created_at'])-18000)).weekday()
                    #-18000 is for the timezone shift
                    sales[pid].weeksales[(date_created-2)%7]+=float(sale['subtotal'])
                    #Subtracting 2 from date to make it wednesday-centric
            except TypeError:
                #Sometimes there are no sales and it returns a string instead of a dictionary, this is ignored
                pass
    TL = sales.keys()[:]
    TL.sort(reverse=True)

    return sales

def misc_sales_data(store, product_number, weeks_to_check):
    """
    This method is very similar to the gmp_sales_data, but the logic for the other stores
    is a little different (as the date is gotten from the DPD sales data, not the name)

    There is a lot of repeat code but there's enough different to warrant a new method.

    :param store: The store to check (a number 1-3)
    :param product_number: Which product to check in the store (number depends on how many products)
    :param weeks_to_check: How many weeks to display on the graph
    :return: List with relevant data for chart
    """


    stores=[15846,18388,17242] #R&C, #HH, #ESS - the store names
    storenames={15846:"Reboot & Cleanse",18388:"Happy Herbivore",17242:"Exit Strategy School"}
    sales = {} #accounts for # of sales
    days_to_check = [] #stores the days to check

    temp = datetime.datetime(1,1,1) #temporary to get today's date

    today = temp.today()  # date object showing today's date
    today = today.replace(hour=0,minute=0,second=0,microsecond=0) #to account for timezone oddities

    sunday= last_sunday(today) #the Sunday before Today
    one_week  = datetime.timedelta(weeks=1) #difference in time of 1 week

    for product_id in range(weeks_to_check):
        days_to_check.append(sunday)
        sunday = sunday-one_week

    DPD_API_PASSWORD=settings.DPD_API_PASSWORD
    DPD_API_USERNAME=settings.DPD_API_USERNAME

    dpd_purchases = "https://api.getdpd.com/v2/purchases"

    dpd_products = "https://api.getdpd.com/v2/products"

    credentials = (DPD_API_USERNAME,DPD_API_PASSWORD)
    json_sales_data = requests.get(dpd_products, auth=credentials, params=None)
    sales_data=json.loads(json_sales_data.text) #list of dictionaries of product info

    for product in sales_data:
        #For each product
        if product['storefront_id'] == stores[store-1]:
        #If it is in the store checked (-1 to account for 0 indexing)
            product_id = product['id']
            #Adds it to sales dictionary
            sales[product_id]=Product(product['name'],product['price'],product_id)
    product_id=sorted(sales.keys())[product_number-1] #The product being checked

    weeksales = {} #the dictionary of the sales for the week

    for date in days_to_check:
        weeksales[date]=Week(date,sales[product_id].name)
        one_week=datetime.timedelta(days=6, hours=8, minutes=0) #To factor for timezone issues
        payload = {'storefront_id': str(stores[store-1]), 'product_id':product_id, 'date_min':date.ctime(),
                   'date_max':(date+one_week).ctime()} #requests all the sales for that week
        dpd_customer_data = requests.get(dpd_purchases, auth=credentials, params=payload)

        if len(dpd_customer_data.text)>0: #If it sold any
            dpd_customer_sales = json.loads(dpd_customer_data.text) #JSON to dict
            for sale in (dpd_customer_sales):
                if type(sale) is dict: #Another test for sale (debugging)
                    if sale['status']=='ACT':
                        date_created = (datetime.datetime.fromtimestamp(int(sale['created_at']))).weekday()
                        weeksales[date].sales[(date_created-2)%7]+=(float(sale['subtotal'])) #stores the sale

    return [storenames[stores[store-1]], sales[product_id].name, weeksales]