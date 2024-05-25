import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from pyquery import PyQuery as pq
import requests
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


# Set up Chrome WebDriver options
chrome_options = ChromeOptions()
# 初始化 Chrome 驱动
driver = webdriver.Chrome(options=chrome_options)


def get_page(url='https://www.zhihu.com/hot'):

    driver.get(url=url)

    # Wait for dynamic content to load
    # Adjust this delay based on your network speed
    time.sleep(random.uniform(1, 3))

    # Scroll down to load dynamic content
    scroll_pause_time = 0.5  # Adjust the pause time as needed
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html = driver.page_source

    return html


def parse_html(drive):
    # 提取信息

    html = get_page()
    doc = pq(html)
    HotItem = doc('.HotItem')

    titles_text = []
    contents_text = []
    answers_list = []
    # comments_list = []
    for item in HotItem.items():
        title = item.find('.HotItem-title')
        content = item.find('.HotItem-excerpt')

        titles_text.append(title.text() if title else 'None')
        contents_text.append(content.text() if content else 'None')
        answers = parse_answer(item, drive)
        answers_list.append(answers)
        # comments_list.append(comments)
        print('message collected!')

    print("信息提取完成...")
    return titles_text, contents_text, answers_list  # comments_list


def parse_answer(HotItem, drive):
    print('start to parse answer')
    a_link = HotItem.find('a')
    url = a_link.attr['href']
    a_url_html = get_page(url)
    a_url_doc = pq(a_url_html)
    # comment_lists = parse_comment(drive, a_url_doc)
    answers = []
    answers_inner = a_url_doc.find(
        '.RichContent-inner')
    answers_item = answers_inner.find('p')
    for answer in answers_item.items():

        answers.append(answer.text())

    print('stop to parse answer')
    return answers  # comment_lists


def parse_comment(drive, a_url_doc):
    print('start to parse comment')
    zi_comment_button = drive.find_element(
        By.CLASS_NAME, "Zi--Comment")
    print(zi_comment_button)
    actions = ActionChains(driver)
    actions.move_to_element(zi_comment_button).click().perform()
    comment_lists = []
    comment_container = a_url_doc.find('.css-1frn93x')
    comment_contents = comment_container.find('.CommentContent')
    for content in comment_contents:
        comment_lists.append(content)
    print(comment_lists)
    print('stop parse comment')
    return comment_lists


def write_to_file(titles_text, contents_text, answers_list):
    # 将信息保存到json文件中
    data = []
    for i in range(len(titles_text)):
        item = {
            'title': titles_text[i],
            'content': contents_text[i],
            'answers': answers_list[i],
        }
        data.append(item)

    with open('title_content.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("信息已保存...")


if __name__ == '__main__':
    print('Start execute')
    titles, contents, answers = parse_html(driver)
    write_to_file(titles, contents, answers)
