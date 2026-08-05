# Testing

## Safe checks

- `python -m compileall .`
- `python -m pytest` is not recommended unless the environment does not require MT5.

## CI guidance

Use compile-only and static validation for CI to avoid MT5/broker side effects.
