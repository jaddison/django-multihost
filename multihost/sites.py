"""Provides utilities to help multi-site aware Django projects.

:Authors:
    - James Addison

This is a reworked version of code originally produced by Bruce Kroeze.  See
below for the original copyright.
"""
"""
New BSD License
===============
Copyright (c) 2010, Bruce Kroeze http://coderseye.com

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of SolidSiteSolutions LLC, Zefamily LLC nor the names of its
      contributors may be used to endorse or promote products derived from this
      software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__docformat__="restructuredtext"

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.loading import app_cache_ready
from django.core.cache import cache
from multihost import get_current_request

def by_host(host=None, id_only=False, recursion=False):
    """Get the current site by looking at the request stored in the thread.

    Returns the best match found in the `django.contrib.sites` app.  If not
    found, then returns the default set as given in `settings.SITE_ID`

    Params:
     - `host`: optional, host to look up
     - `id_only`: if true, then do not retrieve the full site, just the id.
     - `recursion`: used to prevent an endless loop of calling this function
    """
    site = None

    # if the host value wasn't passed in, take a look inside the request for data
    if not host:
        request = get_current_request()
        if request:
            # if the request object already has the site set, just return it now
            # and skip the intensive lookup - it's unnecessary!
            if hasattr(request, 'site'):
                # if the request.site value isn't of type Site, just return it, as the
                # developer using this app is doing something funky
                if not isinstance(request.site, Site):
                    return request.site
                
                # otherwise, just return the id or site depending on what was requested
                return id_only and request.site.id or request.site
            else:
                host = request.get_host()

    if host:
        if app_cache_ready():
            key = 'SITE%s' % (host,)

            # try to get the Site out of Django's cache
            site = cache.get(key)
            if not site:
                site = lookup(site, host, recursion, id_only)
                # if we finally have the Site, save it in the cache to prevent
                # the intensive lookup again!
                if site:
                    cache.set(key, site)
        else:
            site = lookup(site, host, recursion, id_only)

        # was it an ID-only request? if so return the site ID only!
        if site and id_only:
            site = site.id

    return site

def lookup(site, host, recursion, id_only):
    try:
        site = Site.objects.get(domain=host)
    except Site.DoesNotExist:
        # if the Site couldn't be found, strip the port off if it
        # exists and try again
        if host.find(":") > -1:
            try:
                # strip the port
                tmp = host.split(":")[0]
                site = Site.objects.get(domain=tmp)
            except Site.DoesNotExist:
                pass

    # if the Site still hasn't been found, add or remove the 'www.'
    # from the host and try with that.
    if not recursion and not site and getattr(settings, 'MULTIHOST_AUTO_WWW', True):
        if host.startswith('www.'):
            site = by_host(host=host[4:], id_only=id_only, recursion=True)
        else:
            site = by_host(host = 'www.%s' % host, id_only=id_only, recursion=True)
    return site
