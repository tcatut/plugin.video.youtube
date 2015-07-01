__author__ = 'bromix'

from resources.lib.youtube.helper import yt_context_menu
from resources.lib import kodion
from resources.lib.kodion import items
from . import utils


def _process_list_response(provider, context, json_data):
    video_id_dict = {}
    channel_id_dict = {}
    playlist_id_dict = {}
    playlist_item_id_dict = {}
    subscription_id_dict = {}

    result = []

    yt_items = json_data.get('items', [])
    if len(yt_items) == 0:
        context.log_warning('List of search result is empty')
        return result

    for yt_item in yt_items:
        yt_kind = yt_item.get('kind', '')
        if yt_kind == u'youtube#video':
            video_id = yt_item['id']
            snippet = yt_item['snippet']
            title = snippet['title']
            image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
            video_item = items.VideoItem(title,
                                         context.create_uri(['play'], {'video_id': video_id}),
                                         image=image)
            video_item.set_fanart(provider.get_fanart(context))
            result.append(video_item)
            video_id_dict[video_id] = video_item
            pass
        elif yt_kind == u'youtube#channel':
            channel_id = yt_item['id']
            snippet = yt_item['snippet']
            title = snippet['title']
            image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')

            channel_item = items.DirectoryItem(title,
                                               context.create_uri(['channel', channel_id]),
                                               image=image)
            channel_item.set_fanart(provider.get_fanart(context))

            # if logged in => provide subscribing to the channel
            if provider.is_logged_in():
                context_menu = []
                yt_context_menu.append_subscribe_to_channel(context_menu, provider, context, channel_id)
                channel_item.set_context_menu(context_menu)
                pass
            result.append(channel_item)
            channel_id_dict[channel_id] = channel_item
            pass
        elif yt_kind == u'youtube#guideCategory':
            guide_id = yt_item['id']
            snippet = yt_item['snippet']
            title = snippet['title']

            guide_item = items.DirectoryItem(title,
                                             context.create_uri(['special', 'browse_channels'], {'guide_id': guide_id}))
            guide_item.set_fanart(provider.get_fanart(context))
            result.append(guide_item)
            pass
        elif yt_kind == u'youtube#subscription':
            snippet = yt_item['snippet']
            image = snippet.get('thumbnails', {}).get('high', {}).get('url', '')
            channel_id = snippet['resourceId']['channelId']
            channel_item = items.DirectoryItem(snippet['title'],
                                                context.create_uri(['channel', channel_id]),
                                                image=image)
            channel_item.set_fanart(provider.get_fanart(context))

            # map channel id with subscription id - we need it for the unsubscription
            subscription_id_dict[channel_id] = yt_item['id']

            result.append(channel_item)
            channel_id_dict[channel_id] = channel_item
            pass
        elif yt_kind == u'youtube#playlist':
            playlist_id = yt_item['id']
            snippet = yt_item['snippet']
            title = snippet['title']
            image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')

            channel_id = snippet['channelId']

            # if the path directs to a playlist of our own, we correct the channel id to 'mine'
            if context.get_path() == '/channel/mine/playlists/':
                channel_id = 'mine'
                pass
            playlist_item = items.DirectoryItem(title,
                                                context.create_uri(['channel', channel_id, 'playlist', playlist_id]),
                                                image=image)
            playlist_item.set_fanart(provider.get_fanart(context))
            result.append(playlist_item)
            playlist_id_dict[playlist_id] = playlist_item
            pass
        elif yt_kind == u'youtube#playlistItem':
            snippet = yt_item['snippet']
            video_id = snippet['resourceId']['videoId']

            # store the id of the playlistItem - for deleting this item we need this item
            playlist_item_id_dict[video_id] = yt_item['id']

            title = snippet['title']
            image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
            video_item = items.VideoItem(title,
                                         context.create_uri(['play'], {'video_id': video_id}),
                                         image=image)
            video_item.set_fanart(provider.get_fanart(context))
            result.append(video_item)
            video_id_dict[video_id] = video_item
            pass
        elif yt_kind == 'youtube#searchResult':
            yt_kind = yt_item.get('id', {}).get('kind', '')

            # video
            if yt_kind == 'youtube#video':
                video_id = yt_item['id']['videoId']
                snippet = yt_item['snippet']
                title = snippet['title']
                image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                video_item = items.VideoItem(title,
                                             context.create_uri(['play'], {'video_id': video_id}),
                                             image=image)
                video_item.set_fanart(provider.get_fanart(context))
                result.append(video_item)
                video_id_dict[video_id] = video_item
                pass
            # playlist
            elif yt_kind == 'youtube#playlist':
                playlist_id = yt_item['id']['playlistId']
                snippet = yt_item['snippet']
                title = snippet['title']
                image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')

                channel_id = snippet['channelId']
                # if the path directs to a playlist of our own, we correct the channel id to 'mine'
                if context.get_path() == '/channel/mine/playlists/':
                    channel_id = 'mine'
                    pass
                channel_name = snippet.get('channelTitle', '')
                playlist_item = items.DirectoryItem(title,
                                                    context.create_uri(
                                                        ['channel', channel_id, 'playlist', playlist_id]),
                                                    image=image)
                playlist_item.set_fanart(provider.get_fanart(context))
                result.append(playlist_item)
                playlist_id_dict[playlist_id] = playlist_item
                pass
            elif yt_kind == 'youtube#channel':
                channel_id = yt_item['id']['channelId']
                snippet = yt_item['snippet']
                title = snippet['title']
                image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')

                channel_item = items.DirectoryItem(title,
                                                   context.create_uri(['channel', channel_id]),
                                                   image=image)
                channel_item.set_fanart(provider.get_fanart(context))
                result.append(channel_item)
                channel_id_dict[channel_id] = channel_item
                pass
            else:
                raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
            pass
        # Activity response with home=true is how to get "Recommended" items.
        # Need to ignore anything that's not a video response.
        # Need to ignore duplicate videos.
        elif yt_kind == 'youtube#activity':
            snippet = yt_item['snippet']
            type = snippet['type']
            if type == 'bulletin':
                yt_item = yt_item['contentDetails']['bulletin']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#channel':
                    pass
                elif yt_kind == 'youtube#playlist':
                    pass
                elif yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'channelItem':
                pass
            elif type == 'comment':
                yt_item = yt_item['contentDetails']['comment']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#channel':
                    pass
                elif yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'favorite':
                yt_item = yt_item['contentDetails']['favorite']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'like':
                yt_item = yt_item['contentDetails']['like']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'playlistItem':
                yt_item = yt_item['contentDetails']['playlistItem']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'recommendation':
                yt_item = yt_item['contentDetails']['recommendation']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'social':
                yt_item = yt_item['contentDetails']['social']['resourceId']
                yt_kind = yt_item['kind']
                if yt_kind == 'youtube#channel':
                    pass
                elif yt_kind == 'youtube#playlist':
                    pass
                elif yt_kind == 'youtube#video':
                    video_id = yt_item['videoId']
                    title = snippet['title']
                    image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                    video_item = items.VideoItem(title,
                                                 context.create_uri(['play'], {'video_id': video_id}),
                                                 image=image)
                    video_item.set_fanart(provider.get_fanart(context))
                    # Need to make sure this isn't a duplicate.
                    if video_id not in video_id_dict.keys():
                        result.append(video_item)
                        video_id_dict[video_id] = video_item
                else:
                    raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
                pass
            elif type == 'subscription':
                pass
            elif type == 'upload':
                video_id = yt_item['contentDetails']['upload']['videoId']
                title = snippet['title']
                image = snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                video_item = items.VideoItem(title,
                                             context.create_uri(['play'], {'video_id': video_id}),
                                             image=image)
                video_item.set_fanart(provider.get_fanart(context))
                # Need to make sure this isn't a duplicate.
                if video_id not in video_id_dict.keys():
                    result.append(video_item)
                    video_id_dict[video_id] = video_item
                pass
            else:
                raise kodion.KodionException("Unknown activity '%s'" % type)
            pass
        else:
            raise kodion.KodionException("Unknown kind '%s'" % yt_kind)
        pass

    # this will also update the channel_id_dict with the correct channel id for each video.
    channel_items_dict = {}
    utils.update_video_infos(provider, context, video_id_dict, playlist_item_id_dict, channel_items_dict)
    utils.update_playlist_infos(provider, context, playlist_id_dict, channel_items_dict)
    utils.update_channel_infos(provider, context, channel_id_dict, subscription_id_dict, channel_items_dict)
    utils.update_fanarts(provider, context, channel_items_dict)
    return result


