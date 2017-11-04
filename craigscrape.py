"""
Stand alone script that peruses craigslist car/truck page for certain vehicles
Sends text updates when new vehicles are found
"""

import urllib3
import certifi
import bs4 as bs
import time
from datetime import datetime
from random import randint
import base64

class Search(object):
    def __init__ (self, loc, year, make, model, key):
        self.loc = loc
        self.year = year
        self.make = make
        self.model = model
        self.key = key

#potentially take user info from CL if client wants to run script without interacting with code
scrape_list = ['bham_2001_ford_ranger'] #loc_year_make_model, append similar format for other vehicles

#holds posts that have been accounted for, keyed by the search terms
ref_dict = {}
for i in scrape_list:
    ref_dict[i] = []

#https://bham.craigslist.org/search/cta?query=2002+toyota+highlander&auto_paint=9
def heavy_scrape(target):
    print('\n[+++   SCRAPER ACTIVATED', datetime.now(), '  +++]')

    try:
        result = get_req(target) #result is list of html segments contianing each post
        for t in result:
            line = str(t).split("<")
            pid = ''
            price = 'No Price Shown'
            post_date = ''
            location = ''
            link = ''
            description = ''
            for j in line:
                if "data-pid" in j and "maptag" not in j:
                    pid_frame = j.split('">')
                    inter = pid_frame[0].replace('li class="result-row" data-pid="','')
                    pid = inter.split('"')[0]
                elif "result-price" in j:
                    price = j.replace('span class="result-price">','')
                elif "datetime=" in j:
                    date_frame = j.split('title=')
                    date2_frame = date_frame[1].split('>')
                    post_date = date2_frame[0].replace('"','')
                elif 'class="result-hood"' in j:
                    loc_frame = j.split('(')
                    location = loc_frame[1].replace(')', '')
                elif 'class="nearby"' in j:
                    loc2_frame = j.split('>')
                    location = loc2_frame[0].replace('span class="nearby" title=','').replace('"','')
                elif 'result-title hdrlnk' in j:
                    url_frame = j.split('href=')
                    url2_frame = url_frame[1].split('>')
                    description = url2_frame[1]
                    link = url2_frame[0].replace('"','')
                    if 'craigslist' not in link:
                        link = 'https://' + loc + '.craigslist.org' + link
            
            if target.model.upper() in description.upper() and target.year in description: #keeps "similar" results out
                if pid not in ref_dict[target.key]:
                    ref_dict[target.key].append(pid)
                    print("[+]     *** NEW POSTING ***    *** NEW POSTING ***     [+]")
                    print('Description:', description)
                    print('Date:', post_date)
                    print('Location:', location)
                    print('Price:', price)
                    print('PID:', pid)
                    print('Link:', link, '\n')
                    
                    text_alert(post_date, location, year, model, price, link)
            
    except:
        print("[-] HEAVY SCRAPER CRASH [-]")


def light_scrape(target):
    print("[+]  !!!     LIGHT SCRAPER LIST UPDATER INITIATED   !!!    [+]")

    try:
        result = get_req(target)
        for t in result:
            line = str(t).split("<")
            pid = ''
            for j in line:
                if "data-pid" in j and "maptag" not in j:
                    pid_frame = j.split('">')
                    inter = pid_frame[0].replace('li class="result-row" data-pid="','')
                    pid = inter.split('"')[0]
                elif 'result-title hdrlnk' in j:
                    url_frame = j.split('href=')
                    url2_frame = url_frame[1].split('>')
                    description = url2_frame[1] 
                
            if target.model.upper() in description.upper() and target.year in description: #keeps irrelevant results out
                if pid not in ref_dict[target.key]:
                    ref_dict[target.key].append(pid)
                    print("[+]                *** PID LIST UPDATED ***                [+]")
                    print("                 ~ NO EXTERNAL NOTIFICATION ~")

                    
    except:
        print("[-] LIGHT SCRAPER CRASH [-]")

def get_req(target):
    #HTTP Requests
    url = 'https://' + target.loc + '.craigslist.org/search/cta?query=' + target.year + '+' + target.model + '+' + target.make
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    r = http.request('GET', url, headers={'User-agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0'})

    #Parsing
    html = r.data
    soup = bs.BeautifulSoup(html, 'lxml')
    result = soup.find_all('li', {'class':"result-row"}) #separates each post
    return result


def text_alert(post_date, location, year, model, price, link):
    #Texting authorization
    from twilio.rest import Client
    creds = []
    cred_file = open('k:/Creds/twilio_creds.txt','r')
    #decrypts the saved file containing access tokens
    for entry in cred_file.readlines():
        i = base64.b64decode(entry.strip('\n'))
        creds.append(str(i,'utf-8'))

    ACCOUNT_SID = creds[0]
    AUTH_TOKEN  = creds[1]
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    message = post_date + ' in ' + location + ', ' + year + ' ' + model + ' for ' + price + ', Link: ' + link
    try:
        client.messages.create(
        to= "", #creds[2], #"1"+"9DIGIT#"
        from_=creds[3],
        body=message
        )
        print("[+] Text Alert Sent [+]")
    except:
        print("[-] !!! Text Alert Failure !!! [-]")

    
def main():
    #read_in() #reads in all catalogued posts, and adds them to instance memory so that text results arent sent out for old vehicles
    target_list = []
    try:
        for i in scrape_list:
            beta = i.split('_')
            target = Search(beta[0], beta[1], beta[2], beta[3], i)
            target_list.append(target) #stores target objects
            light_scrape(target)
    except KeyboardInterrupt:
        print("[-] Manually Exited During Startup [-]")

    run = True
    while run:
        try:
            for entry in target_list:
                heavy_scrape(entry)
                time.sleep(randint(5, 9)) #feeble attempt to not look like a bot when iterating over several target vehicles

            time.sleep(120) #sleeps 2 min after iterating over all the cars were looking for
        except KeyboardInterrupt:
            print("[-] Manual Exit [-]")
            run = False

    print("[--- !!! SCRAPER DEACTIVATED", datetime.now(), " !!! ---]")


if __name__ == '__main__':
    main()

