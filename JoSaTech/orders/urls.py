from django.conf.urls import url
from . import views

app_name = 'orders'

urlpatterns = [
    url(r'^$', views.Index, name='index'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login_user/$', views.login_user, name='login_user'),
    url(r'^logout_user/$', views.logout_user, name='logout_user'),
    url(r'^orderbook/$', views.OrderBook, name='orderbook'),
    url(r'^dealjournal/$', views.DealJournal, name='dealjournal'),
    url(r'^add_order/$', views.add_order, name='add_order'),
    url(r'^(?P<order_id>[0-9]+)/delete_order/$', views.delete_order, name='delete_order'),
    url(r'^(?P<trade_id>[0-9]+)/delete_trade/$', views.delete_trade, name='delete_trade'),
    url(r'^exchange/$', views.exchange, name='exchange'),
    url(r'^portfolio/$', views.portfolio, name='portfolio'),
    url(r'^delete_all/$', views.delete_all, name='delete_all'),
    url(r'^randomize/$', views.randomize, name='randomize')
]
