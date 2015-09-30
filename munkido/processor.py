from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.conf import settings

from django.contrib.auth.models import User, Group
PROJECT_DIR = settings.PROJECT_DIR
APPNAME = settings.APPNAME

def index(request):
	handle=open(PROJECT_DIR+"/../version", 'r+')
	version=handle.read()
	return {
			'webadmin_version': version}

def resolver_context_processor(request):
    return {
        'app_name': request.resolver_match.app_name,
        'namespace': request.resolver_match.namespace,
        'url_name': request.resolver_match.url_name
    }
