import requests,json,re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
}

login_url = "https://pass.neu.edu.cn/tpass/login?service=http%3A%2F%2F219.216.96.4%2Feams%2FhomeExt.action"
login_post_url = "https://pass.neu.edu.cn/tpass/login?service=http%3A%2F%2F219.216.96.4%2Feams%2FhomeExt.action"
schedule_url = "http://219.216.96.4/eams/courseTableForStd.action"
schedule_post_url = "http://219.216.96.4/eams/courseTableForStd!courseTable.action"
user_info_url = "http://219.216.96.4/eams/stdDetail.action?"


def str_to_list(course_str):
    i = 0
    res = []
    for item in course_str:
        if(item == '1'):
            res.append(i)
        i += 1
    return res


def get_course(login_cookies, semester):
    post_data = {
        'ignoreHead': '1',
        'showPrintAndExport': '1',
        'setting.kind': 'std',
        'startWeek': '',
        'project.id': '1',
        'semester.id': semester,
        'ids': '46600'
    }

    course_data = requests.post(schedule_post_url, data=post_data, headers=headers, cookies=login_cookies)
    teachers = re.findall('var teachers = \[{id:.*?,name:"(.*?)",lab:false}\];', course_data.text)
    course_names = re.findall('actTeacherName.join\(\',\'\),".*?","(.*?)"', course_data.text)
    course_classroom = re.findall('actTeacherName.join\(\',\'\),".*?",".*?",".*?","(.*?)"', course_data.text)
    course_weeks_str = re.findall('actTeacherName.join\(\',\'\),".*?",".*?",".*?",".*?","(.*?)"', course_data.text)
    course_class = re.findall('activity = new TaskActivity([\s\S]*?)var teachers', course_data.text)
    course_class = course_class + re.findall('activity = new TaskActivity([\s\S]*?)table0.marshalTable', course_data.text)

    for count in range(0,len(course_class)):
        day = re.findall('index =(\d+)\*unitCount\+\d+',course_class[count])
        class_num = re.findall('index =\d+\*unitCount\+(\d+)', course_class[count])
        this_course = []
        for cour in range(0,len(day)):
            this_course.append({'day': day[cour],'class_num': class_num[cour]})
        course_class[count] = this_course

    res = []
    for i in range(0,len(teachers)):
        course = {
            'teacher': teachers[i],
            'name': course_names[i],
            'classroom': course_classroom[i],
            'weeks': course_weeks_str[i],
            'time': course_class[i]
        }
        res.append(course)

    return res


def index_login(uid, pwd):
    login_page = requests.get('https://pass.neu.edu.cn/tpass/login')
    lt = re.findall("input type=\"hidden\" id=\"lt\" name=\"lt\" value=\"(.*?)\" />", login_page.text)[0]
    execution = re.findall("input type=\"hidden\" name=\"execution\" value=\"(.*?)\" />", login_page.text)[0]
    rsa = uid+pwd+lt
    ul = len(uid)
    pl = len(pwd)

    post_data = {
        'rsa': rsa,
        'ul': ul,
        'pl': pl,
        'lt': lt,
        'execution': execution,
        '_eventId': 'submit'
    }

    login_post = requests.post('https://pass.neu.edu.cn/tpass/login', headers=headers,cookies=login_page.cookies, data=post_data)
    for i in login_post.history:
        if 'tp_up' in i.cookies:
            return i.cookies

    return None


def get_card(cookies):
    res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getCardMoney', cookies=cookies, headers=headers, data='{}')
    return json.loads(res.text)


def get_net(cookies):
    res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getWlzzList', cookies=cookies, headers=headers, data='{}')
    return json.loads(res.text)


def get_email(cookies):
    res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getBindEmailInfo', cookies=cookies, headers=headers, data='{}')
    return json.loads(res.text)


def get_finance(cookies):
    res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getFinanceInfo', cookies=cookies, headers=headers, data='{}')
    return json.loads(res.text)


def jwc_login(uid, pwd):
    login_page = requests.get(login_url)
    lt = re.findall("input type=\"hidden\" id=\"lt\" name=\"lt\" value=\"(.*?)\" />", login_page.text)[0]
    execution = re.findall("input type=\"hidden\" name=\"execution\" value=\"(.*?)\" />", login_page.text)[0]
    rsa = uid+pwd+lt
    ul = len(uid)
    pl = len(pwd)

    post_data = {
        'rsa': rsa,
        'ul': ul,
        'pl': pl,
        'lt': lt,
        'execution': execution,
        '_eventId': 'submit'
    }

    login_post = requests.post(login_post_url,  headers=headers, cookies=login_page.cookies, data=post_data)
    table_cookies = dict(JSESSIONID=login_post.history[-1].cookies['JSESSIONID'], GSESSIONID=login_post.cookies['GSESSIONID'])
    if len(login_post.history) != 0:
       return table_cookies
    else:
        return 0


