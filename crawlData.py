import requests
from lxml import etree
import json
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import concurrent.futures

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Cookie': '_zap=9d729e47-6f14-48a3-ae15-890940567d51; d_c0=AXDWAWCHeBiPTtJgVSlg2a9UAdUhp0fbfmM=|1713185411; user_device_id=a9cd5e72eebe4d3ba8c320af6b2823e1; user_device_id_timestamp=1713185403622; _xsrf=a507LFzg0dnZTASAnx5Dfmsi87aCaDeX; __snaker__id=vSQuPSGurydtY2X2; q_c1=e91a699ee9e04dbebf07935485e2268c|1713593381000|1713593381000; __zse_ck=001_7a5o2DXRa5/g8fh6AhmlSU1lFlXtCI7xdbfSzOb+NVxDkFYb=Wfl0moRwQZOi=HT9SW0CTqPRRFveYSF6Nd0z/pTKX1acjVLULpKVqaOhFwsKO2uxzgu4JwOTlzJZYmY; z_c0=2|1:0|10:1720608936|4:z_c0|80:MS4xRFdOTkRnQUFBQUFtQUFBQVlBSlZUVnpVYjJmWEV6Y2VMRGJfcWZ0NkZGcnNOVzZxcW9yYTBBPT0=|ddf9b5eceaf0519ce5b6e778c7da1cf461c3d5cc165bd5ea8b8ed02fa8c096d8; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1718280008,1719830106,1720509069,1720608938; HMACCOUNT=821CC66FA9BBDE84; BEC=244e292b1eefcef20c9b81b1d9777823; Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49=1720609030; tst=h; SESSIONID=qdKZNJosevFoEscfrrqiRF4mXjNRsV7cUQFx5LHMcpu; JOID=VFgUBk7dxFykPV1BXd7Rge9R2TxCqqET_nARLyq7tBvPeC0kOtKo1sE4WkRZLFRHZ1XtDU57E4BwB7koBK-om6s=; osd=V1gQC0jexFipO15BWdPXgu9V1DpBqqUe-HMRKye9txvLdSsnOtal0MI4XklfL1RDalPuDUp2FYNwA7QuB6-slq0='
}


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def getTitle():
    session = requests_retry_session()
    page_source = session.get(
        'https://www.zhihu.com/hot', headers=headers).text
    tree = etree.HTML(page_source)
    Hotlist = tree.xpath('//div[@class="HotItem-content"]')[:10]
    Msglist = []
    for h in Hotlist:
        title = h.xpath('.//h2/text()')[0]
        content = h.xpath('.//p/text()')
        href = h.xpath('.//a[@href]/@href')[0]
        _id = href.split('/')[-1]

        msg = {
            'title': title,
            'id': _id,
            'content': content,
        }
        Msglist.append(msg)
    return Msglist


answerList = []


def parse(respInfo, title, qid, content):
    for i in respInfo['data']:
        tid = str(i['target']['id'])
        try:
            cont = i['target'].get('content', '')
            tree = etree.HTML(cont)
            anscont = ''.join([j.strip() for j in tree.xpath('string(.)')])
        except:
            anscont = ''
        msg = {

            'answer_id': tid,
            'question_title': title,
            'question_content': content,
            'question_id': qid,
            'answer_content': anscont
        }
        answerList.append(msg)

    return respInfo['paging']['next']


def get_zhihu_answers(question_id, title, content):
    session = requests_retry_session()
    url = f'https://www.zhihu.com/api/v4/questions/{question_id}/feeds?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cattachment%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Cis_labeled%2Cpaid_info%2Cpaid_info_content%2Creaction_instruction%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cvip_info%2Cbadge%5B%2A%5D.topics%3Bdata%5B%2A%5D.settings.table_of_content.enabled&limit=5&offset=0&order=default&platform=desktop'
    params = {'include': 'data[*].is_normal,content',
              'limit': 25}

    while url:
        response = session.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print('Cannot access the website')
            break
        data = response.json()
        print("parse answer")
        next_page = parse(data, title, question_id, content)
        if not next_page:
            break
        url = next_page


def fetch_all_answers(hot_titles):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(
            get_zhihu_answers, item['id'], item['title'], item['content']) for item in hot_titles]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error occurred: {e}")


HotTitleList = getTitle()
fetch_all_answers(HotTitleList)

with open('zhihu_data2.json', 'w', encoding='utf-8') as f:
    json.dump(answerList, f, ensure_ascii=False, indent=4)
