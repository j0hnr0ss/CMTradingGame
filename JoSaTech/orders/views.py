from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Permission, User
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order, Trade, Price
from random import choice, randint
from datetime import datetime
from .forms import OrderForm, UserForm
from collections import defaultdict, OrderedDict
#import schedule
import time
from graphos.sources.model import ModelDataSource
from graphos.renderers.gchart import LineChart
from django.contrib import messages


Shares = Price.objects.values_list('share_name', flat=True)
ClosePrices = Price.objects.values_list('close_price', flat=True)
Funds = ['JRAM','Fundlicious','Sanguard','HotnFund','Fundrama','RoboFund']
StartValue = 100000
diversification_threshold = 5 #percent per share
diversification_bonus = 10000
random_market = False

def Random_Ross():
    orderIDs = Order.objects.values_list('order_id', flat=True)
    order_id = orderIDs.last() + 1
    #fund_name = 'Market'
    fund_name = choice(Funds)
    r = randint(1, Shares.count())
    share_name = Shares[r-1]
    r2 = randint(-15, 20)
    quantity = 100+(5*r2)
    price = round(ClosePrices[r - 1] * (1 + r2 / 100),2)
    total_order = round(price * quantity, 2)
    choices = ['Buy','Sell']
    buysell = choice(choices)
    timestamp = str(datetime.now())
    filled = 0
    Order.objects.create(order_id= order_id, fund_name=fund_name, share_name=share_name, quantity=quantity, price=price,
                         total_order=total_order, buysell=buysell, timestamp=timestamp, filled=filled)


def ShareMatch():
    for sharenum in Shares:
       match = True
       while match == True:
           #create sublists of Buy orders and Sell orders (separately) per share assuming it has not been fully filled
           BuyOrdersToBeSorted = []
           SellOrdersToBeSorted = []
           for sublist in Order.objects.filter(share_name=sharenum):
               if (sublist.buysell == 'Buy') and (sublist.quantity-sublist.filled > 0):
                   BuyOrdersToBeSorted.append(sublist)
               if (sublist.buysell == 'Sell') and (sublist.quantity-sublist.filled > 0):
                   SellOrdersToBeSorted.append(sublist)
           #sort sublist to get highest Buy order and lowest Sell order
           SortedBuyOrders = sorted(BuyOrdersToBeSorted, key=lambda x: x.price, reverse=True)
           SortedSellOrders = sorted(SellOrdersToBeSorted, key=lambda x: x.price)
           if not SortedBuyOrders or not SortedSellOrders:
               match = False
           else:
           #elif (SortedBuyOrders[0].fund_name != SortedSellOrders[0].fund_name) or (SortedBuyOrders[0].fund_name == 'Market'):
               HighestBuyOrder = SortedBuyOrders[0]
               LowestSellOrder = SortedSellOrders[0]
               #determine how many shares matched and update DealJournal accordingly
               if HighestBuyOrder.price >= LowestSellOrder.price: #and ((HighestBuyOrder[0] != LowestSellOrder[0]) or (HighestBuyOrder[0] == 'Market')): this doesn't work because it will never fund the next highest buy order or lowest sell order
                   match = True
                   MatchingShares = min(HighestBuyOrder.quantity - HighestBuyOrder.filled,LowestSellOrder.quantity - LowestSellOrder.filled)
                   HighestBuyOrder.filled = HighestBuyOrder.filled + MatchingShares
                   LowestSellOrder.filled = LowestSellOrder.filled + MatchingShares
                   #Insert amended highest buy order and lowest sell order back into Order table
                   hbo = Order.objects.get(id=HighestBuyOrder.id)
                   hbo.filled = HighestBuyOrder.filled
                   hbo.save()
                   lso = Order.objects.get(id=LowestSellOrder.id)
                   lso.filled = LowestSellOrder.filled
                   lso.save()
                   index = 0
                   #update ClosePrice
                   cp = Price.objects.get(share_name=HighestBuyOrder.share_name)
                   cp.close_price = LowestSellOrder.price
                   cp.save()
                   ClosePrices = Price.objects.values_list('close_price', flat=True)
                   for sum in range(len(ClosePrices)):
                       index += ClosePrices[sum]
                   tradeIDs = Trade.objects.values_list('trade_id', flat=True)
                   if tradeIDs:
                       trade_id = tradeIDs.last() + 1
                   else:
                       trade_id = 1
                   # create new dealjournal entry
                   Trade.objects.create(share_name=HighestBuyOrder.share_name, quantity=MatchingShares,
                                        price=LowestSellOrder.price, trade_id=trade_id,
                                        total_order=round(MatchingShares * LowestSellOrder.price, 2),
                                        buying_fund=HighestBuyOrder.fund_name,
                                        selling_fund=LowestSellOrder.fund_name, buying_orderID=HighestBuyOrder.id,
                                        selling_orderID=LowestSellOrder.id, index=index)
               else:
                   match = False
           #else:
           #    match = False

