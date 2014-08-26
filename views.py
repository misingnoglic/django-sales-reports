from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from logic import *
from forms import *

from django.views.decorators.cache import cache_page

@cache_page(60 * 60)
def gmp_data(request, filter, weeks_to_check=8):
    """
    The view that creates the sales chart for GMP

    :param filter: family vs individual
    :param weeks_to_check: how many weeks to check (defaults to 8)
    :return: rendered chart
    """

    if request.method == 'POST': #If there was a POST request for a new number of weeks

        form = WeeksToCheckDropdown(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            n = str(data['weeks_to_check'])
            return HttpResponseRedirect(n+"/") #changes the # of weeks
        else:
            HttpResponse("Bad Form")
    #Because of how Highcharts works I need to organize like this:
    else: #to generate the chart

        #Create a separate array for each day of the week (this could have been done better)
        wed = []
        thurs = []
        fri = []
        sat = []
        sun = []
        mon = []
        tues = []
        names = []


        sales = gmp_sales_data(filter, int(weeks_to_check)) # imported from logic.py
        id_list = sales.keys()[:]

        #orders the product IDs
        id_list.sort(reverse=True)

        for product_id in id_list:
            #Add the number of sales for each week to the weekdays
            #This is confusing, but because of the way highcharts works the data needs to be
            #separated like this

            L = sales[product_id].weeksales
            names.append(sales[product_id].name) #Stores the week in the same order as the sale
            wed.append(L[0])
            thurs.append(L[1])
            fri.append(L[2])
            sat.append(L[3])
            sun.append(L[4])
            mon.append(L[5])
            tues.append(L[6])

        processed_name = [str(name) for name in names]

        context = dict(wed=str(wed), thurs=str(thurs), fri=str(fri), sat=str(sat), sun=str(sun), mon=str(mon),
                       tues=str(tues), names=str(processed_name)) #array passed as string so Javascript can deal with it

        context['filter']=str(filter)

        form = WeeksToCheckForm()
        form2 = WeeksToCheckDropdown()

        context['form']=form
        context['form2']=form2
        return render(request,'reports/gmpreport.html',context)

def index(request):
    """
    Creates the index view with links to all the charts
    """


    DPD_API_PASSWORD=settings.DPD_API_PASSWORD
    DPD_API_USERNAME=settings.DPD_API_USERNAME
    dpd_products = "https://api.getdpd.com/v2/products"
    credentials = (DPD_API_USERNAME,DPD_API_PASSWORD)
    pd = requests.get(dpd_products, auth=credentials, params=None)
    prod_data=json.loads(pd.text)  # list of dictionaries of product info

    rcprods=[]
    hhprods=[]
    ess=[]

    sid = 15846
    for product in prod_data:
        if product['storefront_id'] == sid: # If it is in the R&C store - adds
            rcprods.append(product['name'])

    sid = 18388
    for product in prod_data:
        if product['storefront_id'] == sid: # If it is in the HH store
            hhprods.append(product['name'])

    sid = 17242
    for product in prod_data:
        if product['storefront_id'] == sid: # If it is in the ESS store
            ess.append(product['name'])

    context = {'rcprods':list(enumerate(rcprods, start=1)), 'hhprods':list(enumerate(hhprods, start=1)),
               'ess':list(enumerate(ess, start=1))}
    return render(request,'reports/directory.html',context)


@cache_page(60 * 60)
def misc_data(request, store, product_number, weeks_to_check=3):
    """
    View to make the non GMP charts. Again because of the way the data is structured the method needs
    to be significantly different to deal with it.

    :param store: Store number
    :param product_number: Product Number
    :param weeks_to_check: Number of weeks to check
    :return: Rendered page with chart of product sales
    """
    '''view to make the Non-GMP Charts'''
    if request.method == 'POST':
        form = WeeksToCheckForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            n = str(data['weeks_to_check'])
            print n
            return HttpResponseRedirect(n+"/")

    else:
        wed=[]
        thurs=[]
        fri=[]
        sat=[]
        sun=[]
        mon=[]
        tues=[]
        names = []
        try:
            sales = misc_sales_data(int(store), int(product_number), int(weeks_to_check))
        except IndexError:
            #These should only return if people are typing their own URLs
            return HttpResponse("Sorry, the product or store you selected is not existent")
        storename = sales[0]
        pname = sales[1]
        sales = sales[2]

        IDs = sales.keys()[:]
        IDs.sort(reverse=True)


        for product_id in IDs:
            L = sales[product_id].sales[:] #copy of the list
            L = [round(i,2) for i in L] #rounds all the sales numbers (weird prices)
            names.append(sales[product_id].name)
            wed.append(L[0])
            thurs.append(L[1])
            fri.append(L[2])
            sat.append(L[3])
            sun.append(L[4])
            mon.append(L[5])
            tues.append(L[6])
        processed_names = [str(name) for name in names]
        context = {'wed': str(wed), "thurs": str(thurs), "fri": str(fri), "sat": str(sat),
                    "sun": str(sun), "mon": str(mon), "tues": str(tues), "names": str(processed_names),
                    "pname":pname, "storename":storename}

        context['store'] = str(store)
        context['product_number']=str(product_number)
        form = WeeksToCheckForm()
        context['form']=form


        return render(request,'reports/miscreport.html',context)
