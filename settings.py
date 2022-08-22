"""
SETTINGS FOR A SPECIFIC INSTANCE OF THE RANKOR API
"""

# Import dotenv and read environmental variables in a file called .env into the
# os.environ dict in case you need to read a setting from the environment (to
# keep it untracked by the repository)
import os
import dotenv
dotenv.load_dotenv()



# Database connection
MONGO_DATABASE_URI = 'mongodb://localhost:27017/rankor'
# This is the uri to connect to the mongodb database that powers the api server.
# If the database is not protected through authentication and if you don't mind
# this uri to be pushed to an online repository where the entire world can see
# it (such as a local project where you have a local mongo database not even
# open to the Internet---something like 'mongodb://localhost:27017/rankor'), you
# can just directly put the uri here. If however, you are using a cluster uri
# that shouldn't be committed to a repository (most cases), you can use dotenv,
# a python package that helps you read environmental variables. Put your uri,
# which may look something like
# "mongodb+srv://USERNAME:PASSW0RD@cluster0-abcde.azure.mongodb.net/rankor", for
# example, into a separate file in the project root directory and call this file
# .env. For example, the contents of your .env file may be a single line that
# look like this (no spaces either side of the "=", this is shell syntax):
# MONGO_URI="mongodb+srv://USERNAME:PASSW0RD@cluster0-abcde.azure.mongodb.net/rankor"
# Do not commit this .env file to the repo (the .gitignore that comes with
# rankor already knows not to track it). This setting file already uses the
# dotenv package to read the .env file. All you have to do now is to set this
# setting to: MONGO_DATABASE_URI = os.environ["MONGO_URI"]



# Response pagination
NUMBER_ITEMS_IN_EACH_PAGE = {
    "thing":        20,
    "ranked_list":  3,
    "ranked_thing": 10,
    "fight":        20
}
SORT_ITEMS_BY_FIELD = {
    "thing":        ("name", "ascending"),
    "ranked_list":  ("time_created", "descending"),
    "ranked_thing": ("rank", "ascending"),            # change not recommended
    "fight":        ("time_fought", "descending")     # change not recommended
} 
# These settings are pretty straightforward. The endpoints that respond with
# lists (which may get long) paginate those lists, and deliver them in chunks.
# These settings determine a) how many of each should be put in a single page,
# and b) which field to sort them by before dividing them into pages.



# TrueSkill mu and sigma initialization values for Things that did not fight
# yet. These define the prior, and they will also roughly determine what the
# score ranges will be.
DEFAULT_INITIAL_SCORE_MU_VALUE = 50
DEFAULT_INITIAL_SCORE_SIGMA_VALUE = 15
# These are the mean and standard deviation of the Gaussian prior for 
# the TrueSkill strength/score estimation.
# You can think of the 99% possible score range for a new Thing to be
# MU  +- 3 SIGMA
# For example, if mu is 2.5 and sigma is 0.84, we are thinking that our
# prior, our initial Gaussian estimate for the 'underlying true score' of
# a Thing will be quite likely somewhere between 0 and 5, a lot more likely
# to be around the center of that range than near 0 or 5. As we gather 
# information about this Thing with more and more fights, its mu will get 
# closer to the 'underlying true score' as its sigma gets smaller and smaller.
# It may end up outside that initial prior range, too, actually, if it keeps
# losing (or winning) all its fights, but this general way of thinking around 
# mu and sigma should give you a general idea of the score ranges you are playing in.
# The larger you choose sigma to be relative to mu, the less initial information
# you are using in the prior (wider range, flatter shape closer to uniform distribution)
# The flatter and wider you make this prior, though (large sigmas compared to mu), the
# more fights you will need before your posteriors get narrow enough to trust.
# Basically, the less confidence you show in the beginning (initialization), the 
# more information you'll need to gather to gain enough confidence. Another way of
# thinking about this is: At the end, for a confident ranking, you want the sigmas
# to be low. If you start with very high sigmas, it will take longer to get the
# the desired low sigmas (narrow posteriors). If you start with very low sigmas
# on the other hand, it's like starting with already strong ideas about all Thing's
# levels, and it will be hard to differentiate them. 
# Depending on how many Things you are ranking and how many fights you can afford
# to complete will lead to different values to be more suitable, but really, don't
# worry about this too much, the prior's impact on your ranking will be negligible 
# as long as you have a good amount of fights and the posterior is determined by
# the data. To give you a very rough idea, by the time you have about ten fights 
# per Thing in your RankedList, these initial values likely won't matter as much
# (depending on the circumstances), and even at smaller numbers of fights, you 
# don't need to worry about these in a lot of cases. The best way to make sure
# is to run a few experiments with different initial values but the same fight
# results to see if the resulting scores are converging or not.


# Setting to let RankedList edit endpoint accept fights and thing_scores
# fields
ALLOW_MANUAL_EDITING_OF_RANKEDLIST_FIGHTS_OR_SCORES = False
# RankedList edits/updates are limited to their basic data only by default.
# This means that you can only change their name using the edit endpoint.
# Fights can be saved to or deleted from RankedLists via other endpoints,
# and this is normally the only way to influence the fights list and the
# thing_scores list in a RankedList. If you set the setting above to True, 
# the RankedList edit endpoint will allow you to directly update all fields
# of the RankedList model, which include these lists.
# Doing this is NOT recommended, as it's not a good way of handling the 
# data, it's prone to introducing slient errors that will come back to 
# bite you later, and it's easy to mess up unless you know exactly what
# you're doing.