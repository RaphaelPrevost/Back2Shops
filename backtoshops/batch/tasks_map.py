from batch.tasks.stats import CalcSalesSim
from batch.tasks.stats import StatsBoughtHistory
from batch.tasks.stats import StatsIncomes
from batch.tasks.stats import StatsOrders
from batch.tasks.stats import StatsVisitors
from batch.tasks.stats import StatsVisitorsOnline


map = {
    'stats': [CalcSalesSim,
              StatsBoughtHistory,
              StatsIncomes,
              StatsOrders,
              StatsVisitors,
              StatsVisitorsOnline]
}