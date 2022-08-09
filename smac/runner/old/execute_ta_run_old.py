from typing import Dict, List, Optional, Tuple

from subprocess import PIPE, Popen

from smac.configspace import Configuration
from smac.runner import StatusType
from smac.runner.serial_runner import SerialRunner

__copyright__ = "Copyright 2022, automl.org"
__license__ = "3-clause BSD"


class ExecuteTARunOld(SerialRunner):
    """Executes a target algorithm run with a given configuration on a given instance and some
    resource limitations.

    Uses the original SMAC/PILS format (SMAC < v2.10).
    """

    def run(
        self,
        config: Configuration,
        instance: Optional[str] = None,
        algorithm_walltime_limit: Optional[float] = None,
        seed: int = 12345,
        budget: Optional[float] = 0.0,
        instance_specific: str = "0",
    ) -> Tuple[StatusType, float, float, Dict]:
        """Runs target algorithm <self.ta> with configuration <config> on instance <instance> with
        instance specifics.

        <specifics> for at most.
        <algorithm_walltime_limit> seconds and random seed <seed>.

        Parameters
        ----------
            config : Configuration
                Dictionary param -> value
            instance : string, optional
                Problem instance
            algorithm_walltime_limit : float
                Runtime algorithm_walltime_limit
            seed : int
                Random seed
            budget : float, optional
                A positive, real-valued number representing an arbitrary limit to the target algorithm.
                Handled by the target algorithm internally. Currently ignored
            instance_specific: str
                Instance specific information (e.g., domain file or solution)

        Returns
        -------
            status: enum of StatusType (int)
                {SUCCESS, TIMEOUT, CRASHED, ABORT}
            cost: float
                cost/regret/quality/runtime (float) (None, if not returned by TA)
            runtime: float
                runtime (None if not returned by TA)
            additional_info: dict
                all further additional run information
        """
        if instance is None:
            instance = "0"
        if algorithm_walltime_limit is None:
            algorithm_walltime_limit = 99999999999999.0

        stdout_, stderr_ = self._call_ta(
            config=config,
            instance=instance,
            instance_specific=instance_specific,
            algorithm_walltime_limit=algorithm_walltime_limit,
            seed=seed,
        )

        status_string = "CRASHED"
        quality = 1234567890.0
        runtime = 1234567890.0
        additional_info = {}  # type: Dict[str, str]
        for line in stdout_.split("\n"):
            if (
                line.startswith("Result of this algorithm run:")
                or line.startswith("Result for ParamILS")
                or line.startswith("Result for SMAC")
            ):
                fields = line.split(":")[1].split(",")

                # If we have more than 6 fields, we combine them all together
                if len(fields) > 5:
                    fields[5 : len(fields)] = ["".join(map(str, fields[5 : len(fields)]))]

                    # Make it prettier
                    for char in [",", ";", "'", "[", "]"]:
                        fields[5] = fields[5].replace(char, "")

                fields = list(map(lambda x: x.strip(" "), fields))
                if len(fields) == 5:
                    status_string, runtime_string, _, quality_string, _ = fields
                    additional_info = {}
                else:
                    (
                        status_string,
                        runtime_string,
                        _,
                        quality_string,
                        _,
                        additional_info_string,
                    ) = fields
                    additional_info = {"additional_info": additional_info_string}

                runtime = min(float(runtime_string), algorithm_walltime_limit)
                quality = float(quality_string)

        if "StatusType." in status_string:
            status_string = status_string.split(".")[1]

        status_string = status_string.upper()

        if status_string in ["SAT", "UNSAT", "SUCCESS"]:
            status = StatusType.SUCCESS
        elif status_string in ["TIMEOUT"]:
            status = StatusType.TIMEOUT
        elif status_string in ["CRASHED"]:
            status = StatusType.CRASHED
        elif status_string in ["ABORT"]:
            status = StatusType.ABORT
        elif status_string in ["MEMOUT"]:
            status = StatusType.MEMOUT
        else:
            self.logger.warning(
                "Could not parse output of target algorithm. Expected format: "
                '"Result of this algorithm run: <status>,<runtime>,<quality>,<seed>"; '
                "Treating as CRASHED run."
            )
            status = StatusType.CRASHED

        if status in [StatusType.CRASHED, StatusType.ABORT]:
            self.logger.warning("Target algorithm crashed. Last 5 lines of stdout and stderr")
            self.logger.warning("\n".join(stdout_.split("\n")[-5:]))
            self.logger.warning("\n".join(stderr_.split("\n")[-5:]))

        if self.run_obj == "runtime":
            cost = runtime
        else:
            cost = quality

        return status, cost, float(runtime), additional_info

    def _call_ta(
        self,
        config: Configuration,
        instance: str,
        instance_specific: str,
        algorithm_walltime_limit: float,
        seed: int,
    ) -> Tuple[str, str]:

        # TODO: maybe replace fixed instance specific and algorithm_walltime_limit_length (0) to other value
        cmd = []  # type: List[str]
        if not isinstance(self.ta, (list, tuple)):
            raise TypeError("self.ta needs to be of type list or tuple, but is %s" % type(self.ta))
        cmd.extend(self.ta)
        cmd.extend([instance, instance_specific, str(algorithm_walltime_limit), "0", str(seed)])
        for p in config:
            if not config.get(p) is None:
                cmd.extend(["-" + str(p), str(config[p])])

        self.logger.debug("Calling: %s" % (" ".join(cmd)))
        p = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout_, stderr_ = p.communicate()

        self.logger.debug("Stdout: %s" % stdout_)
        self.logger.debug("Stderr: %s" % stderr_)

        return stdout_, stderr_
