import json

from more_itertools import chunked

from livereload import Server

from jinja2 import Environment, FileSystemLoader, select_autoescape


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')
    with open('parsed_book.json', 'r') as my_file:
        parsed_books_json = my_file.read()

    parsed_books = json.loads(parsed_books_json)
    rendered_page = template.render(
        parsed_books=list(chunked(parsed_books, 2))
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


on_reload()

server = Server()
server.watch('template.html', on_reload)
server.serve(root='.')


