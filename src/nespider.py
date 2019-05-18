import requests, json, re, time


# 图书馆搜索引擎
class LibrarySearch(object):
    
    # 分析第一页获取 其他页的URL
    def __decode_first_text(self, text):
        return_list = []
        res = re.findall('<tr><td class=label1>作者：<td class=content valign=top>(.*?)<td class=lab\
el1>索书号：<td class=content valign=top>(.*?) \n<tr><td class=label1>出版社：<td class\
=content valign=top>(.*?)<td class=label>年份：<td class=content valign=top>(.*?) ', text)
        result_num = int(re.findall('(\d+) \(最大显示记录', text)[0])
        self.query_url = re.findall('10,"(.*?)1"\)</script></div>[\s\S]*?记录', text)[0]
        for i in res:
            return_list.append({
                'writer': i[0],
                'index': i[1],
                'publisher': i[2],
                'year': i[3]
            })
        self.sum = result_num
        self.first = return_list  # 保存第一页的信息

    def get_books(self, page):
        # 如果是第一页 直接返回第一页的信息 否则进行二次访问
        if page == 1 or page == '1':
            return self.first
        else:
            if int(page-1)*10 > self.sum:
                return None
            else:
                page = str(int(page)-1)+'1'
        text = str(requests.get(self.query_url+page).content, 'utf8')
        return_list = []
        res = re.findall('<tr><td class=label1>作者：<td class=content valign=top>(.*?)<td class=lab\
el1>索书号：<td class=content valign=top>(.*?) \n<tr><td class=label1>出版社：<td class\
=content valign=top>(.*?)<td class=label>年份：<td class=content valign=top>(.*?) ', text)
        for i in res:
            return_list.append({
                'writer': i[0],
                'index': i[1],
                'publisher': i[2],
                'year': i[3]
            })
        return return_list

    def __init__(self, keyword):
        # 查询参数
        param = '?func=find-b&find_code=WRD&request=%s&filter_code_1=WLN&filter_request_1=&filter_code_2=WYR&filter_request_2=&filter_code_3=WYR&filter_request_3=&filter_code_4=WFM&filter_request_4=&filter_code_5=WSL&filter_request_5='%keyword
        query_page = str(requests.get('http://202.118.8.7:8991/F/').content, 'utf8')  # 与line254相同 不能直接获取text 需要手动抓换
        post_url = re.findall('<form method=get name=form1 action="(.*?)" onsubmit="return presearch\(this\);">', query_page)[0]
        query_res = requests.get(post_url+param)
        query_text = str(query_res.content, 'utf8')
        self.__decode_first_text(query_text)  # 进行第一页的查询


