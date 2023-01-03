from django.http.response import HttpResponseRedirectBase


class HttpResponseSeeOtherRedirect(HttpResponseRedirectBase):
    status_code = 303
