TITLE = 'NPO'
API_BASE_URL = 'https://start-api.npo.nl/'
EPISODE_URL = 'https://www.npo.nl/redirect/00-00-0000/%s'
DAY = ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag']
MONTH = ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni',
         'juli', 'augustus', 'september', 'oktober', 'november', 'december']

####################################################################################################

def Start():

    ObjectContainer.title1 = TITLE
    HTTP.CacheTime = 300
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
    HTTP.Headers['ApiKey'] = 'e45fe473feaf42ad9a215007c6aa5e7e'

####################################################################################################

# API
# Website
# https://start-api.npo.nl/page/catalogue?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/page/franchise/KN_1676727?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/page/episode/POW_03991657?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e

# Backend
# https://start-api.npo.nl/media/series/AT_2046031/seasons/?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/media/POW_03991657?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e
# https://start-api.npo.nl/media/POW_03991657/stream/?ApiKey=e45fe473feaf42ad9a215007c6aa5e7e

# payload for stream "{\"profile\":\"hls\",\"viewer\":1061049068313,\"options\":{\"startOver\":false}}"
# player token => http://ida.omroep.nl/app.php/auth

@handler('/video/npo', TITLE)
def MainMenu(**kwargs):

    oc = ObjectContainer()

#	oc.add(DirectoryObject(key=Callback(Overview, title='Kijktips', path='tips.json'), title='Kijktips'))
    # oc.add(DirectoryObject(key=Callback(Overview, title='Populair', path='episodes/popular.json'), title='Populair'))
    oc.add(DirectoryObject(key=Callback(Series, series_id="POW_03108599"), title='HHB'))
    oc.add(DirectoryObject(key=Callback(OnDemand), title='Gemist'))
    oc.add(DirectoryObject(key=Callback(AZ), title='Programma\'s A-Z'))

    return oc

####################################################################################################


@route('/video/npo/overview')
def Overview(title, path, **kwargs):

    oc = ObjectContainer(title2=title)
    json_obj = JSON.ObjectFromURL('%s/%s' % (API_BASE_URL, path))

    # for programme in find_grid_all(json_obj, pages=3):
    programmes = find_grid_all(json_obj, pages=7)
    programmes = sorted(programmes, key=lambda x: x.get("broadcastDate", 0), reverse=True)

    for programme in programmes:

        thumbs = []
        try:
            thumbs.append(programme['images']['original']['formats']['original']['source'])
        except:
            pass

        if programme.get("isMovie"):

            try:
                oc.add(VideoClipObject(
                    url=EPISODE_URL % (programme['id']),
                    title=programme['title'],
                    summary=programme['description'],
                    duration=programme['duration'] * 1000,
                    # originally_available_at=airdate.date(),
                    thumb=Resource.ContentsOfURLWithFallback(thumbs),
                ))
            except:
                pass

        else:
            oc.add(DirectoryObject(
                key=Callback(Series, series_id=programme['id']),
                title=programme['title'],
                summary=programme['description'],
                thumb=Resource.ContentsOfURLWithFallback(thumbs)
            ))

    return oc

####################################################################################################


# @route('/video/npo/episode/{episode_id}')
# def Episode(episode_id, **kwargs):
#
#     video = JSON.ObjectFromURL('%s/page/episode/%s' % (API_BASE_URL, episode_id))
#
#     oc = ObjectContainer(title2=video['series']['name'])
#
#     airdate = Datetime.FromTimestamp(video['broadcasted_at'])
#     title = video['name'] if video['name'] else video['series']['name']
#     title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)
#
#     thumbs = []
#     if video['image']:
#         thumbs.append(video['image'])
#     if 'stills' in video and video['stills']:
#         thumbs.append(video['stills'][0]['url'])
#     if video['series']['image']:
#         thumbs.append(video['series']['image'])
#
#     oc.add(VideoClipObject(
#         url=EPISODE_URL % (video['mid']),
#         title=title,
#         summary=video['description'],
#         duration=video['duration'] * 1000,
#         originally_available_at=airdate.date(),
#         thumb=Resource.ContentsOfURLWithFallback(thumbs)
#     ))
#
#     oc.add(DirectoryObject(
#         key=Callback(Series, series_id=video['series']['id']),
#         title='Alle afleveringen'
#     ))
#
#     return oc

####################################################################################################

