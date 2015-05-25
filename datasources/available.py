
import urllib2
import re
import numpy as np
from datetime import datetime, timedelta

spc_base_url = "http://www.spc.noaa.gov/exper/soundings/"

def _available_spc():
    '''
        _available_spc()

        Gets all of the available sounding times from the SPC site.

        Returns
        -------
        matches : array
            Array of datetime objects that represents all the available times
            of sounding data on the SPC site.
    '''
    text = urllib2.urlopen(spc_base_url).read()
    matches = sorted(list(set(re.findall("([\d]{8})_OBS", text))))
    return [ datetime.strptime(m, '%y%m%d%H') for m in matches ]

def _availableat_spc(dt):
    '''
        _availableat_spc(dt)

        Get all the station locations where data was available for a certain dt object.

        Parameters
        ----------
        dt : datetime object

        Returns
        -------
        matches : array of strings
            An array that contains all of the three letter station identfiers.
    '''
    recent_url = "%s%s/" % (spc_base_url, dt.strftime('%y%m%d%H_OBS'))
    text = urllib2.urlopen(recent_url).read()
    matches = re.findall("alt=\"([\w]{3}|[\d]{5})\"", text)
    return matches

psu_base_url = "ftp://ftp.meteo.psu.edu/pub/bufkit/"
psu_text = ""
psu_time = None

def _download_psu():
    '''
        _download_psu()

        Downloads the PSU directory webpage that lists all the
        files available.

        Returns
        -------
        psu_text : string
            Lists the files within the PSU FTP site.
    '''
    global psu_time, psu_text
    now = datetime.utcnow()
    if psu_time is None or psu_time < now - timedelta(minutes=5):
        psu_time = now

        url_obj = urllib2.urlopen(psu_base_url)
        psu_text = url_obj.read()

    return psu_text 

def _availableat_psu(model, dt):
    '''
        _availableat_psu

        Downloads a list of all the BUFKIT profile stations for a given
        model and runtime.

        Parameters
        ----------
        model : string
            A string representing the forecast model requested
        dt : datetime object
            A datetime object that represents the model initalization time.
    '''
    if model == '4km nam': model = 'nam4km'
    _repl = {'gfs':'gfs3', 'nam':'namm?', 'rap':'rap', 'nam4km':'nam4kmm?', 'hrrr':'hrrr', 'sref':'sref'}

    cycle = dt.hour
    url = "%s%s/%02d/" % (psu_base_url, model.upper(), cycle)
    url_obj = urllib2.urlopen(url)
    text = url_obj.read()
    stns = re.findall("%s_(.+)\.buf" % _repl[model], text)
    return stns

def _available_psu(model, nam=False, off=False):
    '''
        _available_psu

        Downloads a list of datetime objects that represents
        the available model times from the PSU server.

        Parameters
        ----------
        model : string
            the name of the forecast model
        nam : boolean (default: false)
            Specifies whether or not this is the NAM or 4km NAM 
        off : boolean (default: false)
            Specifies whether or not this is an off-hour run
    '''
    if model == '4km nam': model = 'nam4km'

    psu_text = _download_psu()
    latest = re.search("%s\.([\d]{12})\.done" % model, psu_text).groups(0)[0]
    dt = datetime.strptime(latest, "%Y%m%d%H%M")

    if nam and off and dt.hour in [ 0, 12 ]:
        dt -= timedelta(hours=6)
    if nam and not off and dt.hour in [ 6, 18 ]:
        dt -= timedelta(hours=6)
    return [ dt ]

pecan_base_url = 'http://weather.ou.edu/~map/real_time_data/'

def _available_oupecan():
    test_dt = datetime.strptime("13062500", '%y%m%d%H')
    return [test_dt]

def _availableat_oupecan(dt):
    dt_string = datetime.strftime(dt, '%y%m%d%H')
    url = "%s%s/soundings/" % (pecan_base_url, dt_string)
    url_obj = urllib2.urlopen(url)
    text = url_obj.read()
    dt_string = datetime.strftime(dt, '%Y%m%d%H')
    stns = re.findall("([\w]{3})_%s.txt" % dt_string, text)
    return np.unique(stns)

ncarens_base_url = 'http://sharp.weather.ou.edu/soundings/ncarens/'

def _available_ncarens():
    text = urllib2.urlopen(ncarens_base_url).read()
    matches = sorted(list(set(re.findall("([\d]{8}_[\d]{2})", text))))
    return [ datetime.strptime(m, '%Y%m%d_%H') for m in matches ]

def _availableat_ncarens(dt):
    dt_string = datetime.strftime(dt, '%Y%m%d_%H')
    url = "%s%s/" % (ncarens_base_url, dt_string)
    url_obj = urllib2.urlopen(url)
    text = url_obj.read()
    dt_string = datetime.strftime(dt, '%Y%m%d%H')
    stns = re.findall("([\w]{3}).txt", text)
    return stns


def _available_nssl(ens=False):
    path_to_nssl_wrf = ''
    path_to_nssl_wrf_ens = ''

# A dictionary of the available times for profiles from observations, forecast models, etc.
available = {
    'psu':{}, 
    'psu_off':{
        'nam':lambda: _available_psu('nam', nam=True, off=True),
        '4km nam':lambda: _available_psu('4km nam', nam=True, off=True)
    },
    'spc':{'observed':_available_spc},
    'ou_pecan': {'pecan ensemble': _available_oupecan },
    'ncar_ens': {'ncar ensemble': _available_ncarens },
}

# A dictionary containing paths to the stations for different observations, forecast models, etc.
# given a specific datetime object.
availableat = {
    'psu':{},
    'psu_off':{
        'nam':lambda dt: _availableat_psu('nam', dt),
        '4km nam':lambda dt: _availableat_psu('4km nam', dt)
    },
    'spc':{'observed':_availableat_spc},
    'ou_pecan': {'pecan ensemble': lambda dt: _availableat_oupecan(dt) },
    'ncar_ens': {'ncar ensemble': lambda dt: _availableat_ncarens(dt) },
}

# Loop through the various models and get all the times and stations for them
# This is test code.
for model in [ 'gfs', 'nam', 'rap', 'hrrr', '4km nam', 'sref' ]:
    available['psu'][model] = (lambda m: lambda: _available_psu(m, nam=(m in [ 'nam', '4km nam' ]), off=False))(model)
    availableat['psu'][model] = (lambda m: lambda dt: _availableat_psu(m, dt))(model)

if __name__ == "__main__":
    dt = available['psu']['gfs']()
    stns = availableat['psu']['gfs'](dt[0])
    #dt = available['spc']['observed']()
    #stns = availableat['spc']['observed'](dt[-1])
    dt = available['ou_pecan']
    stns = availableat['ou_pecan'](dt[0])
