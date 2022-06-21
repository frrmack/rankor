# RANKOR
A web app for ranking things by comparing pairs of them.

It's fun to let them fight for your love; it's also a lot more accurate, efficient, and satisfying than trying to directly make a ranked list or a tier list.


-- Irmak

## Virtual environment setup

Make a virtual environment. This source code was written using `pyenv` and `pyenv-virtualenvwrapper`. You can also use them, or use your own virtual environment tool. The python version installed with 'pyenv' here and used to develop this code is '3.10.4'. Below are instructions to do it the way I did it.


Setup instructions for `pyenv` and `pyenv-virtualenvwrapper` if you don't have them are [here](https://gist.github.com/eliangcs/43a51f5c95dd9b848ddc). 


When you have them, the following installs the correct python version, creates a virtualenv (with this python version) called `rankor`, and activates it.


```
pyenv install 3.10.4
pyenv virtualenv 3.10.4 rankor
pyenv activate rankor
```


The packages used by this code are (as always) in `requirements.txt`. You can install all of them with `pip install -r requirements.txt`

## Run development server
- start python server in project root: `python server.py`

## Run production server
- `gunicorn --bind 0.0.0.0:5000 server:app -w 4` (change `-w 4` to however many workers you want)

