from chapter10.portfolio_assets import PortfolioAssets

import pandas as pd
import numpy as np
import importlib


class PortfolioSimulation:

    """
    Class that perform mean-variance, frontier analysis of a 
    Portfolio with returns of specified frequency .

    Parameters
    ----------
    portfolio_assets: Object,
                      Implementation class of PortfolioAssets
                      It can be a YahooFinancialsPortfolioAssets, 
                      MarketStackPortfolioAssets or any custom one

    portfolio_optimizer_full_class_name: String,
                                         Fully qualified class name of implmentation 
                                         of PortfolioOptimizer

    """
    _N_SIMULATION_MEAN_VAR = 2000
    _N_SIMULATION_EFFICIENT_FRONTIER = 100

    def __init__(self, portfolio_assets: PortfolioAssets,
                 portfolio_optimizer_full_class_name: str = None):

        self._portfolio_assets = portfolio_assets
        self._load_portfolio_optimizer_class(
            portfolio_optimizer_full_class_name)
        self._mean_var_dist = self._simulate_expected_return_volatility_distribution()
        self._efficient_frontier = self._compute_efficient_frontier_path()

    def _load_portfolio_optimizer_class(self, full_class_name):
        module_name, class_name = full_class_name.rsplit(".", 1)
        self._portfolio_optimizer_class = getattr(
            importlib.import_module(module_name), class_name)

    def _generate_random_asset_weight_distribution(self):
        """
         Generate a batch of random asset weight vector of size 
         (MeanVarAnalysis._N_SIMULATION_MEAN_VAR, no of assets).
         Weights of each simulation are normalized to make 
         their sum equals to 1. 
        """
        ri = np.random.randint(100, size=(PortfolioSimulation._N_SIMULATION_MEAN_VAR,
                                          len(self._portfolio_assets.ticker_symbols)))
        norm_factor = np.array(1.0 / ri.sum(axis=1))
        return (ri.T * norm_factor).T

    def _simulate_expected_return_volatility_distribution(self):
        """
        Computes expected return & volatility of the simulated 
        portfolios with a batch of randomly generated asset weights. 
        These weights may not be fully optimal. Only a portion of them
        will give minimum volatility for the portfolio.If plotted
        it takes shape of horizontaly lying solid parabola.

        Returns a dataframe of mean-var distribution having
        'Expected Return' & 'Volatility' as columns

        """

        tickers = self._portfolio_assets.ticker_symbols
        weights_batch = self._generate_random_asset_weight_distribution()
        expected_return_volatility = pd.DataFrame()

        # Generates _N_SIMULATION_MEAN_VAR number of data points
        for i_batch in range(PortfolioSimulation._N_SIMULATION_MEAN_VAR):

            # Simulated weights are assigned in the portfolio
            self._portfolio_assets.weights = weights_batch[i_batch]

            means = self._portfolio_assets.expected_return
            var = self._portfolio_assets.volatility

            expected_return_volatility = pd.concat([expected_return_volatility,
                                                    pd.DataFrame({'Expected Return': [means],
                                                                  'Volatility': [var]})],
                                                   ignore_index=True)

        return expected_return_volatility

    def _compute_efficient_frontier_path(self):
        """
        Computes efficient frontier path from the generated
        mean-var distribution. This path is within the range 
        of minimum & maximum target means of the mean-var
        distribution. If plotted, it comes along the
        boundary of solid parabola generated by 
        mean-var distribution. 

        Returns a dataframe of path having 'Expected Return'
        & 'Volatility' as columns

        """
        if self._mean_var_dist is None:
            self._mean_var_dist = self._simulate_expected_return_volatility_distribution()

        efficient_froniter = pd.DataFrame()

        # Generate a linear space of real numbers of size _N_SIMULATION_EFFICIENT_FRONTIER
        # within the range of min & max of mean-var distribution
        target_means_space = np.linspace(np.min(self._mean_var_dist['Expected Return']),
                                         np.max(
                                             self._mean_var_dist['Expected Return']),
                                         PortfolioSimulation._N_SIMULATION_EFFICIENT_FRONTIER)

        for i_batch in range(PortfolioSimulation._N_SIMULATION_EFFICIENT_FRONTIER):
            target_mean = target_means_space[i_batch]

            # Instantiate the portfolio optimizer having expected target
            # mean from the series
            portfolio_optimizer = self._portfolio_optimizer_class(
                expected_mean_return=target_mean)

            # Run the portfolio optimizer to get the optimal weights
            portfolio_optimizer.fit(self._portfolio_assets)

            optimal_var = portfolio_optimizer.optimal_variance
            if optimal_var is not None:
                efficient_froniter = pd.concat([efficient_froniter,
                                                pd.DataFrame({'Expected Return': [target_mean],
                                                              'Volatility': [optimal_var]})],
                                               ignore_index=True)

        return efficient_froniter

    @property
    def mean_variance_distribution(self):
        return self._mean_var_dist

    @property
    def efficient_frontier(self):
        return self._efficient_frontier