def find_grid_all(obj, pages=2):
    all = find_grid(obj)
    Log("Got first page")
    for component in obj["components"]:
        if component.get("type") == "grid":
            data = component.get("data")
            if "_links" in data and "next" in data["_links"]:
                i = 0
                while True:
                    if i >= pages: break
                    i += 1
                    next = data["_links"].get("next")
                    Log("Getting next page: {}".format(next))
                    if next is not None:
                        data = JSON.ObjectFromURL(next["href"])
                        items = data.get("items")
                        if items is not None:
                            all.extend(items)
                        else:
                            break
                    else:
                        break
    return all


def find_grid(obj):
    for component in obj["components"]:
        if component.get("type") == "grid":
            data = component.get("data")
            items = data.get("items")
            return items


def find_grid_all2(obj, pages=2):
    all = obj.get("items")
    Log("Got first page")
    if "_links" in obj and "next" in obj["_links"]:
        i = 0
        while True:
            if i >= pages: break
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


@route('/video/npo/series/{series_id}')
def Series(series_id, **kwargs):

    # url = '%s/page/franchise/%s' % (API_BASE_URL, series_id)
    url = '%s/media/series/%s/episodes' % (API_BASE_URL, series_id)
    json_obj = JSON.ObjectFromURL(url)
    # print(json_obj)
    episodes = find_grid_all2(json_obj, pages=5)
    # Log(episodes)

    if len(episodes) > 0:
        oc = ObjectContainer(title2=episodes[0]['title'])
    else:
        return ObjectContainer(title2="No episodes")

    episodes = sorted(episodes, key=lambda x: x["broadcastDate"], reverse=True)

    for video in episodes:

        # 2019-01-20T19:25:00Z
        # airdate = Datetime.strptime(video['broadcastDate'], '%Y-%M-%DT%XZ')
        title = video['episodeTitle']
        # title = '%s (%s %s %s)' % (title, airdate.day, MONTH[airdate.month], airdate.year)

        thumbs = []
        try:
            thumbs.append(programme['images']['original']['formats']['original']['source'])
        except:
            pass

        # if video['image']:
        #     thumbs.append(video['image'])
        # if 'stills' in video and video['stills']:
        #     thumbs.append(video['stills'][0]['url'])
        # if json_obj['image']:
        #     thumbs.append(json_obj['image'])
        try:
            oc.add(VideoClipObject(
                url=EPISODE_URL % (video['id']),
                title=title,
                summary=video['description'],
                duration=video['duration'] * 1000,
                # originally_available_at=airdate.date(),
                thumb=Resource.ContentsOfURLWithFallback(thumbs)
            ))
        except:
            Log("{} crashed".format(video['id']))

    return oc

####################################################################################################


@route('/video/npo/ondemand')
def OnDemand(**kwargs):

    oc = ObjectContainer(title2='Gemist')
    delta = Datetime.Delta(days=1)
    yesterday = (Datetime.Now() - delta).date()

    for i in range(0, 10):

        date_object = Datetime.Now() - (delta * i)
        title = '%s %s %s' % (DAY[date_object.weekday()], date_object.day, MONTH[date_object.month])

        oc.add(DirectoryObject(key=Callback(Overview, title=title, path='/page/catalogue/?dateFrom=%s' % (date_object.date())), title=title))

    return oc

####################################################################################################


@route('/video/npo/az')
def AZ(**kwargs):

    oc = ObjectContainer(title2='Programma\'s A-Z')

    json_obj = JSON.ObjectFromURL('%s/page/catalogue' % (API_BASE_URL))

    programmes = find_grid_all(json_obj, pages=7)
    programmes = sorted(programmes, key=lambda x: x["title"], reverse=True)

    for programme in programmes:

        thumbs = []
        try:
            thumbs.append(programme['images']['original']['formats']['original']['source'])
        except:
            pass

        if programme.get("isMovie"):
            try:
                oc.add(VideoClipObject(
                    url=EPISODE_URL % (programme['id']),
                    title=programme['title'],
                    summary=programme['description'],
                    duration=programme['duration'] * 1000,
                    # originally_available_at=airdate.date(),
                    thumb=Resource.ContentsOfURLWithFallback(thumbs)
                ))
            except:
                pass

        else:
            oc.add(DirectoryObject(
                key=Callback(Series, series_id=programme['id']),
                title=programme['title'],
                summary=programme['description'],
                thumb=Resource.ContentsOfURLWithFallback(thumbs)
            ))

    return oc
