from jsonrpcserver import method, InvalidParams
from .models import Transfer,Error
from excel.models import Cards
import logging
from django.views.decorators.csrf import csrf_exempt
from jsonrpcserver import dispatch
import json
from django.http import JsonResponse
from .rpc_methods import *


logger = logging.getLogger("__name__")
@csrf_exempt
def rpc_handler(request):
    if request.method != 'POST':
        logger.warning('ONLY POST is allowed!')
        return JsonResponse({'error':'ERROR'},status=200)
    try:
        response = dispatch(request.body.decode())
        return JsonResponse(json.loads(response),safe=False)
    except Exception as e:
        logger.error('Returning error:',e)
        
