import json
import pathlib

from more_itertools import chunked

from livereload import Server

from jinja2 import Environment, FileSystemLoader, select_autoescape


def on_reload():
    pages_folder = 'pages'

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')
    with open('parsed_book.json', 'r') as my_file:
        parsed_books_json = my_file.read()

    parsed_bookss = json.loads(parsed_books_json)

    for number, parsed_books in enumerate(list(chunked(parsed_bookss, 10)), 1):
        rendered_page = template.render(
            parsed_books=list(chunked(parsed_books, 2))
        )
        pathlib.Path(pages_folder).mkdir(parents=True, exist_ok=True)
        with open(f'pages/index{number}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)


on_reload()

server = Server()
server.watch('template.html', on_reload)
server.serve(root='.')


