__author__ = 'arya'
# I moved all the "Logical" functions to this file since I assumed it would makes the views a lot less crowded
# Couldn't find anything in the django book on what to do with helper functions
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
        self.weeksales = [0 for x in range(7)]

class Week:
    def __init__(self,date,pname):
        self.date = date
        self.name = "Week of "+date.ctime()
        self.sales=[0 for x in range(7)]
        self.productname=pname

class Product:
    #Stores information about a cetain product
    def __init__(self,name,price,iden):
        self.name=name
        self.price=float(price)
        self.sales=0
        self.iden=iden

def last_sunday(date):
    #Given a date, it returns the date rolled back to the last wednesday
    dt = datetime.timedelta(days=1)
    while date.weekday()!=6:
        date=date-dt
    return date

def last_wednesday(date):
    #Given a date, it returns the date rolled back to the last wednesday
    dt = datetime.timedelta(days=1)
    while date.weekday()!=2:
        date=date-dt
    return date

def day_to_string(date):
    """Given a date, it returns the string that the gmp uses"""
    ms = {0: '', 1: 'January', 2: 'February', 3: 'March', 4:
          'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
          9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    return str(ms[date.month])+" "+str(date.day)+" "+str(date.year)

def day_to_string2(date):
    """
    Similar to 1st method, but sometimes gmp has 2 digits for the date
    even if it's a single digit day, this accounts for that"""
    d = str(date.day)
    if len(d)==1: d="0"+d
    ms = {0: '', 1: 'January', 2: 'February', 3: 'March', 4:
          'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
          9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    return str(ms[date.month])+" "+d+" "+str(date.year)

def gmp_sales_data(filter, weeks_to_check):
    sales = {} #accounts for # of sales
    daystocheck = [] #stores the days to check
    temp = datetime.date(1,1,1)
    today = temp.today() #date object showing today's date
    wed= last_wednesday(today) #the wednesday before this
    week  = datetime.timedelta(weeks=1) #difference in time of 1 week
    weekwed = wed#-week #the wednesday before that (to report) -- taken out cause we now want current week
    for i in range(weeks_to_check):
        #for 8 weeks store the date and then roll back a week
        daystocheck.append(weekwed)
        weekwed = weekwed-week

    #List of strings to check for dates
    daystocheck1 = [day_to_string(i) for i in daystocheck]
    daystocheck2 = [day_to_string2(i) for i in daystocheck]


    ##Stuff to be deleted later, using system variables
    DPD_API_PASSWORD=settings.DPD_API_PASSWORD
    DPD_API_USERNAME=settings.DPD_API_USERNAME
    dpd_api_uri = 'https://api.getdpd.com/v2/'
    dpd_purchases = "https://api.getdpd.com/v2/purchases"
    dpd_products = "https://api.getdpd.com/v2/products"
    credentials = (DPD_API_USERNAME,DPD_API_PASSWORD)
    #payload = {'customer_email': "scott@happyherbivore.com"}
    #payload = {'storefront_id': "17244", 'date_min':'1392803004'}


    pd = requests.get(dpd_products, auth=credentials, params=None)
    prod_data=json.loads(pd.text) #JSON for each product (now in a dict)

    for product in prod_data:

        if product['storefront_id'] == 17244: #If it is in the gmp store
            n = product['name']
            L = n.split(" ")[-3:]
            day = " ".join(L) #Just takes the date part of the string
            if ((day in daystocheck2) or (day in daystocheck1)) and (filter in n.lower()):
                try:
                    da=daystocheck1.index(day)
                except ValueError:
                    da=daystocheck2.index(day)
                #If it's a date in the past 8 weeks we will keep track of it
                i = product['id']
                #Adds it to sales dictionary
                sales[i]=GMPProduct(product['name'],product['price'],i)

    for pid in sales.keys():
        #For each of the products we were told to check
        payload = {'storefront_id': "17244", 'product_id':pid} #gets all purchases of product
        dpd_customer_data = requests.get(dpd_purchases, auth=credentials, params=payload)
        dpd_customer_sales = json.loads(dpd_customer_data.text) #JSON to list of dicts of the products
        for sale in dpd_customer_sales:
            try:
                if sale['status']=='ACT':
                    date_created = (datetime.datetime.fromtimestamp(int(sale['created_at'])-18000)).weekday() #18000 for timezone
                    sales[pid].weeksales[(date_created-2)%7]+=float(sale['subtotal'])
            except TypeError:
                print sale
    TL = sales.keys()[:]
    TL.sort(reverse=True)

    return sales

def misc_sales_data(store, product_number, weeks_to_check):
    stores=[15846,18388,17242] #R&C, #HH, #ESS
    storenames={15846:"Reboot & Cleanse",18388:"Happy Herbivore",17242:"Exit Strategy School"}
    sales = {} #accounts for # of sales
    daystocheck = [] #stores the days to check
    temp = datetime.datetime(1,1,1)
    today = temp.today() #date object showing today's date
    today = today.replace(hour=0,minute=0,second=0,microsecond=0)

    wed= last_sunday(today) #the wednesday before this
    week  = datetime.timedelta(weeks=1) #difference in time of 1 week
    weekwed = wed
    for i in range(weeks_to_check):
        daystocheck.append(weekwed)
        weekwed = weekwed-week

    DPD_API_PASSWORD=settings.DPD_API_PASSWORD
    DPD_API_USERNAME=settings.DPD_API_USERNAME

    dpd_api_uri = 'https://api.getdpd.com/v2/'
    dpd_purchases = "https://api.getdpd.com/v2/purchases"
    dpd_products = "https://api.getdpd.com/v2/products"
    credentials = (DPD_API_USERNAME,DPD_API_PASSWORD)
    pd = requests.get(dpd_products, auth=credentials, params=None)
    prod_data=json.loads(pd.text) #list of dictionaries of product info

    for product in prod_data:
        #For each product
        if product['storefront_id'] == stores[store-1]: #If it is in the store checked
            i = product['id']
            #Adds it to sales dictionary
            sales[i]=Product(product['name'],product['price'],i)
    pid=sorted(sales.keys())[product_number-1]
    weeksales = {}
    for date in daystocheck:
        weeksales[date]=Week(date,sales[pid].name)
        week=datetime.timedelta(days=6, hours=8, minutes=0)
        payload = {'storefront_id': str(stores[store-1]), 'product_id':pid, 'date_min':date.ctime(), 'date_max':(date+week).ctime()} #Loop over it here
        dpd_customer_data = requests.get(dpd_purchases, auth=credentials, params=payload)

        if len(dpd_customer_data.text)>0: #If it sold any
            dpd_customer_sales = json.loads(dpd_customer_data.text) #JSON to dict
            for sale in (dpd_customer_sales):
                if type(sale) is dict: #Again if it sells any
                    if sale['status']=='ACT':
                        date_created = (datetime.datetime.fromtimestamp(int(sale['created_at']))).weekday()
                        weeksales[date].sales[(date_created-2)%7]+=(float(sale['subtotal']))

    return [storenames[stores[store-1]], sales[pid].name, weeksales]