def response_to_items(provider, context, json_data, sort=None, reverse_sort=False, process_next_page=True):
    result = []
    # This could be an error response; such as Invalid Credentials.
    if not handle_error(provider, context, json_data):
        return result

    kind = json_data.get('kind', '')
    if kind == u'youtube#searchListResponse' or kind == u'youtube#playlistItemListResponse' or \
                    kind == u'youtube#playlistListResponse' or kind == u'youtube#subscriptionListResponse' or \
                    kind == u'youtube#guideCategoryListResponse' or kind == u'youtube#channelListResponse' or \
                    kind == u'youtube#videoListResponse' or kind == u'youtube#activityListResponse':
        result.extend(_process_list_response(provider, context, json_data))
        pass
    else:
        raise kodion.KodionException("Unknown kind '%s'" % kind)

    if sort is not None:
        result = sorted(result, key=sort, reverse=reverse_sort)
        pass

    # next page
    yt_next_page_token = json_data.get('nextPageToken', '')
    if process_next_page and yt_next_page_token:
        new_params = {}
        new_params.update(context.get_params())
        new_params['page_token'] = yt_next_page_token

        new_context = context.clone(new_params=new_params)

        current_page = int(new_context.get_param('page', 1))
        next_page_item = items.NextPageItem(new_context, current_page, fanart=provider.get_fanart(new_context))
        result.append(next_page_item)
        pass

    return result


def handle_error(provider, context, json_data):
    if json_data and 'error' in json_data:
        message = json_data['error'].get('message', '')
        if message:
            context.get_ui().show_notification(message)
            pass
        return False

    return True