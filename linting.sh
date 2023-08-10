#!/bin/bash -xe
# Run Linters and Fix
check=0

while getopts hc opt; do
    case "$opt" in
        h)
            echo "Usage: $0 [-h] [-c]"
            exit 0
            ;;
        c)
            check=1
            ;;
    esac
done
shift $((OPTIND-1))

if [ $check -ne 1 ]; then
poetry run isort src/
poetry run isort tests/
poetry run python3 -m black src/
poetry run python3 -m black tests/
poetry run docformatter --in-place src/
poetry run docformatter --in-place tests/
fi

poetry run python3 -m flake8 src/
poetry run python3 -m flake8 tests/
poetry run mypy -p sparta.twitterapi
poetry run mypy tests/
poetry run isort --diff -c src/
poetry run isort --diff -c tests/
poetry run python3 -m black --check src/
poetry run python3 -m black --check tests/