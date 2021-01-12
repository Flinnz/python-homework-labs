import time
import re
import logging
import urllib.request
import json
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG, filename='debug.log', format='[%(asctime)s] %(levelname)s:%(message)s')

base_url = 'https://www.imdb.com'

DETAIL_BLOCKS = [
    'Details', 'Box Office', 'Technical Specs'
]

TITLE_TYPES = [
    'Feature Film', 'TV Movie', 'TV Series', 'TV Episode',
    'TV Special', 'Mini-Series', 'Documentary', 'Video Game',
    'Short', 'Video', 'TV Short'
]


def get_html(url):
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request) as f:
            html = f.read().decode('utf-8')
            logging.info(f"Successfully loaded page from {url}")
            return html
    except Exception as exception:
        logging.error(f"Page loading failed: {exception}")


def checked_list(*args):
    flag = True
    result = []
    for arg in args:
        if arg is None:
            result.append('')
        else:
            flag = False
            result.append(str(arg))
    return [] if flag else result


def get_title_type(title_bar):
    for title_type in TITLE_TYPES:
        if title_type in title_bar:
            return title_type
    return 'Feature Film'


def get_checked_arguments(title_types=None,
                          release_date_from=None,
                          release_date_to=None,
                          user_rating_from=None,
                          user_rating_to=None,
                          genres=None,
                          countries=None):
    args = {}

    if title_types is not None and len(title_types) > 0:
        args['title_type'] = ','.join(title_types)

    if genres is not None and len(genres) > 0:
        args['genres'] = ','.join(genres)

    if countries is not None and len(countries) > 0:
        args['countries'] = ','.join(countries)

    release_date = checked_list(release_date_from, release_date_to)
    if len(release_date) > 0:
        args['release_date'] = ','.join(release_date)

    user_rating = checked_list(user_rating_from, user_rating_to)
    if len(user_rating) > 0:
        args['user_rating'] = ','.join(user_rating)

    return args


def build_args_url(args):
    return base_url + '/search/title/?' + '&'.join([key + '=' + value for key, value in args.items()])


def get_movie_info_from_page(html_page):
    soup = BeautifulSoup(html_page, 'html.parser')
    title_bar_div = soup.find('div', class_='title_bar_wrapper')
    title_info = {}
    if title_bar_div is not None:
        rating_span = title_bar_div.find('span', attrs={"itemprop": "ratingValue"})
        if rating_span is not None:
            rating = rating_span.text
            title_info['rating'] = rating
        else:
            logging.info('title rating not found')
        title_div = title_bar_div.find('div', class_='titleBar')
        name_h1 = title_div.find('h1')
        if name_h1 is not None:
            if name_h1.span is not None:
                name_h1.span.decompose()
            name = name_h1.text.replace('\xa0 ', '').strip()
            title_info['name'] = name
        else:
            logging.info('title name not found')
        subtext_div = title_div.find('div', class_='subtext')
        if subtext_div is not None:
            subtext = subtext_div.text
            title_type = get_title_type(subtext)
            title_info['title_type'] = title_type
        else:
            logging.info('title type not found')
    else:
        logging.info('title name, title type and rating not found')
    plot_summary_div = soup.find('div', class_='plot_summary')
    if plot_summary_div is not None:
        stars_h4 = plot_summary_div.find('h4', text='Stars:')
        if stars_h4 is not None:
            stars = [star.text for star in stars_h4.parent.find_all('a')]
            del stars[-1]
            title_info['stars'] = stars
    if 'stars' not in title_info:
        logging.info('stars not found')

    title_story_line_div = soup.find('div', id='titleStoryLine')
    if title_story_line_div is not None:
        genres_h4 = title_story_line_div.find('h4', text='Genres:')
        if genres_h4 is not None:
            genres = [star.text.strip() for star in genres_h4.parent.find_all('a')]
            title_info['genres'] = genres
    if 'genres' not in title_info:
        logging.info('genres not found')

    details_div = soup.find('div', id='titleDetails')
    if details_div is not None:
        current_key = 'details'
        needed_block = True
        for child in details_div.children:
            if child.name == 'h3' or child.name == 'h2':
                current_key = child.text.strip()
                needed_block = current_key in DETAIL_BLOCKS
                if needed_block:
                    title_info[current_key] = {}
            if child.name == 'div' and 'txt-block' in child['class'] and needed_block:
                h4 = child.find('h4')
                if h4 is not None:
                    sub_key = h4.text.replace(':', '')
                    child.h4.decompose()
                    children_text = [txt.strip() for txt in child.text.replace('See more\xa0»', '').strip().split('|')]
                    title_info[current_key][sub_key] = children_text if len(children_text) > 1 else children_text[0]
    else:
        logging.info('details not found')
    logging.info(f'title info found')
    print(title_info)
    return title_info


def scrape_movies(title_types=None,
                  release_date_from=None,
                  release_date_to=None,
                  user_rating_from=None,
                  user_rating_to=None,
                  genres=None,
                  countries=None,
                  max_count=1000):  # TODO: Threading было бы круто) и дату проверять)
    args = get_checked_arguments(title_types,
                                 release_date_from,
                                 release_date_to,
                                 user_rating_from,
                                 user_rating_to,
                                 genres,
                                 countries)
    if len(args) <= 0:
        logging.error('At least one argument should be provided')
        return {}
    logging.info(f'Provided arguments: {args}')
    args_url = build_args_url(args)
    base_search_url = args_url + '&view=simple&count=250'
    total_title_count = 0
    title_pages = []
    while total_title_count < max_count:
        search_url = base_search_url + f'&start={total_title_count + 1}'
        print(search_url)
        html_doc = get_html(search_url)
        soup = BeautifulSoup(html_doc, 'html.parser')
        titles = {*[link.find('a', href=True).get('href') for link in soup.select('div.lister-item.mode-simple')]}
        if len(titles) == 0:
            break
        print(len(titles))
        title_pages.extend([get_movie_info_from_page(get_html(base_url + title)) for title in titles])
        total_title_count += len(titles)
    return title_pages


def main():
    start_time = time.perf_counter()
    logging.info(f'Scrape Started')
    result = scrape_movies(title_types=[],
                           release_date_from='2019-02-11',
                           release_date_to='2020-12-31',
                           user_rating_from=2.2,
                           user_rating_to=10.0,
                           genres=['comedy'],
                           countries=['us'])
    logging.info(f'total titles: {len(result)}')
    try:
        with open('titles.json', 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, ensure_ascii=False)
            logging.info('json file was created')
    except Exception as exception:
        logging.error(f"json file wasn't created {exception}")
    end_time = time.perf_counter()
    logging.info(f'Total working time: {end_time - start_time}')


if __name__ == '__main__':
    main()
