from __future__ import annotations

from typing import Any, Callable, Iterator

from ConfigSpace import Configuration
from smac.constants import MAXINT
from smac.intensification.abstract_intensifier import AbstractIntensifier
from smac.runhistory import TrialInfo, TrialValue, TrialInfoIntent, RunHistory
from smac.scenario import Scenario
from smac.utils.logging import get_logger

__copyright__ = "Copyright 2022, automl.org"
__license__ = "3-clause BSD"

logger = get_logger(__name__)


class SimpleIntensifier(AbstractIntensifier):
    """Performs the traditional Bayesian Optimization loop, without instance/seed intensification.

    Parameters
    ----------
    stats: smac.stats.stats.Stats
        stats object
    rng : np.random.RandomState
    instances : List[str]
        list of all instance ids
    instance_specifics : Mapping[str, str]
        mapping from instance name to instance specific string
    algorithm_walltime_limit : Optional[int]
        algorithm_walltime_limit of TA runs
    deterministic : bool
        whether the TA is deterministic or not
    """

    def __init__(
        self,
        scenario: Scenario,
        seed: int | None = None,
    ) -> None:

        super().__init__(
            scenario=scenario,
            min_challenger=1,
            seed=seed,
        )

        # We want to control the number of runs that are sent to
        # the workers. At any time, we want to make sure that if there
        # are just W workers, there should be at max W active runs
        # Below variable tracks active runs not processed
        self._run_tracker: dict[tuple[Configuration, str | None, int | None, float | None], bool] = {}

    @property
    def uses_seeds(self) -> bool:
        return True

    @property
    def uses_budgets(self) -> bool:
        return False

    @property
    def uses_instances(self) -> bool:
        return self._instances is not None

    def get_meta(self) -> dict[str, Any]:
        """Returns the meta data of the created object."""
        return {
            "name": self.__class__.__name__,
        }

    def process_results(
        self,
        trial_info: TrialInfo,
        trial_value: TrialValue,
        incumbent: Configuration | None,
        runhistory: RunHistory,
        time_bound: float,
        log_trajectory: bool = True,
    ) -> tuple[Configuration, float]:
        """The intensifier stage will be updated based on the results/status of a configuration
        execution. Also, a incumbent will be determined.

        Parameters
        ----------
        trial_info : RunInfo
            A RunInfo containing the configuration that was evaluated
        incumbent : Optional[Configuration]
            Best configuration seen so far
        runhistory : RunHistory
            stores all runs we ran so far
            if False, an evaluated configuration will not be generated again
        time_bound : float
            time in [sec] available to perform intensify
        result: RunValue
            Contain the result (status and other methadata) of exercising
            a challenger/incumbent.
        log_trajectory: bool
            Whether to log changes of incumbents in trajectory

        Returns
        -------
        incumbent: Configuration()
            current (maybe new) incumbent configuration
        inc_perf: float
            empirical performance of incumbent configuration
        """
        # Mark the fact that we processed this configuration
        self._run_tracker[(trial_info.config, trial_info.instance, trial_info.seed, trial_info.budget)] = True

        # If The incumbent is None we use the challenger
        if not incumbent:
            logger.info("First run, no incumbent provided; challenger is assumed to be the incumbent")
            incumbent = trial_info.config

        self._num_trials += 1

        incumbent = self._compare_configs(
            challenger=trial_info.config,
            incumbent=incumbent,
            runhistory=runhistory,
            log_trajectory=log_trajectory,
        )
        # get incumbent cost
        inc_perf = runhistory.get_cost(incumbent)

        return incumbent, inc_perf

    def get_next_run(
        self,
        challengers: list[Configuration] | None,
        incumbent: Configuration,
        get_next_configurations: Callable[[], Iterator[Configuration]] | None,
        runhistory: RunHistory,
        repeat_configs: bool = True,
        n_workers: int = 1,
    ) -> tuple[TrialInfoIntent, TrialInfo]:
        """Selects which challenger to be used. As in a traditional BO loop, we sample from the EPM,
        which is the next configuration based on the acquisition function. The input data is read
        from the runhistory.

        Parameters
        ----------
        challengers : List[Configuration]
            promising configurations
        incumbent: Configuration
            incumbent configuration
        chooser : smac.optimizer.epm_configuration_chooser.EPMChooser
            optimizer that generates next configurations to use for racing
        runhistory : smac.runhistory.runhistory.RunHistory
            stores all runs we ran so far
        repeat_configs : bool
            if False, an evaluated configuration will not be generated again
        n_workers: int
            the maximum number of workers available
            at a given time.

        Returns
        -------
        intent: RunInfoIntent
               Indicator of how to consume the RunInfo object
        trial_info: RunInfo
            An object that encapsulates the minimum information to
            evaluate a configuration
        """

        # We always sample from the configs provided or the EPM
        challenger = self._next_challenger(
            challengers=challengers,
            get_next_configurations=get_next_configurations,
            runhistory=runhistory,
            repeat_configs=repeat_configs,
        )

        # Run tracker is a dictionary whose values indicate if a run has been
        # processed. If a value in this dict is false, it means that a worker
        # should still be processing this configuration.
        total_active_runs = len([v for v in self._run_tracker.values() if not v])
        if total_active_runs >= n_workers:
            # We only submit jobs if there is an idle worker
            return TrialInfoIntent.WAIT, TrialInfo(
                config=None,
                instance=None,
                seed=None,
                budget=None,
            )

        trial_info = TrialInfo(
            config=challenger,
            instance=None if self._instances is None else self._instances[-1],
            seed=0 if self._deterministic else int(self._rng.randint(low=0, high=MAXINT, size=1)[0]),
            budget=None,
        )

        self._run_tracker[(trial_info.config, trial_info.instance, trial_info.seed, trial_info.budget)] = False
        return TrialInfoIntent.RUN, trial_info