def portfolio_create(request):
    fundr = str(request.user)
    all_trades = Trade.objects.all()
    all_funds = Order.objects.values_list('fund_name', flat=True).distinct()
    portfoliodict = {}
    sharedict = {}
    for fund in all_funds:
        # if fund == fundr:
            pos = 0
            penalty = 0
            totalsharevalue = 0
            overdraft = 0
            margin = 0
            portfoliodict[fund] = {}
            sharedict[fund] = {}
            for share in Shares:
                buytrades = 0
                selltrades = 0
                buyprice = 0
                sellprice = 0
                buyquantity = 0
                sellquantity = 0
                for trade in all_trades:
                    if fund == trade.selling_fund:
                        selltrades += trade.total_order
                        if share == trade.share_name:
                            sellquantity += trade.quantity
                            sellprice += trade.total_order
                    if fund == trade.buying_fund:
                        buytrades += trade.total_order
                        if share == trade.share_name:
                            buyquantity += trade.quantity
                            buyprice += trade.total_order

                if buyquantity != 0:
                    avgbuyprice = buyprice / buyquantity
                else:
                    avgbuyprice = '-'
                if sellquantity != 0:
                    avgsellprice = sellprice / sellquantity
                else:
                    avgsellprice = '-'
                #test = sharedict[fund].value
                totalquantity = buyquantity - sellquantity
                cp = Price.objects.filter(share_name=share)[0]
                sharevalue = totalquantity * cp.close_price
                totalsharevalue += sharevalue
                if sharevalue < 0:
                    margin += abs(sharevalue)
                share_dict ={'buys': buyquantity,'sells': sellquantity, 'quantity': totalquantity, 'value': sharevalue,
                             'avgbuyprice': avgbuyprice, 'avgsellprice': avgsellprice, 'closeprice': cp.close_price}
                sharedict[fund].update({share: share_dict})
                pos += 1

            margin = margin / 2
            margininterest = margin * 0.04
            closecash = StartValue + selltrades - buytrades - margin
            if closecash < 0:
                overdraft += abs(closecash) * 0.10
            elif closecash > 10000:
                penalty += (closecash - 10000) * 0.05

            cashplusshares = closecash + totalsharevalue
            cashpercent = closecash / cashplusshares * 100
            sharepercent = totalsharevalue / cashplusshares * 100
            check = 0
            for share in Shares:
                sharedict[fund][share].update({'percent': sharedict[fund][share].get('value')/cashplusshares*100})
                if (sharedict[fund][share].get('value')/cashplusshares*100) >= diversification_threshold:
                    check += 1
            if check == Shares.count():
                divbonus = diversification_bonus
            else:
                divbonus = 0
            portfoliovalue = closecash + totalsharevalue - penalty - overdraft + divbonus - margininterest + margin
            portfoliogrowth = (portfoliovalue - StartValue) / StartValue * 100


            portfoliodict[fund].update({'portfoliovalue': portfoliovalue, 'portfoliogrowth': portfoliogrowth,
                                        'selltrades': selltrades, 'buytrades': buytrades, 'closecash': closecash,
                                        'sharevalue': totalsharevalue, 'penalty': penalty, 'cashpercent': cashpercent,
                                        'sharepercent': sharepercent, 'divbonus': divbonus, 'margin': margin,
                                        'margininterest': margininterest, 'overdraft': overdraft, 'sharedeets': sharedict[fund]})
            portfoliodict = OrderedDict(sorted(portfoliodict.items(), key=lambda x: x[1]['portfoliovalue'], reverse=True))
    return portfoliodict


