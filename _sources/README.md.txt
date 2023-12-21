# SPARTA Twitter API

![Linting Status](https://github.com/UnibwSparta/twitterapi/actions/workflows/linting.yaml/badge.svg)
![Test Status](https://github.com/UnibwSparta/twitterapi/actions/workflows/test.yaml/badge.svg)
![Build Status](https://github.com/UnibwSparta/twitterapi/actions/workflows/build.yaml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

Welcome to the official GitHub repository for the [SPARTA](https://dtecbw.de/sparta) Twitter API, a powerful Python implementation to interact with Twitter's API v2 in a robust and efficient manner.

## 🚀 Features

- Methods for gathering tweets, users and more.
- Asynchronous API calls support.
- Efficient error handling and rate limit management.
- Comprehensive documentation with usage examples.

## 📦 Installation

We recommend using [Poetry](https://python-poetry.org/docs/) for managing the project dependencies. If you don't have Poetry installed, check their [official documentation](https://python-poetry.org/docs/#installation) for guidance.

To install the SPARTA Twitter API via Poetry:

```bash
poetry add sparta-twitterapi
```

or to install it via pip:

```bash
pip3 install sparta-twitterapi
```

## 📝 Quick Start

Here's a simple example to get you started:

```python
import os
os.environ["BEARER_TOKEN"] = "XXXXXXXXXXXXXX"
from sparta.twitterapi.tweets.tweets import get_tweets_by_id

async for tweet_response in get_tweets_by_id(['1511275800758300675', '1546866845180887040']):
    print(tweet_response.tweet)
```

For in-depth methods and examples, consult our [official documentation](https://unibwsparta.github.io/twitterapi/index.html).

## 🛠 Development & Contribution
Clone the Repo:

```bash
git clone https://github.com/UnibwSparta/twitterapi.git
cd twitterapi
```

Install Dependencies:
```bash
poetry install
```

Submit Your Changes: Make your improvements and propose a Pull Request!

## 🧪 Testing
Tests are powered by pytest. Execute tests with:

```bash
poetry run pytest tests/
```

## ❓ Support & Feedback
Issues? Feedback? Use the [GitHub issue tracker](https://github.com/UnibwSparta/twitterapi/issues).

## 📜 License
MIT License. View [LICENSE](https://github.com/UnibwSparta/twitterapi/blob/main/LICENSE) for details.

## Create twitter spec
Install datamodel-code-generator
```bash
pip3 install datamodel-code-generator
```

```bash
datamodel-codegen --input openapi.json --input-file-type openapi --output model.py --output-model-type pydantic_v2.BaseModel --collapse-root-models --use-double-quotes
```

## Project SPARTA
SPARTA is an interdisciplinary research project at the UniBw M. The Chair of Political Science is responsible for managing the project. The project is funded by dtec.bw (Digitalization and Technology Research Center of the Bundeswehr). dtec.bw is funded by the European Union - NextGenerationEU.
