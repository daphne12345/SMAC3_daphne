#MYPYPATH=smac
MYPYOPTS=""

MYPYOPS="$MYPYOPS --ignore-missing-imports --follow-imports skip"
# We would like to have the following options set, but for now we have to use the ones above to get started
#MYPYOPTS="--ignore-missing-imports --strict"
#MYPYOPTS="$MYPYOPS --disallow-any-unimported"
#MYPYOPTS="$MYPYOPS --disallow-any-expr"
#MYPYOPTS="$MYPYOPS --disallow-any-decorated"
#MYPYOPTS="$MYPYOPS --disallow-any-explicit"
#MYPYOPTS="$MYPYOPS --disallow-any-generics"
MYPYOPTS="$MYPYOPS --disallow-untyped-defs"
mypy $MYPYOPTS --show-error-codes smac/configspace
mypy $MYPYOPTS --show-error-codes smac/epm
mypy $MYPYOPTS --show-error-codes smac/facade
mypy $MYPYOPTS --show-error-codes smac/intensification
mypy $MYPYOPTS --show-error-codes smac/optimizer
mypy $MYPYOPTS --show-error-codes smac/runhistory
mypy $MYPYOPTS --show-error-codes smac/scenario
mypy $MYPYOPTS --show-error-codes smac/stats
mypy $MYPYOPTS --show-error-codes smac/tae
mypy $MYPYOPTS --show-error-codes smac/utils