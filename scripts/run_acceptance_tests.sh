# Perform all possible tests at user side, CI uses a bit different approach

# Migrate to `set -xe` after fix with colors, TODO!
set -e
gofra-testkit -d examples --build-only -p "*/main.gof" -e pong_game -s 
gofra-testkit -d tests -s
gofra ./examples/pong_game/main.gof -lraylib
pytest .