![RANKOR](https://raw.githubusercontent.com/frrmack/rankor/master/Rankor_logo_white.png)

A web app for ranking things by comparing pairs of them.

It's fun to let them fight for your love; it's also a lot more accurate, efficient, and satisfying than trying to directly make a ranked list or a tier list.


-- Irmak

## Virtual environment setup

Make a virtual environment. This source code was written using `pyenv` and `pyenv-virtualenvwrapper`. You can also use them, or use your own virtual environment tool. The python version I installed with `pyenv` and used to develop this code is `3.10.4`. Below are instructions to do it the way I did it.


Setup instructions for `pyenv` and `pyenv-virtualenvwrapper` if you don't have them are [here](https://gist.github.com/eliangcs/43a51f5c95dd9b848ddc). 


When you have them, the following installs the correct python version, creates a virtualenv (with this python version) called `rankor`, and activates it.


```
pyenv install 3.10.4
pyenv virtualenv 3.10.4 rankor
pyenv activate rankor
```

## Install rankor locally
With the virtual environment active, install rankor including all its dependencies:
`pip install -e .`


## Install mongodb and set up a database

- Install mongo unless you already have it.

If you are using OS X, use brew:

[If you don't already have command line tools, install them with `xcode-select --install`]

[If you don't already have brew, install it following [these instructions](https://brew.sh/#install)]
```
brew tap mongodb/brew
brew update
brew install mongodb-community
```

- Start the mongo server as a macOS service:
`brew services start mongodb-community`


- Verify that the server is running by doing `brew services list`. You should see the service `mongodb-community` listed as `started`. 


If you are using linux instead of OS X, use the distribution's package manager following [mongodb's installation instructions](https://www.mongodb.com/docs/manual/administration/install-on-linux/) and start the server as a daemon as detailed in that article.



## Run development server
- Start python server in project root: `python server.py`



## Run production server
- `gunicorn --bind 0.0.0.0:5000 server:app -w 4` (change `-w 4` to however many workers you want)

