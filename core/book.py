from core.node import Node


def book_str(nodes: [Node]):
    book = []
    for node in nodes:
        book.append(node.msg.decode('utf-8'))
    return '\n'.join(book) + '\n'


def book_bytes(nodes: [Node]):
    book = []
    for node in nodes:
        book.append(node.msg)
    return b'\n'.join(book) + b'\n'


def book_iter(nodes: [Node], string=False):
    for node in nodes:
        yield (node.msg.decode('utf-8') + '\n') if string else (node.msg + b'\n')
