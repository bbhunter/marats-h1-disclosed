import requests, sqlite3, hashlib, os, bitly_api

conn = sqlite3.connect('h1.db')
c = conn.cursor()
b = bitly_api.Connection(os.environ.get('BITLY_USER'), os.environ.get('BUTLY_KEY'))

new_reports = requests.get('https://hackerone.com/hacktivity?sort_type=latest_disclosable_activity_at&page=1&filter=type%3Apublic&querystring=', headers={
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
}).json()["reports"]

fcm_auth = {'Authorization': 'key='+os.environ.get('FCM_KEY'), 'Content-Type': 'application/json'}

def short_bitly(longurl):
    return b.shorten(uri=longurl)['url']

def distribute_new_report(report):
    r = requests.post('https://fcm.googleapis.com/fcm/send', json={
        "notification": {
            "title": report['title'],
            "body":  "%s just disclosed the report by %s" % (report['team']['profile']['name'], report['reporter']['username']),
            "click_action": short_bitly("https://hackerone.com" + report["url"]),
            "icon": report['team']['profile_picture_urls']['small']
        },
        "to": "/topics/h1"
    }, headers=fcm_auth)
    return r.status_code

def check_hash_for_existing(hash):
    return c.execute("SELECT hash FROM hash_table WHERE hash='%s'" % hash).fetchone() == None

def get_new_reports_and_add_to_hashtable_index(hash_table, new_reports):
    for report in new_reports:
        if report["readable_substate"]=="Resolved": # Filter shitty reports like spam or n/a 
            current_report_hash = hashlib.md5(report["title"].encode('utf-8')+str(report["id"])).hexdigest()
            if check_hash_for_existing(current_report_hash):
                # here what to do if parser found new reports :)
                print('New report:' + report['title'].encode('utf-8'))
                print(distribute_new_report(report))
                c.execute("INSERT INTO hash_table VALUES ('%s')" % current_report_hash)
                conn.commit()
            else:
                print('Old:'+report['title'].encode('utf-8'))
    print('done')
    conn.close()

get_new_reports_and_add_to_hashtable_index(c.execute('SELECT hash FROM hash_table'), new_reports)
