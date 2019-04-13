import requests
import re

login_url = "https://pass.neu.edu.cn/tpass/login"
login_post_url = "https://pass.neu.edu.cn/tpass/login"




def login(uid, pwd):
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

    login_post = requests.post(login_post_url, cookies=login_page.cookies, data=post_data)
    if len(login_post.history) != 0:
        return 1
    else:
        return 0