
#from urllib.parse import urlencode
import json 
import urllib2
import urllib

########################################################################
class QClient(object):
    """
    
    """
    __clientId      = ""
    __clientSecret  = ""
    __accessToken   = ""

    __oauth         = ""
    
    #----------------------------------------------------------------------
    def __init__(self, clientId, clientSecret, accessToken):
        """Constructor"""
        self.__clientId      = clientId
        self.__clientSecret  = clientSecret
        self.__accessToken   = accessToken
        self.__oauth = QOAuth2(clientId, clientSecret, accessToken)

    #----------------------------------------------------------------------
    def userMe(self):
        """"""
        url = self.__oauth.getUrl('host')
        url = ''.join((url, '/user/me.json'))

        data = {
            'access_token'     : self.__accessToken
        }

        return self.__oauth.getRequest(url, data)
    


class QOAuth2(object):
    """"""
    __clientId      = ""
    __clientSecret  = ""
    __accessToken   = ""

    __host             = "https://openapi.360.cn"
    __authorizeURL     = "https://openapi.360.cn/oauth2/authorize"
    __accessTokenURL   = "https://openapi.360.cn/oauth2/access_token"

    #----------------------------------------------------------------------
    def __init__(self, clientId, clientSecret, accessToken=''):
        """Constructor"""
        self.__clientId      = clientId
        self.__clientSecret  = clientSecret
        self.__accessToken   = accessToken

    #----------------------------------------------------------------------
    def getUrl(self, name):
        """"""
        if name == 'host':
            return self.__host
        elif name == 'authorize':
            return self.__authorizeURL
        elif name == 'accesstoken':
            return self.__accessTokenURL

    #----------------------------------------------------------------------
    def getAuthorizeURL(self, responseType, redirectUri, scope='', state='', display=''):
        """"""
        data = {
            'client_id'     : self.__clientId,
            'response_type'  : responseType,
            'redirect_uri'  : redirectUri
        }

        if scope:
            data['scope'] = scope
        if state:
            data['state'] = state
        if display:
            data['display'] = display

        query = self._buildHttpQuery(data)
        return ''.join((self.__authorizeURL, '?', query))

    #----------------------------------------------------------------------
    def getAccessTokenByCode(self, code, redirectUri):
        data = {
            'grant_type'       : "authorization_code",
            'code'             : code,
            'client_id'        : self.__clientId,
            'client_secret'    : self.__clientSecret,
            'redirect_uri'     : redirectUri,
            'scope'            : 'basic'
        }

        return self.getRequest(self.__accessTokenURL, data)

    #----------------------------------------------------------------------
    def getAccessTokenByRefreshToken(self, refreshToken, scope):
        data = {
            'grant_type'    : "refresh_token",
            'refresh_token' : refreshToken,
            'client_id'     : self.__clientId,
            'client_secret' : self.__clientSecret,
            'scope'         : scope
        }

        return self.getRequest(self.__accessTokenURL, data)

    #----------------------------------------------------------------------
    def getRequest(self, url, data):
        if data:
            query = self._buildHttpQuery(data)
            url = ''.join((url, '?', query))
        response = self._makeRequest(url, 'GET')

        return json.JSONDecoder().decode(response)
    
    #----------------------------------------------------------------------
    def _makeRequest(self, url, method = 'GET', postdata = ""):
        """"""
        print url
        request = urllib2.Request(url)
        request.add_header('User-Agent', "QIHOO360 PYTHONSDK API v0.0.1")

        if method == 'GET':
            resp = urllib2.urlopen(request)
            body = resp.read()
            return body  
            #return urlopen(request).read().decode('utf-8')
        elif method == 'POST':
            return urlopen(request, postdata).read().decode('utf-8')

    #----------------------------------------------------------------------
    def _buildHttpQuery(self, data):
        if not data:
            return '';


        args = []
        for k, v in data.iteritems():
            qv = v.encode('utf-8') if isinstance(v, unicode) else str(v)
            args.append('%s=%s' % (k, urllib.quote(qv)))
        return '&'.join(args)



        params = self._sortDictByKey(data)
        print "ddddddddddd", params, type(params), type(data)
        for p in params:
            print p, type(p)
        return urllib.quote(data)

    #----------------------------------------------------------------------
    def _sortDictByKey(self, adict):
        return sorted(adict.items(), key=lambda adict:adict[0])





        

        
    

    
        