class NeuStu(object):
    
    # 用于欺骗服务器的伪装头，通过这个伪装头，将爬虫伪装为Windows系统下的Chrome浏览器
    __headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
    }
    
    # 这个方法是在课表转换中使用的
    # 课表中为了表示某一周是否有课使用如：011011这种字符串来表示
    # 这种字符串的意义如下：
    # 若第i位（由0开始）为1为有课，0为无课
    @staticmethod
    def __week_num(week_str):
        res = []
        for i in range(0,len(week_str)):
            if week_str[i]=='1':
                res.append(i)
        return res

    # 一网通办登录，在登录过程中将由pass.neu.edu.cn 跳转至 portal.neu.edu.cn
    # 值得注意的是 这两个域名对应的cookies都是有用的
    # 对于一卡通、教务处将使用pass.neu.edu.cn的cookies进行跳转 这个cookies被命名为pass_cookies
    # 对于图书馆、将使用portal.neu.edu.cn的cookies进行跳转 这个cookies被命名为index_cookies
    def __index_login(self):
        login_page = requests.get('https://pass.neu.edu.cn/tpass/login')
        # 生成登录参数
        lt = re.findall("input type=\"hidden\" id=\"lt\" name=\"lt\" value=\"(.*?)\" />", login_page.text)[0]
        execution = re.findall("input type=\"hidden\" name=\"execution\" value=\"(.*?)\" />", login_page.text)[0]
        rsa = self.id + self.password + lt
        ul = len(self.id)
        pl = len(self.password)

        # JESESSIONID是一个必不可少的cookie
        self.pass_cookies['JSESSIONID'] = login_page.cookies['JSESSIONID']

        post_data = {
            'rsa': rsa,
            'ul': ul,
            'pl': pl,
            'lt': lt,
            'execution': execution,
            '_eventId': 'submit'
        }

        login_post = requests.post('https://pass.neu.edu.cn/tpass/login',
                                   headers=self.__headers,
                                   cookies=login_page.cookies,
                                   data=post_data)
        for i in login_post.history:
            if 'CASTGC' in i.cookies:
                self.pass_cookies['CASTGC'] = i.cookies['CASTGC']
            if 'tp_up' in i.cookies:
                self.index_cookies = i.cookies
                self.success = True

    # 通过一网通办登录图书馆，私有方法
    def __library_url(self):
        lib_headers = {
            'Referer': 'https://portal.neu.edu.cn/tp_up/view?m=up',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/74.0.3729.131 Safari/537.36',
            'Origin': 'https://portal.neu.edu.cn',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        page = requests.get('https://portal.neu.edu.cn/tp_up/up/subgroup/library', cookies=self.index_cookies, headers=lib_headers)
        library_url = re.findall('var url = "(.*?)"', page.text)[0]
        return library_url

    # 通过一网通办登录校园卡平台，私有方法
    def __card_login(self):
        card_url = 'https://pass.neu.edu.cn/tpass/login?service=http://ecard.neu.edu.cn/selflogin/login.aspx'
        response = requests.get(card_url, cookies=self.pass_cookies)

        data = {
            'username': re.findall("<input type=hidden name='username' id='username' value='(.*?)'/>", response.text)[0],
            'timestamp': re.findall("<input type=hidden name='timestamp' id='timestamp' value='(.*?)'/>", response.text)[0],
            'auid': re.findall("<input type=hidden name='auid' id='auid' value='(.*?)'/>", response.text)[0]
        }

        get_session = requests.post('http://ecard.neu.edu.cn/selfsearch/SSOLogin.aspx', cookies=response.cookies,
                                    data=data, headers=self.__headers)

        self.card_cookies ={
            '.ASPXAUTSSM': get_session.history[0].cookies['.ASPXAUTSSM'],
            'ASP.NET_SessionId': response.cookies['ASP.NET_SessionId']
        }

    # 通过一网通办登陆教务处，私有方法
    def __aao_login(self):
        aao_url = 'https://pass.neu.edu.cn/tpass/login?service=http%3A%2F%2F219.216.96.4%2Feams%2FhomeExt.action'
        response = requests.get(aao_url, cookies=self.pass_cookies, headers=self.__headers)
        jsessionid = ''
        for page in response.history:
            if 'JSESSIONID' in page.cookies:
                jsessionid = page.cookies['JSESSIONID']
        self.aao_cookies = dict(JSESSIONID=jsessionid, GSESSIONID=response.cookies['GSESSIONID'])

    # 校园卡余额、补助余额（不知道干什么的）
    @property
    def card_info(self):
        res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getCardMoney',
                            cookies=self.index_cookies,
                            headers=self.__headers,
                            data='{}')
        return json.loads(res.text)

    # 校园网使用情况
    @property
    def net_info(self):
        res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getWlzzList',
                            cookies=self.index_cookies,
                            headers=self.__headers,
                            data='{}')
        return json.loads(res.text)

    # 学生邮箱情况
    @property
    def email_info(self):
        res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getBindEmailInfo',
                            cookies=self.index_cookies,
                            headers=self.__headers,
                            data='{}')
        return json.loads(res.text)

    # 获取报销情况
    @property
    def finance_info(self):
        res = requests.post('https://portal.neu.edu.cn/tp_up/up/subgroup/getFinanceInfo',
                            cookies=self.index_cookies,
                            headers=self.__headers,
                            data='{}')
        return json.loads(res.text)

    # 获取学生一网通办绑定的手机号、邮箱
    @property
    def mobile_info(self):
        post_url = 'https://portal.neu.edu.cn/tp_up/sys/uacm/profile/getMobileEmail'
        my_headers = {
            'Referer': 'https://portal.neu.edu.cn/tp_up/view?m=up',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Origin': 'https://portal.neu.edu.cn',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        response = requests.post(post_url, headers=my_headers, cookies=self.index_cookies, data='{}')
        return json.loads(response.text)

    # 卡是否挂失
    @property
    def is_card_lost(self):
        # 如果还没有通过一网通办获取到一卡通的cookies，则获取
        if self.card_cookies==False:
            self.__card_login()
        info_url = 'http://ecard.neu.edu.cn/selfsearch/User/Home.aspx'
        info_page = requests.get(info_url, cookies=self.card_cookies)
        res =  re.findall('<span>卡状态：(.*?)</span>', info_page.text)[0]
        if res == '正常卡' :
            return False
        else:
            return True

    # 获取来自教务处的学生信息
    @property
    def user_info(self):
        # 如果尚未登录教务处，则尝试登录
        if self.aao_cookies == None:
            self.__aao_login()

        user_info = requests.get('http://219.216.96.4/eams/stdDetail.action?', cookies=self.aao_cookies, headers=self.__headers)
        stu_id = re.findall('学号：[\s\S]*?<td width="25%">(.*?)</td>', user_info.text)[0]
        # 下面的注释用于获取用户照片（学生证上的那个），并保存到相对于此文件的head文件夹下，保存为“学号.jpg”
        # 如果取消注释，则将启用该功能
        # img_url = 'http://219.216.96.4' + re.findall('<img width="80px" height="110px" src="(.*?)"', user_info.text)[0]
        # head_img = requests.get(img_url, cookies=self.aao_cookies, headers=self.__headers)
        # # 保存用户照片
        # with open('head/' + stu_id + '.jpg', 'wb+') as f:
        #     f.write(head_img.content)

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

    # 获取用户图书馆信息，由于信息一般较少，一次性获取
    # 由于无需参数，使用了property修饰器
    # 你可能注意到了，在所有图书馆页面，并没有使用requests-obj.text这样的用法，因为这样用不知道为何会引起乱码
    # 所以必须直接获取二进制信息，手动使用utf-8解码
    @property
    def library_info(self):
        library_url = self.__library_url()
        response_data = requests.get(library_url)
        borrow_url = re.findall('外借[\s\S]*?href="javascript:replacePage\(\'(.*?)\'\)', str(response_data.content, 'utf8'))[0]
        history_url = re.findall('借阅历史列表[\s\S]*?href="javascript:replacePage\(\'(.*?)\'\)', str(response_data.content, 'utf8'))[0]
        borrow_res = str(requests.get(borrow_url).content, 'utf8')
        history_res = str(requests.get(history_url).content, 'utf8')

        history = re.findall('<td class=td1 valign=top><a href=".*?" target=_blank>(.*?)</a></td>[\s\S]*?target=_blank>(.*?)</a></td>\
[\s\S]*?<td class=td1 valign=top>(.*?)</td>[\s\S]*?<td class=td1 valign=top>(.*?)</td>[\s\S]*?<td class=td1 valign=top>(.*?)</td>\
[\s\S]*?<td class=td1 valign=top>(.*?)</td>[\s\S]*?<td class=td1 valign=top>(.*?)</td>[\s\S]*?<td class=td1 valign=top><br></td>[\s\S]*?\
<td class=td1 valign=top>(.*?)</td>', history_res)

        writers = re.findall('<td class=td1 valign=top width="8%" >(.*?)<', borrow_res)
        books = re.findall('target=_blank>(.*?)</a></td', borrow_res)
        back_day = re.findall('<td class=td1 valign=top width="10%">(.*?)</td>', borrow_res)
        books_code = re.findall('<input type="checkbox" name="(.*?)"></td>', borrow_res)
        # extend_url 是用来续借的时候使用的，不必透露给用户，在library_continue_borrow中使用了这个链接
        extend_url = re.findall('var strData = "(.*?)"', borrow_res)[0]

        res = []
        histories = []
        for i in range(0, len(writers)):
            res.append({
                'writer': writers[i],
                'book': books[i],
                'back_day': back_day[2 * i],
                'book_code': books_code[i],
            })

        for i in range(0, len(history)):
            histories.append({
                'writer': history[i][0],
                'name': history[i][1],
                'publish_year': history[i][2],
                # 为了方便存储与传输，我将借书、还书时间由人类公元纪年法转化为unix时间戳
                'back_time': int(time.mktime( time.strptime(history[i][3]+' '+history[i][4], '%Y%m%d %H:%M'))),
                'real_back_time': int(time.mktime( time.strptime(history[i][5]+' '+history[i][6], '%Y%m%d %H:%M'))),
                'type': history[i][7]
            })

        return {'extend_url': extend_url, 'book_data': res, 'history': histories}

    # 获取考试成绩
    def get_grade(self, semester):
        # 如果没有登录教务处，尝试登录
        if self.aao_cookies==None:
            self.__aao_login()
        response = requests.get('http://219.216.96.4/eams/teach/grade/course/person!search.action?semesterId='+str(semester),
                                cookies=self.aao_cookies,
                                headers=self.__headers)
        hash_list = re.findall('<td.*?>([\s\S]*?)</td>', response.text)
        res = []
        # 初始化返回数据
        for i in range(0, int(len(hash_list)/11)):
            res.append({
                'semester': '',
                'course_code': '',
                'course_ord': '',
                'course_name': '',
                'course_type': '',
                'course_credit': '',
                'final_grade': '',
                'mid_grade': '',
                'class_grade': '',
                'sum_grade': '',
                'gp' : ''
            })
        # 你可能觉得这种做法很笨，但这获取并不比使用正则表达式慢，而且更容易理解
        # 返回的页面实在太难以阅读了 不方便写正则表达式
        for i in range(0, len(hash_list)):
            index = ''
            if i%11 == 0:
                index = 'semester'
            elif i%11 == 1:
                index = 'course_code'
            elif i%11 == 2:
                index = 'course_ord'
            elif i%11 == 3:
                index = 'course_name'
            elif i%11 == 4:
                index = 'course_type'
            elif i%11 == 5:
                index = 'course_credit'
            elif i%11 == 6:
                index = 'final_grade'
            elif i%11 == 7:
                index = 'mid_grade'
            elif i%11 == 8:
                index = 'class_grade'
            elif i%11 == 9:
                index = 'sum_grade'
            elif i%11 == 10:
                index = 'gp'
            # strip是为了过滤空白字符 如回车、空格、制表符
            res[int(i/11)][index] = hash_list[i].strip()
        return res

    # 获取课表以及课程信息
    def get_course(self, semester):
        # 如果还没有登录新教务处则登录
        if self.aao_cookies==None:
            self.__aao_login()
        post_data = {
            'ignoreHead': '1',
            'showPrintAndExport': '1',
            'setting.kind': 'std',
            'startWeek': '',
            'project.id': '1',
            'semester.id': semester,
            'ids': '46600'
        }

        table_headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Referer': 'http://219.216.96.4/eams/courseTableForStd.action', # 之所以要使用定制headers的原因就在这里
            # 经过测试，查课表页面会检测Referer，即页面来源。
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'Host': '219.216.96.4',
            'Origin': 'http://219.216.96.4',
        }

        course_data = requests.post("http://219.216.96.4/eams/courseTableForStd!courseTable.action", data=post_data, headers=table_headers, cookies=self.aao_cookies)
        teachers = re.findall('var teachers = \[{id:.*?,name:"(.*?)",lab:false}\];', course_data.text)
        course_names = re.findall('actTeacherName.join\(\',\'\),".*?","(.*?)"', course_data.text)
        course_classroom = re.findall('actTeacherName.join\(\',\'\),".*?",".*?",".*?","(.*?)"', course_data.text)
        course_weeks_str = re.findall('actTeacherName.join\(\',\'\),".*?",".*?",".*?",".*?","(.*?)"', course_data.text)
        course_class = re.findall('activity = new TaskActivity([\s\S]*?)var teachers', course_data.text)
        course_class = course_class + re.findall('activity = new TaskActivity([\s\S]*?)table0.marshalTable', course_data.text)
        course_info = re.findall('<td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>[\s\S]*?<a href=".*?" onclick=".*?" title="点击显示单个教学任务具体安排">.*?</a>[\s\S]*?</td><td>(.*?)</td><td>', course_data.text)

        for count in range(0, len(course_class)):
            day = re.findall('index =(\d+)\*unitCount\+\d+', course_class[count])
            class_num = re.findall('index =\d+\*unitCount\+(\d+)', course_class[count])
            this_course = []
            for cour in range(0, len(day)):
                this_course.append({'day': int(day[cour]), 'class_num': int(class_num[cour])})
            course_class[count] = this_course

        res = []
        info = []
        for i in range(0, len(teachers)):
            course = {
                'teacher': teachers[i],
                'name': course_names[i],
                'classroom': course_classroom[i],
                'weeks': self.__week_num(course_weeks_str[i]),
                'time': course_class[i]
            }
            res.append(course)

        for i in course_info:
            info.append({
                'course_code': i[0],
                'course_name': i[1],
                'course_score': i[2],
                'course_teacher': i[3]
            })

        return {'table': res, 'info': info}

    # 获取校园卡消费记录
    def get_card_trade(self, start, end):
        # 如果还没有通过一网通办获取到一卡通的cookies，则获取
        if self.card_cookies==False:
            self.__card_login()
        trade_url = 'http://ecard.neu.edu.cn/selfsearch/User/ConsumeInfo.aspx'
        page = 1
        res = []
        query_page = requests.get('http://ecard.neu.edu.cn/selfsearch/User/ConsumeInfo.aspx', cookies=self.card_cookies)
        while True:
            data = {
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$AspNetPager1',
                '__EVENTARGUMENT': str(page),
                '__VIEWSTATE':
                    re.findall('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE"[\s\S]*?value="(.*?)"',
                               query_page.text)[0],
                '__EVENTVALIDATION':
                    re.findall('<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="(.*?)" />',
                               query_page.text)[0],
                'ctl00$ContentPlaceHolder1$rbtnType': '0',
                'ctl00$ContentPlaceHolder1$txtStartDate': start,
                'ctl00$ContentPlaceHolder1$txtEndDate': end,
            }

            if page==1:
                data['ctl00$ContentPlaceHolder1$btnSearch'] = '查  询'
                data['__EVENTARGUMENT'] = ''

            query_page = requests.post(trade_url, data=data, cookies=self.card_cookies, headers=self.__headers)
            page_num = re.findall('style="margin-right:5px;">(\d+)</a>', query_page.text)
            trade_time = re.findall('<span id="Content.*?">(.*?)</span>', query_page.text)
            trades = re.findall(
                '</td><td>(.*?)</td><td align="right">(.*?)</td><td align="right">(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>',
                query_page.text)
            for i in range(0, len(trade_time)):
                if (trade_time[i] == ''):
                    break
                append_content = {
                    'trade_time': trade_time[i],
                    'trade_type': trades[i][0],
                    'trade_cost': trades[i][1],
                    'remaind': trades[i][2],
                    'salesman': trades[i][3],
                    'place': trades[i][4],
                    'terminal': trades[i][5]
                }
                #print(append_content)
                res.append(append_content)
            if 1-(str(page + 1) in page_num):
                break
            page += 1

        return res

    # 门禁记录，start与end格式为都如2019-05-18这样
    def get_door_info(self, start, end):
        # 如果还没有通过一网通办获取到一卡通的cookies，则获取
        if self.card_cookies==False:
            self.__card_login()
        #门禁记录请求界面
        requests_url = 'http://ecard.neu.edu.cn/selfsearch/User/DoorInfo.aspx'
        page = 1
        res = []
        query_page = requests.get(requests_url, cookies=self.card_cookies)

        while True:
            # data的参数是通过浏览器行为分析得出的
            data = {
                '__VIEWSTATE':
                    re.findall('<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE"[\s\S]*?value="(.*?)"',
                               query_page.text)[0],
                '__EVENTVALIDATION':
                    re.findall('<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="(.*?)" />',
                               query_page.text)[0],
                'ctl00$ContentPlaceHolder1$rbtnType': '2',
                'ctl00$ContentPlaceHolder1$txtStartDate': start,
                'ctl00$ContentPlaceHolder1$txtEndDate': end,
            }

            if page==1:
                data['ctl00$ContentPlaceHolder1$btnSearch'] = '查  询'
            else:
                data['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$AspNetPager1'
                data['__EVENTARGUMENT'] = str(page)

            query_page = requests.post(requests_url, data=data, cookies=self.card_cookies, headers=self.__headers)
            page_num = re.findall('style="margin-right:5px;">(\d+)</a><a class="aspnetpager"', query_page.text)
            records = re.findall(
                '<td>.*?</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td>',
                query_page.text)
            for i in range(0, len(records)):

                append_content = {
                    'time': records[i][0],
                    'place': records[i][1],
                    'io': records[i][2],
                    'result': records[i][3]
                }
                if append_content['time']=='&nbsp;':
                    break
                res.append(append_content)
            if 1-(str(page + 1) in page_num):
                break
            page += 1

        return res

    # 续借功能 目前由于样本不足，不能判断是否成功续借
    def library_continue_borrow(self, book_list):
        # 获取续借源链接
        extend_url = self.library_info['extend_url']
        # 生成续借请求链接
        for book in book_list:
            extend_url += ('&'+book+'=Y')
        response = requests.get(extend_url)
        response_text = str(response.content,'utf8')
        if len(re.findall('<td class=td1>不能再续借 \(还书日期没改变\)。</td> ',response_text))>0:
            return False
        else:
            return True

    # 待开发
    def lost_card(self):
        pass

    # 初始化
    def __init__(self, stu_id, pwd):
        self.id = str(stu_id)
        self.password = str(pwd)
        self.success = False
        self.pass_cookies = {'Language': 'zh_CN'}
        self.aao_cookies = None
        self.card_cookies = False
        # 登录一网通办 获取登录cookies 如果成功，success将改变为True，可以通过此参数确定账号密码是否正确以及是否完成验证
        self.__index_login()


