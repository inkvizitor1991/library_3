import argparse
import json
import logging
import os
import pathlib
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def get_last_page():
    url = 'https://tululu.org/l55/'
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    selector = '.npage:last-child'
    last_page = int(soup.select_one(selector).text)
    return last_page


def parse_book_page(soup, books_path, images_path, filename, book_id,
                    basic_image_url):
    comments_selector = '.texts .black'
    comments = soup.select(comments_selector)

    genres_selector = 'span.d_book a'
    links_genre = soup.select(genres_selector)

    title_with_author_selector = 'body h1'
    title_with_author = soup.select_one(title_with_author_selector)
    title, author = title_with_author.text.split('::')

    pathlib.Path(books_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(images_path).mkdir(parents=True, exist_ok=True)
    img_scr = os.path.join(images_path, f'{book_id}_{filename}')
    book_path = os.path.join(books_path, f'{book_id}_{title.strip()}.txt')
    parsed_book = {
        'title': title.strip(),
        'author': author.strip(),
        'img_scr': img_scr,
        'basic_image_url': basic_image_url,
        'genres': [tag.text for tag in links_genre],
        'book_path': book_path,
        'comments': [tag.text for tag in comments],
    }
    return parsed_book


def download_txt(parsed_book, book_id):
    book_id = {'id': book_id}
    download_url = 'https://tululu.org/txt.php'
    download_url_response = requests.get(download_url, params=book_id)
    check_for_redirect(download_url_response)
    response.raise_for_status()

    filepath = parsed_book['book_path']
    with open(filepath, 'w') as file:
        file.write(download_url_response.text)


def download_image(parsed_book, basic_image_url):
    image_url = parsed_book['img_scr']
    response = requests.get(basic_image_url)
    response.raise_for_status()

    with open(image_url, 'wb') as file:
        file.write(response.content)


def download_description_book(parsed_book, json_path):
    with open(json_path, 'w', encoding='utf8') as description_book:
        json.dump(parsed_book, description_book, ensure_ascii=False)


def download_book(soup, book_url, books_path, images_path, args):
    relative_image_url_selector = '.bookimage a img'
    relative_image_url = soup.select_one(relative_image_url_selector)['src']
    parse_image_url = urlsplit(relative_image_url)
    image_id = os.path.split(parse_image_url.path)[-1]
    filename = unquote(image_id)
    book_id, _ = os.path.splitext(image_id)

    basic_image_url = urljoin(book_url, relative_image_url)

    parsed_book = parse_book_page(
        soup, books_path,
        images_path, filename,
        book_id, basic_image_url
    )

    if not args.skip_txt:
        download_txt(parsed_book, book_id)
    if not args.skip_imgs:
        download_image(parsed_book, basic_image_url)
    return parsed_book


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--start_page', nargs='?',
        type=int, default=0,
        help='С какой страницы скачать'
    )
    parser.add_argument(
        '--end_page', nargs='?',
        type=int, default=get_last_page(),
        help='С какой по какую страницы скачать'
    )
    parser.add_argument(
        '--dest_folder',
        help='Путь к каталогу с результатами парсинга: картинкам, книгам, JSON.',
        default=os.path.abspath(os.curdir)
    )
    parser.add_argument(
        '--skip_txt',
        action='store_true',
        help='Не скачивать книги.'
    )
    parser.add_argument(
        '--skip_imgs',
        action='store_true',
        help='Не скачивать картинки.'
    )
    parser.add_argument(
        '--json_path',
        help='Указать свой путь к *.json файлу с результатами.',
        default='parsed_book.json'
    )
    return parser


if __name__ == '__main__':
    logging.basicConfig(
        filename='log.txt', filemode='a',
        level=logging.DEBUG
    )
    books_folder = 'books'
    images_folder = 'images'

    parser = get_parser()
    args = parser.parse_args()

    books_path = Path(args.dest_folder, books_folder)
    images_path = Path(args.dest_folder, images_folder)
    json_path = Path(args.dest_folder, args.json_path)

    start_page = args.start_page
    end_page = args.end_page

    book_description = []
    for page_number in range(start_page, end_page):
        url = f'https://tululu.org/l55/{page_number}/'
        response = requests.get(url)
        check_for_redirect(response)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        selector = '.bookimage a'
        books = soup.select(selector)

        for book in books:
            try:
                book_id = book['href']
                book_url = urljoin(url, book_id)
                response = requests.get(book_url)
                check_for_redirect(response)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')
                parsed_book = download_book(
                    soup, book_url,
                    books_path, images_path,
                    args,
                )
                book_description.append(parsed_book)

            except requests.HTTPError:
                logging.error('Произошла ошибка при скачивании.')

    download_description_book(book_description, json_path)
