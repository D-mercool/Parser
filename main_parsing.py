import datetime

import dateparser
import requests
import pandas
from bs4 import BeautifulSoup
from typing import Tuple, List, Union


def get_page(url: str, proxies: str = '') -> Union[bool, BeautifulSoup]:
    """
    Принимает: url страницы
    Возвращает: Разметку

    :param proxies:
    :param url: str:
    :return BeautifulSoup():
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Mobile Safari/537.36'}
    if proxies != '':
        proxies = {"http": f'http://{proxies}', "https": f'https://{proxies}'}
    else:
        proxies = {}

    response = requests.get(url, headers=headers, proxies=proxies)
    if response.status_code == 200:
        print('Success!')
    elif response.status_code == 404:
        print('Not Found.')
        return False

    soup = BeautifulSoup(response.content, features='html.parser')
    return soup


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


if __name__ == '__main__':
    url = 'https://ria.ru/politics/'

    df_report = pandas.DataFrame()

    soup = get_page(url)
    if soup:  # Если получили данные страницы
        titles, infos, tags = get_data_ria(soup)

        for title, info, tag in zip(titles, infos, tags):
            df_report = df_report.append({'Название': title[0],
                                          'Ссылка': title[1],
                                          'Дата': info[0],
                                          'Просмотры': info[1],
                                          'Тэги': '|'.join(tag),
                                          },
                                         ignore_index=True)
        save_xlsx(df_report)
