#include <Trade/Trade.mqh>

CTrade trade;

int OnInit()
{
   double fm = AccountInfoDouble(ACCOUNT_FREEMARGIN);
   return INIT_SUCCEEDED;
}

void OnTick()
{
   trade.Buy(0.10, "US100", 0.0, 0.0, 0.0, "test");
   trade.PositionModify(123, 0.0, 0.0);
}
