__author__ = 'tcatut'

from resources.lib import kodion
from resources.lib.youtube.helper import v2, v3


def _process_list(provider, context, re_match):
    provider.set_content_type(context, kodion.constants.content_type.EPISODES)

    result = []
    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_activities(channel_id='home', page_token=page_token)
    result.extend(v3.response_to_items(provider, context, json_data))

    return result

def _process_insert(provider, context, re_match):
    raise kodion.KodionException("Activities method 'insert' is not implemented yet.")

def process(method, provider, context, re_match):
    result = []

    if method == 'list':
        result.extend(_process_list(provider, context, re_match))
        pass
    elif method == 'insert':
        return _process_insert(provider, context, re_match)
    else:
        raise kodion.KodionException("Unknown activities method '%s' not found" % method)

    return result
