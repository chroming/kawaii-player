"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import re
import json
from bs4 import BeautifulSoup
from player_functions import ccurl


class Shoutcast():
    
    def __init__(self, tmp):
        self.hdr = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'
        self.tmp_dir = tmp
        
    def getOptions(self):
            criteria = ['History', 'Genre']
            return criteria
        
    def getFinalUrl(self, name, epn, mir, quality):
        return epn
        
    def process_page(self, content):
        content = re.sub(r'\\', "-", content)
        try:
            l = json.loads(content)
        except Exception as err:
            print(err, '--49--')
            o = re.findall('{[^}]*}', content)
            l = []
            for i in o:
                print(i)
                try:
                    j = json.loads(i)
                    print(j['ID'], j['Name'])
                    l.append(j)
                except Exception as err:
                    print(err, '--58--')
        s = []
        for i in l:
            try:
                s.append(i['Name'].replace('/', '-')+'	id='+str(i['ID'])+'|Bitrate='+str(i['Bitrate'])+'|Listeners='+str(i['Listeners']))
            except Exception as err:
                print(err, '--64--')
        return s
        
    def search(self, name):
        strname = str(name)
        print(strname)
        if name.lower() == 'tv':
            m = self.getCompleteList(name.upper(), 1)
        else:
            url = "https://www.shoutcast.com/Home/BrowseByGenre"
            post = "genrename="+name
            content = ccurl(url+'#'+'-d'+'#'+post)
            m = self.process_page(content)
        return m
        
    def getCompleteList(self, opt, genre_num):
        m = []
        if opt == 'Genre' and genre_num == 0:
            url = "http://www.shoutcast.com/"
            content = ccurl(url)
            m = re.findall('Genre[^"]name[^"]*', content)
            j = 0
            for i in m:
                m[j] = re.sub('Genre[^"]name=', '', i)
                m[j] = re.sub("[+]|%20", ' ', m[j])
                j = j+1
            m.sort()
            print(m)
            n = ["History", "Genre"]
            m = n + m
        elif opt == 'History':
            pass
        elif opt == 'TV':
            pass
        else:
            url = "https://www.shoutcast.com/Home/BrowseByGenre"
            post = 'genrename='+opt
            content = ccurl(url+'#'+'-d'+'#'+post)
            m = self.process_page(content)
        print(opt, url)
        return m
    
    def getEpnList(self, name, opt, depth_list, extra_info, siteName, category):
        name_id = (re.search('id=[^|]*', extra_info).group()).split('=')[1]
        file_arr = []
        id_station = int(name_id)
        station_url = ''
        if opt == "TV" or '-TV' in name:
            pass
        else:
            url = "https://www.shoutcast.com/Player/GetStreamUrl"
            post = 'station='+str(id_station)
            content = ccurl(url+'#-d#'+post)
            m = re.findall('http://[^"]*', content)
            station_url = str(m[0])
        file_arr.append(name+'	'+station_url+'	'+'NONE')
        record_history = True
        return (file_arr, 'Summary Not Available', 'No.jpg', record_history, depth_list)
        

    def getNextPage(self, opt, pgn, genre_num, name):
        m = []
        return m
