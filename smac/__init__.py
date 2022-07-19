import datetime
import os
import sys
import warnings

from smac.config import Config
from smac.facade.black_box import BlackBoxFacade
from smac.facade.hyperparameter import HyperparameterFacade
from smac.facade.multi_fidelity import MultiFidelityFacade
from smac.runhistory.runhistory import RunHistory

name = "SMAC3"
package_name = "smac"
author = (
    "\tMarius Lindauer, Katharina Eggensperger, Matthias Feurer, André Biedenkapp, "
    "Difan Deng,\n\tCarolin Benjamins, Tim Ruhkopf, René Sass and Frank Hutter"
)

author_email = "fh@cs.uni-freiburg.de"
description = "SMAC3, a Python implementation of 'Sequential Model-based Algorithm Configuration'."
url = "https://www.automl.org/"
project_urls = {
    "Documentation": "https://https://github.com/automl.github.io/SMAC3/main",
    "Source Code": "https://github.com/https://github.com/automl/smac",
}
copyright = f"""
    Copyright {datetime.date.today().strftime('%Y')}, Marius Lindauer, Katharina Eggensperger,
    Matthias Feurer, André Biedenkapp, Difan Deng, Carolin Benjamins, Tim Ruhkopf, René Sass
    and Frank Hutter
"""
version = "2.0.0"


if os.name != "posix":
    warnings.warn(
        f"Detected unsupported operating system: {sys.platform}."
        "Please be aware, that SMAC might not run on this system."
    )


__all__ = ["Config", "RunHistory", "BlackBoxFacade", "HyperparameterFacade", "MultiFidelityFacade"]
