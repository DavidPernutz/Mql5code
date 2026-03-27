#include <Trade/Trade.mqh>

input int MagicNumber = 1234;
input bool UseSpreadFilter = true;
input double MaxSpreadPoints = 100.0;
input int FridayNoNewTradesHour = 18;

CTrade trade;

bool IsSpreadOK()
{
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask <= 0.0 || bid <= 0.0)
      return false;

   double spreadPoints = (ask - bid) / _Point;
   return (spreadPoints <= MaxSpreadPoints);
}

int OnInit()
{
   return INIT_SUCCEEDED;
}