def get_mobile(cookies):
    post_url = 'https://portal.neu.edu.cn/tp_up/sys/uacm/profile/getMobileEmail'
    my_headers = {
        'Referer': 'https://portal.neu.edu.cn/tp_up/view?m=up',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
        'Origin': 'https://portal.neu.edu.cn',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    response = requests.post(post_url, headers=my_headers, cookies=cookies, data='{}')
    return json.loads(response.text)

def get_user_info(login_cookies):
    user_info = requests.get(user_info_url, cookies=login_cookies, headers=headers)
    stu_id = re.findall('学号：[\s\S]*?<td width="25%">(.*?)</td>', user_info.text)[0]
    img_url = 'http://219.216.96.4'+re.findall('<img width="80px" height="110px" src="(.*?)"', user_info.text)[0]
    head_img = requests.get(img_url, cookies=login_cookies, headers=headers)
    with open('head/'+stu_id+'.jpg', 'wb+') as f:
        f.write(head_img.content)
    res = {
        'name': re.findall('姓名[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'en_name': re.findall('英文名[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'gender': re.findall('性别[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'grade': re.findall('年级[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'es': re.findall('学制[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'type': re.findall('项目[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'edu_level': re.findall('学历层次[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'college': re.findall('院系[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'major': re.findall('专业[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'school_area': re.findall('所属校区[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'class': re.findall('所属班级[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'in_time': re.findall('入校时间[\s\S]*?<td>(.*?)</td>', user_info.text)[0],
        'out_time': re.findall('毕业时间[\s\S]*?<td>(.*?)</td>', user_info.text)[0]
    }
    return res


def get_library_url(cookies):
    lib_headers = {
        'Referer': 'https://portal.neu.edu.cn/tp_up/view?m=up',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
        'Origin': 'https://portal.neu.edu.cn',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    page = requests.get('https://portal.neu.edu.cn/tp_up/up/subgroup/library', cookies=cookies, headers=lib_headers)
    library_url = re.findall('var url = "(.*?)"', page.text)[0]
    return library_url


def get_card_cookie(uid, pwd):

    card_url = 'https://pass.neu.edu.cn/tpass/login?service=http://ecard.neu.edu.cn/selflogin/login.aspx'

    login_page = requests.get(card_url, headers=headers)
    lt = re.findall("input type=\"hidden\" id=\"lt\" name=\"lt\" value=\"(.*?)\" />", login_page.text)[0]
    execution = re.findall("input type=\"hidden\" name=\"execution\" value=\"(.*?)\" />", login_page.text)[0]
    rsa = uid+pwd+lt
    ul = len(uid)
    pl = len(pwd)

    post_data = {
        'rsa': rsa,
        'ul': ul,
        'pl': pl,
        'lt': lt,
        'execution': execution,
        '_eventId': 'submit'
    }

    login_post = requests.post(card_url,  headers=headers, cookies=login_page.cookies, data=post_data)

    data = {
        'username': re.findall("<input type=hidden name='username' id='username' value='(.*?)'/>", login_post.text)[0],
        'timestamp': re.findall("<input type=hidden name='timestamp' id='timestamp' value='(.*?)'/>", login_post.text)[0],
        'auid': re.findall("<input type=hidden name='auid' id='auid' value='(.*?)'/>", login_post.text)[0]
    }

    get_session = requests.post('http://ecard.neu.edu.cn/selfsearch/SSOLogin.aspx', cookies=login_post.cookies, data=data, headers=headers)

    return {'.ASPXAUTSSM':get_session.history[0].cookies['.ASPXAUTSSM'], 'ASP.NET_SessionId': login_post.cookies['ASP.NET_SessionId']}


def get_card_page(cookies):
    info_url = 'http://ecard.neu.edu.cn/selfsearch/User/Home.aspx'
    info_page = requests.get(info_url, cookies=cookies)
    return re.findall('<span>卡状态：(.*?)</span>', info_page.text)[0]


def get_card_trade(cookies,start,end):
    trade_url = 'http://ecard.neu.edu.cn/selfsearch/User/ConsumeInfo.aspx'
    page = 1
    res = []
    query_page = requests.get('http://ecard.neu.edu.cn/selfsearch/User/ConsumeInfo.aspx',cookies=cookies)

    while True:
        data = {
            '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$AspNetPager1',
            '__EVENTARGUMENT': str(page),
            '__VIEWSTATE': re.findall('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE"[\s\S]*?value="(.*?)"', query_page.text )[0],
            '__EVENTVALIDATION': re.findall('<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="(.*?)" />', query_page.text)[0],
            'ctl00$ContentPlaceHolder1$rbtnType': '0',
            'ctl00$ContentPlaceHolder1$txtStartDate': start,
            'ctl00$ContentPlaceHolder1$txtEndDate': end,
            'ctl00$ContentPlaceHolder1$btnSearch': '查  询'
        }

        print(res)
        query_page = requests.post(trade_url, data=data, cookies=cookies, headers=headers)
        page_num = re.findall('style="margin-right:5px;">(\d+)</a>', query_page.text)
        trade_time = re.findall('<span id="Content.*?">(.*?)</span>', query_page.text)
        trade_type = re.findall('</td><td>(.*?)</td><td align="right">.*?</td><td align="right">.*?</td><td>.*?</td><td>.*?</td><td>.*?</td>', query_page.text)
        cost = re.findall('</td><td>.*?</td><td align="right">(.*?)</td><td align="right">.*?</td><td>.*?</td><td>.*?</td><td>.*?</td>', query_page.text)
        remind = re.findall('</td><td>.*?</td><td align="right">.*?</td><td align="right">(.*?)</td><td>.*?</td><td>.*?</td><td>.*?</td>', query_page.text)
        salesman = re.findall('</td><td>.*?</td><td align="right">.*?</td><td align="right">.*?</td><td>(.*?)</td><td>.*?</td><td>.*?</td>', query_page.text)
        place = re.findall('</td><td>.*?</td><td align="right">.*?</td><td align="right">.*?</td><td>.*?</td><td>(.*?)</td><td>.*?</td>', query_page.text)
        terminal_name = re.findall('</td><td>.*?</td><td align="right">.*?</td><td align="right">.*?</td><td>.*?</td><td>.*?</td><td>(.*?)</td>', query_page.text)
        for i in range(0,len(trade_time)):
            if(trade_time[i]==''):
                break
            res.append({
                'trade_time': trade_time[i],
                'trade_type': trade_type[i],
                'trade_cost': cost[i],
                'remaind': remind[i],
                'salesman': salesman[i],
                'place': place[i],
                'terminal': terminal_name[i]
            })
        print(page, page_num)
        if (str(page+1) in page_num) == False:
            break
        page+=1

    return res


def lost_card(cookies, pwd, cid):
    lost_url = 'http://ecard.neu.edu.cn/selfsearch/User/UserLoss.aspx'

    data = {
        '__VIEWSTATE': '/wEPDwUINDEyMzA5NDkPFgIeCFNvcnRUeXBlBQNBU0MWAmYPZBYCAgMPZBYCAgMPZBYCAgQPPCsAEQIADxYEHgtfIURhdGFCb3VuZGceC18hSXRlbUNvdW50ZmQBEBYAFgAWABYCZg9kFgJmD2QWAgIBD2QWAgIBDw8WBB4IQ3NzQ2xhc3MFClNvcnRCdF9Bc2MeBF8hU0ICAmRkGAEFImN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkZ3JpZFZpZXcPPCsADAEIZmQ0WhVfM7Uh5Zuzbyoj5u1+C7p6oWEvTHpJJl1N74TkCA==',
        '__EVENTVALIDATION': 'wEWBgLypayJDQL8+9SXBwLE2/a/AgL3k5rWDgKE9dfUCQKG1qD0Ca733nFJ79yjQO/TvoLGgdI4fClToCF2HiXRVYPHHy0j',
        'ctl00$ContentPlaceHolder1$txtPwd': pwd,
        'ctl00$ContentPlaceHolder1$txtIDcardNo': cid,
        'ctl00$ContentPlaceHolder1$btnLoss': '挂  失'
    }
    response = requests.post(lost_url, data=data, cookies=cookies, headers=headers)




def get_library_info(library_url):
    response_data = requests.get(library_url)
    borrow_url = re.findall('外借[\s\S]*?href="javascript:replacePage\(\'(.*?)\'\)', str(response_data.content,'utf8'))[0]
    borrow_res = str(requests.get(borrow_url).content, 'utf8')

    writers = re.findall('<td class=td1 valign=top width="8%" >(.*?)<', borrow_res)
    books = re.findall('target=_blank>(.*?)</a></td', borrow_res)
    back_day = re.findall('<td class=td1 valign=top width="10%">(.*?)</td>', borrow_res)
    books_code = re.findall('<input type="checkbox" name="(.*?)"></td>', borrow_res)
    long_url =re.findall('var strData = "(.*?)"', borrow_res)[0]

    res = []
    for i in range(0, len(writers)):
        res.append({
            'writer': writers[i],
            'book': books[i],
            'back_day': back_day[2*i],
            'book_code': books_code[i],
        })

    return {'extend_url': long_url, 'book_data':res}


#cookies = jwc_login('20183496', '106113')

cookies = get_card_cookie('20183496', '106113')
print(get_card_trade(cookies, '2019-04-08','2019-05-10'))
