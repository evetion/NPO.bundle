TITLE = 'NPO'
API_BASE_URL = 'https://start-api.npo.nl/'
EPISODE_URL = 'https://www.npo.nl/redirect/00-00-0000/'
DAY = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
MONTH = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni',
         'juli', 'augustus', 'september', 'oktober', 'november', 'december']


def Start():
    ObjectContainer.title1 = TITLE
    HTTP.CacheTime = 300
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
    HTTP.Headers['ApiKey'] = 'e45fe473feaf42ad9a215007c6aa5e7e'


# API
# Website
# https://start-api.npo.nl/page/catalogue?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/page/franchise/KN_1676727?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/page/episode/POW_03991657?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e

# Backend
# https://start-api.npo.nl/media/series/?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/media/series/AT_2046031/episodes/?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/media/series/AT_2046031/seasons/?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/media/POW_03991657?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/media/POW_03991657/stream/?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e

# payload for stream "{\"profile\":\"hls\",\"viewer\":1061049068313,\"options\":{\"startOver\":false}}"
# player token => http://ida.omroep.nl/app.php/auth

@handler('/video/npo', TITLE)
def MainMenu(**kwargs):

    oc = ObjectContainer()

    # Generic ones
    oc.add(DirectoryObject(key=Callback(Overview, title='Movies', type='broadcast'), title='Movies'))
    oc.add(DirectoryObject(key=Callback(Overview, title='Series', type='series'), title='Series'))
    oc.add(DirectoryObject(key=Callback(Overview, title='Series', type='series'), title='Series'))
    oc.add(DirectoryObject(key=Callback(OnDemand, title='Gemist'), title='Gemist'))

    oc.add(DirectoryObject(key=Callback(Series, series_id="POW_03108599"), title='HHB'))
    oc.add(DirectoryObject(key=Callback(Series, series_id="VPWON_1250334"), title='Lubach'))

    return oc

####################################################################################################


@route('/video/npo/overview')
def Overview(title, type='series', path='media/series/', filter="", order="title", reverse=True, **kwargs):

    oc = ObjectContainer(title2=title)
    url = '{}{}{}'.format(API_BASE_URL, path, filter)
    Log(url)
    json_obj = JSON.ObjectFromURL(url)

    # for programme in find_grid_all(json_obj, pages=3):
    programmes = find_grid_all2(json_obj, pages=7)
    programmes = sorted(programmes, key=lambda x: (x.get("isOnlyOnNpoPlus"), x.get(order)), reverse=reverse)

    for programme in programmes:

        # Skip stuff we don't want
        if programme.get("type") != type:
            continue

        plus = "+" if programme.get("isOnlyOnNpoPlus") else ""

        thumbs = images(programme)

        if type == "broadcast":
            try:
                oc.add(VideoClipObject(
                    url="{}{}".format(EPISODE_URL, programme['id']),
                    title=plus + " " + programme['title'],
                    summary=programme['description'],
                    duration=programme['duration'] * 1000,
                    # originally_available_at=airdate.date(),
                    thumb=Resource.ContentsOfURLWithFallback(thumbs),
                ))
            except:
                Log("Failed to parse {}".format(programme['id']))

        elif type == "series":
            oc.add(DirectoryObject(
                key=Callback(Series, series_id=programme['id']),
                title=plus + " " + programme['title'],
                summary=programme['description'],
                thumb=Resource.ContentsOfURLWithFallback(thumbs)
            ))

        else:
            Log("Unknown type {}".format(programme.get("type")))

    return oc


def find_grid_all2(obj, pages=2):
    all = obj.get("items")
    Log("Got first page")
    if "_links" in obj and "next" in obj["_links"]:
        i = 0
        while True:
            if i >= pages:
                break
            i += 1
            next = obj["_links"].get("next")
            Log("Getting next page: {}".format(next))
            if next is not None:
                obj = JSON.ObjectFromURL(next["href"])
                items = obj.get("items")
                if items is not None:
                    all.extend(items)
                else:
                    break
            else:
                break
    return all


def images(media):
    thumbs = []
    try:
        thumbs.append(media['images']['original']['formats']['original']['source'])
    except:
        pass
    return thumbs


@route('/video/npo/series/{series_id}')
def Series(series_id, **kwargs):
    url = '{}/media/series/{}/episodes'.format(API_BASE_URL, series_id)
    json_obj = JSON.ObjectFromURL(url)

    episodes = find_grid_all2(json_obj, pages=5)
    oc = ObjectContainer(title2=series_id)

    if len(episodes) > 0:
        episode = episodes[0]
        oc = ObjectContainer(title2=episode['title'])
    else:
        Log("No episodes found!")
        return ObjectContainer(title2="No episodes")

    episodes = sorted(episodes, key=lambda x: (x["seasonNumber"], x["episodeNumber"]), reverse=True)

    for episode in episodes:
        # 2019-01-20T19:25:00Z
        # airdate = Datetime.strptime(episode['broadcastDate'], '%Y-%M-%DT%XZ')
        # title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)

        thumbs = images(episode)

        plus = "+" if episode.get("isOnlyOnNpoPlus") else ""

        oc.add(VideoClipObject(
            url="{}{}".format(EPISODE_URL, episode['id']),
            title="{} S{}E{}: {}".format(plus, episode["seasonNumber"],
                                         episode["episodeNumber"], episode['episodeTitle']),
            summary=episode['descriptionLong'],
            duration=episode['duration'] * 1000,
            # originally_available_at=airdate.date(),
            thumb=Resource.ContentsOfURLWithFallback(thumbs)
        ))

    return oc


@route('/video/npo/ondemand')
def OnDemand(**kwargs):

    oc = ObjectContainer(title2='Gemist')
    delta = Datetime.Delta(days=1)
    yesterday = (Datetime.Now() - delta).date()

    for i in range(0, 10):

        date_object = Datetime.Now() - (delta * i)
        title = '%s %s %s' % (DAY[date_object.weekday()], date_object.day, MONTH[date_object.month])

        oc.add(DirectoryObject(key=Callback(Overview, title=title, order="geen",
                                            filter='?dateFrom={}'.format(date_object.date())),
                               title=title))

    return oc

####################################################################################################
