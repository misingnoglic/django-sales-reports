from django.conf.urls import patterns, url

from reports import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<filter>family|individual|^)/(?P<weeks_to_check>\d+)/$', views.gmp_data, name='bars'),

    url(r'^(family|individual|^)/$', views.gmp_data, name='bars-weeks'),

    url(r'^(?P<store>[0-9]{1})/(?P<product_number>[0-9]{1})/(?P<weeks_to_check>\d+)/$', views.misc_data, name='chart'),

    url(r'^([0-9]{1})/([0-9]{1})/$', views.misc_data, name='chart-weeks')
)
