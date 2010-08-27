"""
:Authors:
   - James Addison

This is a reworked version of code loosely based on Bruce Kroeze's work located
here: [http://bitbucket.org/bkroeze/django-threaded-multihost/]
"""

from django.contrib.sites.models import SiteManager, Site
from django.http import HttpResponseRedirect
from django.conf import settings
from multihost import sites
import multihost

# this will intentionally raise an exception if the user does not set a default
# redirect URL.  It is required in the event a matching Site isn't found.
MULTIHOST_REDIRECT_URL = getattr(settings, 'MULTIHOST_REDIRECT_URL')

def multihost_init_func():
    """This function overrides the get_current() method of the SiteManager so that it
    can be more robust in detecting incoming Host headers and finding mtaching
    Site instances.

    As you see in the MultiHostMiddleware middleware below, developers can
    override the functionality in this function by creating their own in settings.
    """
    def site_get_current(self):
        """Overridden version of get_current, which is multihost aware."""
        return sites.by_host()

    SiteManager.get_current = site_get_current

def multihost_process_request_func(request):
    """This function sets the request object into threadlocal storage so that it
    can be accessed from within our Site.objects.get_current() override method
    (see above) as it does not have access to the request instance at all.

    Using the new get_current() functionality (from above), it then gets the
    Site matching the Host header and sets it into the request instances if 
    found. If it returned the default site (SITE_ID), then it failed to find a
    match, and we redirect to a safe location.

    As you see in the MultiHostMiddleware middleware below, developers can
    override the functionality in this function by creating their own in settings.
    """
    multihost.set_thread_variable('request', request)

    # if the site returned equates to the default SITE_ID (1, by default), then
    # redirect to a safe location.
    site = Site.objects.get_current()
    if site.id == settings.SITE_ID:
        return HttpResponseRedirect(getattr(settings, 'MULTIHOST_REDIRECT_URL', MULTIHOST_REDIRECT_URL))

    # set the site into the request for use in the project views
    request.site = site

    return None

class MultiHostMiddleware(object):
    """Middleware to detect the incoming hostname and take a specified action based
    on its value.
    """
    def __init__(self):
        # call the user-defined multihost middleware initialization function if it
        # exists in settings, otherwise use the default from above
        return getattr(settings, 'MULTIHOST_FUNC_INIT', multihost_init_func)()
        
    def process_request(self, request):
        # call the user-defined multihost middleware process_request function if it
        # exists in settings, otherwise use the default from above
        return getattr(settings, 'MULTIHOST_FUNC_PROCESSREQUEST', multihost_process_request_func)(request)