# Perform baseline testcases (testkit) with optimizer passes at aggressive setting

# Migrate to `set -xe` after fix with colors, TODO!
set -e
gofra-testkit -d examples --build-only -p "*/main.gof" -e pong_game -s --aggressive-optimizations
gofra-testkit -d tests -s --aggressive-optimizations
gofra ./examples/pong_game/main.gof -lraylib -O1