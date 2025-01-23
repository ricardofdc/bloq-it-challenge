# Here you can get some useful commands to run and test this project

``` sh
# (optional) create python virtual environment
python -m venv venv

# (optional) activate python virtual environment
source path/to/venv/bin/activate

# install project dependencies
pip install -r requirements.txt

# run flash server
flask run
# or with debug mode (automatic reload after code changes)
flask run --debug

# run tests
pytest
# run tests with coverage report
pytest --cov --cov-branch
pytest --cov --cov-branch --cov-report=html:htmlcov

# (optional) deactivate python virtual environment
deactivate
```