def add_order(request):
    global random_market
    orderIDs = Order.objects.values_list('order_id', flat=True)
    if orderIDs:
        order_id = orderIDs.last() + 1
    else:
        order_id = 1
    fundr = str(request.user)
    user_buyorders = Order.objects.filter(fund_name=request.user, buysell='Buy')
    user_sellorders = Order.objects.filter(fund_name=request.user, buysell='Sell')
    close_prices = {}
    x = 0
    for share in Shares:
        close_prices[share] = ClosePrices[x]
        x += 1
    if not request.user.is_authenticated():
        return render(request, 'orders/login.html')
    else:
        form = OrderForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            order = form.save(commit=False)
            order.order_id = order_id
            if request.POST.get("buy"):
                order.buysell = 'Buy'
            elif request.POST.get("sell"):
                order.buysell = 'Sell'
            order.user = request.user
            order.fund_name = request.user
            order.total_order = round(order.price * order.quantity, 2)
            order.timestamp = str(datetime.now())
            order.filled = 0
            lastprice = close_prices.get(order.share_name)
            if random_market:
                if (order.price <= lastprice * 1.5) and (order.price >= lastprice * 0.5):
                    order.save()
                    Random_Ross()
                    ShareMatch()
                else:
                    messages.info(request, 'Price needs to be within 50% of last traded price')
            else:
                order.save()
                ShareMatch()

        form = OrderForm()
        context={
            'fundr': fundr,
            'form': form,
            'user_buyorders': user_buyorders,
            'user_sellorders': user_sellorders,
            'close_prices': close_prices,
            'shares': Shares,
            'portfolio_dict': portfolio_create(request),
        }
        return render(request, 'orders/order_form.html', context)

def randomize(request):
    fundr = str(request.user)
    global random_market
    if fundr == 'Market' or fundr == 'admin':
        if request.POST.get("start"):
            random_market = True
        if request.POST.get("stop"):
            random_market = False
    return render(request, 'orders/randomize.html', {'fundr': fundr})


def delete_order(request, order_id):
    fundr = str(request.user)
    order = Order.objects.get(pk=order_id)
    if order.fund_name == fundr or fundr == 'Market':
        order.delete()
    return redirect('/orders/add_order/')

def delete_trade(request, trade_id):
    fundr = str(request.user)
    if fundr == 'Market' or fundr == 'admin':
        trade = Trade.objects.get(pk=trade_id)
        trade.delete()
    return redirect('/orders/dealjournal/')


