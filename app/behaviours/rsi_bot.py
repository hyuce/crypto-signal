
import structlog
import ccxt

class RSIBot():
    def __init__(self, behaviour_config, exchange_interface, strategy_analyzer, notifier, db_handler):
        self.logger = structlog.get_logger()
        self.behaviour_config = behaviour_config
        self.exchange_interface = exchange_interface
        self.strategy_analyzer = strategy_analyzer
        self.notifier = notifier
        self.db_handler = db_handler

    def run(self, market_pairs, update_interval):
        if market_pairs:
            market_data = self.exchange_interface.get_symbol_markets(market_pairs)
        else:
            market_data = self.exchange_interface.get_exchange_markets()

        rsi_data = {}
        for exchange in market_data:
            rsi_data[exchange] = {}
            for market_pair in market_data[exchange]:
                try:
                  rsi_data[exchange][market_pair] = self.strategy_analyzer.analyze_rsi(
                      market_data[exchange][market_pair]['symbol'],
                      exchange,
                      self.behaviour_config['trade_parameters']['buy']['rsi_threshold'],
                      self.behaviour_config['trade_parameters']['sell']['rsi_threshold'])
                except ccxt.NetworkError:
                  self.logger.warn("Read timeout getting data for %s on %s skipping", market_pair, exchange)
                  continue

        current_holdings = self.get_holdings()
        for exchange in rsi_data:
            for market_pair in rsi_data[exchange]:
                if rsi_data[exchange][market_pair]['is_overbought']:
                    if not market_pair in current_holdings[exchange]:
                        self.buy(market_pair, exchange)
                elif rsi_data[exchange][market_pair]['is_oversold']:
                    if market_pair in current_holdings[exchange]:
                        self.sell(market_pair, exchange)

    def buy(self, market_pair, exchange):
        return

    def sell(self, market_pair, exchange):
        return

    def get_holdings(self):
        transactions = self.db_handler.get_transactions({'is_open': True})
        holdings = {}
        for row in transactions:
            if not row.exchange in holdings:
                holdings[row.exchange] = []
            market_pair = row.base_symbol + '/' + row.quote_symbol
            holdings[row.exchange].append(market_pair)
        return holdings
