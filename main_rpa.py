from fake_useragent import UserAgent
from selenium.webdriver import Chrome, ChromeOptions, Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from typing import Tuple, List
import datetime
import dateparser
import time
import random
import pandas


def get_driver(proxy: str, headless: bool) -> Chrome:
    """
    Конфигруация и настройка драйвера для поисковика (Google)

    :param proxy: str -> host:port:
    :param headless: bool:
    :return:
    """
    ua = UserAgent()
    user_agent = ua.random

    opts = ChromeOptions()
    opts.add_argument(f'user-agent={user_agent}')
    if proxy != '':
        opts.add_argument(f'--proxy-server={proxy}')
    if headless:
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
    else:
        opts.add_argument('--start-maximized')
    opts.add_argument('--allow-profiles-outside-user-dir')
    driver = Chrome(options=opts)

    return driver


def random_delay(start: int, end: int):
    """
    Функция делает рандомную задержку в диапазоне [start, end] секунды
    :param start: int:
    :param end: int:
    :return:
    """
    time.sleep(round(random.uniform(start, end), 2))


def save_xlsx(data: pandas.DataFrame):
    """
    Принимает: DataFrame()
    Сохраняет файл с названием report.xlsx

    :param data: DataFrame():
    :return:
    """
    if len(data) != 0:
        try:
            with pandas.ExcelWriter(f'report.xlsx') as writer:
                data.to_excel(writer)
                print(f'<*> Excel сформирован <*>')
        except:
            print(f'- Ошибка сохранения Excel')


def get_data_news_ria(soup: BeautifulSoup) -> Tuple[str, str, List[str], List[str]]:
    """
    Принимает: разметку (soup)
    Возвращает: Список названий, список информации и список тэгов новости

    :param soup: BeautifulSoup():
    :return title, text, info, tags:
    """
    title = soup.find('div', {'class': 'article__title'}).text
    text = '\n'.join([text.text for text in soup.find_all('div', {'class': 'article__text'})])
    tags = [tag.text for tag in soup.find_all('a', {'class': 'article__tags-item'})]

    date = soup.find('div', {'class': 'article__info-date'}).find('a').text
    date = datetime.datetime.strftime(dateparser.parse(date), '%d.%m.%Y %H:%M')
    views = soup.find('span', {'class': 'statistic__item'}).text
    info = [date, views]

    return title, text, info, tags


def get_data_ria(soup: BeautifulSoup) -> Tuple[List[List[str]], List[List[str]], List[List[str]]]:
    """
    Принимает: разметку (soup)
    Возвращает: Список названий, список информации и список тэгов новости

    :param soup: BeautifulSoup():
    :return titles, infos, tags:
    """
    titles = [[title.text, title.attrs['href']] for title in soup.find_all('a', {'class': 'list-item__title'})]
    infos = []
    tags = []

    tag_divs = soup.find_all('div', {'class': 'list-item__tags'})
    for tag_div in tag_divs:
        tags.append([tag.text for tag in tag_div.find('ul').find_all('a')])
    info_divs = soup.find_all('div', {'class': 'list-item__info'})
    for info_div in info_divs:
        date = info_div.find('div', {'class': 'list-item__date'}).text
        date = datetime.datetime.strftime(dateparser.parse(date), '%d.%m.%Y %H:%M')
        views = info_div.find('div', {'class': 'list-item__views-text'}).text
        infos.append([date, views])

    return titles, infos, tags


def get_200_news(driver):
    for i in range(9):  # Получаем 200 новостей
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if i == 0:
            btn = driver.find_element(By.CLASS_NAME, 'list-more')
            btn.click()
        random_delay(2, 4)


def main(driver) -> pandas.DataFrame:
    """
    Получение списка новостей с одной страницы

    :param driver: selenium.webdriwer.Chrome():
    :return pandas.DataFrame():
    """
    df_report = pandas.DataFrame()

    soup = BeautifulSoup(driver.page_source, features='html.parser')
    if soup:  # Если получили данные страницы
        titles, infos, tags = get_data_ria(soup)

        for title, info, tag in zip(titles, infos, tags):
            df_report = df_report.append({'Название': title[0],
                                          'Ссылка': title[1],
                                          'Дата': info[0],
                                          'Просмотры': info[1],
                                          'Тэги': '|'.join(tag)},
                                         ignore_index=True)
    return df_report


def main_pagination(driver) -> pandas.DataFrame:
    """
    Получение каждой новости по отдельности с текстом этой новости.
    Обход каждой страницы с новостью

    :param driver: selenium.webdriwer.Chrome():
    :return: pandas.DataFrame():
    """
    df_report = pandas.DataFrame()

    hrefs = driver.find_elements(By.CLASS_NAME, 'list-item__title')
    for i in range(len(hrefs)):
        random_delay(2, 3)
        href = hrefs[i].get_attribute('href')
        hrefs[i].send_keys(Keys.CONTROL + Keys.SHIFT + Keys.RETURN)
        random_delay(1, 3)
        driver.switch_to.window(driver.window_handles[1])
        soup = BeautifulSoup(driver.page_source, features='html.parser')
        title, text, info, tags = get_data_news_ria(soup)
        df_report = df_report.append({'Название': title,
                                      'Ссылка': href,
                                      'Дата': info[0],
                                      'Просмотры': info[1],
                                      'Тэги': '|'.join(tags),
                                      'Текст новости': text},
                                     ignore_index=True)
        random_delay(2, 3)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    return df_report


if __name__ == '__main__':
    url = 'https://ria.ru/politics/'
    proxies = ''

    driver = get_driver(proxy=proxies, headless=False)  # Если headless=False, безголовный режим выключен

    driver.get(url)
    random_delay(2, 5)
    get_200_news(driver)

    df_report = main(driver)  # Получение списка новостей с одной страницы
    # df_report = main_pagination(driver)

    save_xlsx(df_report)