def exchange(request):
    fundr = str(request.user)
    close_prices = {}
    x = 0
    for share in Shares:
        close_prices[share] = ClosePrices[x]
        x += 1
    exchange = {}
    for sharenum in Shares:
        exchange[sharenum] = {}
        BuyOrdersToBeSorted = []
        SellOrdersToBeSorted = []
        for sublist in Order.objects.filter(share_name=sharenum):
            if (sublist.buysell == 'Buy') and (sublist.quantity - sublist.filled > 0):
                BuyOrdersToBeSorted.append(sublist)
            if (sublist.buysell == 'Sell') and (sublist.quantity - sublist.filled > 0):
                SellOrdersToBeSorted.append(sublist)
        SortedBuyOrders = sorted(BuyOrdersToBeSorted, key=lambda x: x.price, reverse=True)
        SortedSellOrders = sorted(SellOrdersToBeSorted, key=lambda x: x.price)
        try:
            b1 = SortedBuyOrders[0].price
            qb1 = SortedBuyOrders[0].quantity - SortedBuyOrders[0].filled
        except IndexError:
            b1 = '-'
            qb1 = '-'
        try:
            b2 = SortedBuyOrders[1].price
            qb2 = SortedBuyOrders[1].quantity - SortedBuyOrders[1].filled
        except IndexError:
            b2 = '-'
            qb2 = '-'
        try:
            b3 = SortedBuyOrders[2].price
            qb3 = SortedBuyOrders[2].quantity - SortedBuyOrders[2].filled
        except IndexError:
            b3 = '-'
            qb3 = '-'
        try:
            o1 = SortedSellOrders[0].price
            qo1 = SortedSellOrders[0].quantity - SortedSellOrders[0].filled
        except IndexError:
            o1 = '-'
            qo1 = '-'
        try:
            o2 = SortedSellOrders[1].price
            qo2 = SortedSellOrders[1].quantity - SortedSellOrders[1].filled
        except IndexError:
            o2 = '-'
            qo2 = '-'
        try:
            o3 = SortedSellOrders[2].price
            qo3 = SortedSellOrders[2].quantity - SortedSellOrders[2].filled
        except IndexError:
            o3 = '-'
            qo3 = '-'

        exchange[sharenum].update({'b1': b1, 'qb1': qb1, 'b2': b2, 'qb2': qb2, 'b3': b3, 'qb3': qb3,

                                   'o1': o1, 'qo1': qo1, 'o2': o2, 'qo2': qo2, 'o3': o3, 'qo3': qo3})

    queryset_index = Trade.objects.all()[5:]
    data_source_index = ModelDataSource(queryset_index, fields=['trade_id', 'index'])
    chart_index = LineChart(data_source_index, height=300, width=1000,
                              options={'title': 'Index', 'legend': {'position': 'none'}})

    queryset_shell = Trade.objects.filter(share_name='Shell')
    data_source_shell = ModelDataSource(queryset_shell, fields=['trade_id', 'price'])
    chart_shell = LineChart(data_source_shell, height=300, width=1000,
                            options={'title': 'Shell', 'legend': {'position': 'none'}})

    queryset_allianz = Trade.objects.filter(share_name='Allianz')
    data_source_allianz = ModelDataSource(queryset_allianz, fields=['trade_id', 'price'])
    chart_allianz = LineChart(data_source_allianz, height=300, width=1000,
                              options={'title': 'Allianz', 'legend': {'position': 'none'}})

    queryset_bnp = Trade.objects.filter(share_name='BNP Paribas')
    data_source_bnp = ModelDataSource(queryset_bnp, fields=['trade_id', 'price'])
    chart_bnp = LineChart(data_source_bnp, height=300, width=1000,
                              options={'title': 'BNP Paribas', 'legend': {'position': 'none'}})

    queryset_daimler = Trade.objects.filter(share_name='Daimler')
    data_source_daimler = ModelDataSource(queryset_daimler, fields=['trade_id', 'price'])
    chart_daimler = LineChart(data_source_daimler, height=300, width=1000,
                              options={'title': 'Daimler', 'legend': {'position': 'none'}})

    queryset_tesla = Trade.objects.filter(share_name='Tesla')
    data_source_tesla = ModelDataSource(queryset_tesla, fields=['trade_id', 'price'])
    chart_tesla = LineChart(data_source_tesla, height=300, width=1000,
                              options={'title': 'Tesla', 'legend': {'position': 'none'}})

    index_list = Trade.objects.values_list('index', flat=True)
    if len(index_list) >= 5 and index_list[4] !=0:
        index_growth = (index_list.last() - index_list[4]) / index_list[4] * 100
    else:
        index_growth = 0

    context = {
        'fundr': fundr,
        'portfolio_dict': portfolio_create(request),
        'shares': Shares,
        'exchange_dict': exchange,
        'chart_shell': chart_shell,
        'chart_allianz': chart_allianz,
        'chart_bnp': chart_bnp,
        'chart_daimler': chart_daimler,
        'chart_tesla': chart_tesla,
        'chart_index': chart_index,
        'close_prices': close_prices,
        'index_growth': index_growth,
    }
    return render(request, 'orders/exchange.html', context)


def Index(request):
    fundr = str(request.user)
    return render(request, 'orders/index.html', {'fundr': fundr})

def OrderBook(request):
    fundr = str(request.user)
    all_orders = Order.objects.all()

    context = {
        'all_orders': all_orders,
        'fundr': fundr,
    }
    return render(request, 'orders/orderbook.html', context)

def DealJournal(request):
    fundr = str(request.user)
    all_trades = Trade.objects.all()

    context = {
        'all_trades': all_trades,
        'fundr': fundr,
    }
    return render(request, 'orders/dealjournal.html', context)


def portfolio(request):
    fundr = str(request.user)

    context = {
        'startvalue': StartValue,
        'fundr': fundr,
        'portfolio_dict': portfolio_create(request),
    }
    return render(request, 'orders/portfolio.html', context)


def logout_user(request):
    logout(request)
    form = UserForm(request.POST or None)
    return render(request, 'orders/login.html', {"form": form})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                order = Order.objects.filter(user=request.user)
                return render(request, 'orders/index.html', {'order': order})
            else:
                return render(request, 'orders/login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'orders/login.html', {'error_message': 'Invalid login'})
    return render(request, 'orders/login.html')


def register(request):
    form = UserForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                order = Order.objects.filter(user=request.user)
                return render(request, 'orders/index.html', {'order': order})
    return render(request, 'orders/register.html', {"form": form})

def delete_all(request):
    fundr = str(request.user)
    if fundr == 'Market' or fundr == 'admin':
        Trade.objects.all().delete()
        Order.objects.all().delete()
    return render(request, 'orders/index.html')

#def job():
#    Random_Ross()
#    ShareMatch()

#def scheduler():
#    schedule.every(20).seconds.do(job)
#    while True:
#        schedule.run_pending()
#        time.sleep(1)

#scheduler()
