# Custom routing rules to override the default Werkzeug routing

# Very specificially, this defines a routing rule to raise an Exception for 
# missing trailing slashes in the uri, instead of the default Werkzeug
# behavior that Flask also repeats. 
# 
# The default Flask (and Werkzeug) behavior is that when it sees a url without 
# a trailing slash, it redirects to the same url with the trailing slash. This 
# redirect is nice for human users on a browser, but not desired in a JSON based 
# api. Because 1) Flask returns an HTML response that says 'Redirecting...', which 
# is not a response this api wants to return, and 2) This is an api for machines to 
# interact with, not human users, and therefore it would rather be strict in the 
# format of requestsit accepts (requiring the trailing slash), rather than human 
# friendly.
#
# Werkzeug does provide an interface related to this. Specifically, strict_slash 
# is a keyword argument which is by default set to True, triggering the redirect
# behavior described above. (Werkzeug catches its own RequestPath exception to
# provide this redirect.) This keyword can be set to False to avoid the redirection
# which is unwanted here. However, this results in behavior where the server accepts
# uris with trailing slash AND those without it and return the same response to 
# either of them. As described above, this is not the behavior we want in case of
# a missing trailing slash. We want to raise an exception in that case. Therefore,
# we are updating the routing rule instead.
#
# For a discussion around if this definition of the new routing rule is a valid
# solution or not, you can refer to the discussion at
# https://github.com/pallets/werkzeug/issues/1246



# Werkzeug imports: The internal error class raised when a trailing slash 
# is missing (RequestPath) and the default rule to class to update and (Rule)
from werkzeug.routing import RequestPath, Rule as WerkzeugDefaultRoutingRule


# Rankor imports: The Exception to be raised in case of a missing trailing slash
from rankor.errors import NoTrailingSlashError


# Update the default routing Rule from Werkzeug that Flask uses, to raise an
# exception in case of a missing trailing slash. 
class SlashInsistingRoutingRule(WerkzeugDefaultRoutingRule):
    def match(self, path, method=None):
        try:
            result = super(SlashInsistingRoutingRule, self).match(path, method)
        except RequestPath:
            raise NoTrailingSlashError

        return result
