from collections import OrderedDict
from requests_html import HTMLSession, HTML
import click

import progressbar


def key_interrupt(func):
    """
    decorator for exception handling
    ===============================
    TODO
    ====
        Add other exceptions 
    """
    def wrapper(*a, **k):
        try:
            func(*a, **k)
        except KeyboardInterrupt:

            click.clear()
    return wrapper
#===========================def func======================================================


headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"}
session = HTMLSession()


@click.command(help="<< not less than 3 characters >> book title or author name ")
@click.argument('query_item', type=str)
@key_interrupt
def main(query_item):

    if len(query_item) < 3:
        click.secho("ATTENTION: Please the search query must be > 3 chrs",
                    bold=True, fg='red', bg='black')
        q = click.prompt("Again: ")
    else:
        q = query_item
        click.secho(f"YOUR REQUEST : {q}", fg='blue')
    result = search(q)
    if result:
        print_result(result)
        download(result)
        click.clear()


def search(q):
    """Get Ids values from the table"""

    # search url
    info = """
              ============================================
              =            Getting Books                 =
              ============================================"""
    print(info)
    url = "http://libgen.io/search.php?open=0&res=99&view=simple&phrase=1&column=def"
    r = session.get(url, params={'req': q})  # get the result page
    html = HTML(html=r.content, url='bunk', default_encoding='utf-8')

    # The result table has rows and columns:
    # we need to extract each row then select the ID column of each row
    table = html.find('.c')[0]  # extract the table element

    trs = table.find('tr')[1:]  # Get trs(rows) elements starting for the row below items row.
    # now: Get the data of each tr(row): ID, Author, BOOk_title and publisher.. etc
    tds = (tr.find('td') for tr in trs)
    ids = (cols[0].text for cols in tds)  # Get id column of each row

    try:
        if next(ids):
            ids = ",".join([ID for ID in ids])
            url = 'http://libgen.io/json.php?fields=title,author,md5,edition,id,year,filesize,extension'
            req = session.get(url=url, params={'ids': ids})
            json_resp = req.json()
            return json_resp

    except StopIteration:
        info = """
              ============================================
              =            Book not found  :(            =
              ============================================"""
        print(info)
        try_agian = input('> Do you want to try again?[Y | N] > ')
        if try_agian in 'yY':
            q = input(">>")
            result = search(q)
            if result:
                print_result(result)
                download(result)
                click.clear()
        else:
            return


def print_result(result):
    """Get detailed book view : Book title,author,id, md5 and edition"""
    info = """
              ============================================
              =            CHOOSE BOOK(S)                =
              ============================================"""
    print(info)
    count_id = 0

    for book in result:
        book['filesize'] = str(
            round(int(book['filesize']) / (1024 * 1024), 1)) + ' Mb'
        book['serial_No'] = str(count_id)

        # Dictionary with ordered keys
        main_dict = OrderedDict()
        global book_title_real
        main_dict['Title'] = book['title']
        book_title_real = main_dict['Title']
        main_dict['Author'] = book['author']
        main_dict['edition'] = book['edition']
        main_dict['Extension'] = book['extension']
        main_dict['filesize'] = book['filesize']
        main_dict['year'] = book['year']
        main_dict['id'] = book['id']
        main_dict['MD5'] = book['md5']
        main_dict['serial_No'] = str(count_id)

        click.secho('-----***------')
        # click.secho(colorify_output(count_id, COLOR='yellow', on_COLOR='on_grey'))
        click.secho(f"{count_id}", fg='red', bg='white', bold=True)
        click.secho('-----***------')
        for pos, (key, value) in enumerate(main_dict.items()):
            click.secho(f"{key}\t\t{value}", fg='green')
        count_id += 1


def download(json_resp):
    """
    Downloading the file
    """
    click.secho('==================================================', fg='red')
    click.secho("Enter the id , if more than one book separate each id by space", fg='red')
    id = input(">>")
    id_parser = id.split(' ')

    for book in json_resp:
        for id in id_parser:
            if id == book["serial_No"]:
                click.secho(f"You chose the following Book ==> {book['title']}", fg='green')
                click.secho('Please wait,we are downloading your Book...', fg='green')

                # url = f"http://libgen.io/get.php?md5={book['md5']}"  # slow nowadays

                url_2 = f"http://lib1.org/_ads/{book['md5']}"  # fast

                # another navigation to get the download page
                #url_3 = f"https://libgen.pw/item/detail/id/{book['id']}"
                req = session.get(url_2, headers=headers)
                html = HTML(html=req.content, url='bunk', default_encoding='utf-8')
                dl_a_element = html.find('a')[0].absolute_links.pop()
                click.secho("That's your link: %s" % dl_a_element)

                with open(book_title_real, 'wb') as f:
                    req = session.get(dl_a_element, stream=True)
                    file_size = int(req.headers['Content-Length'])
                    chunk = 1
                    num_bars = file_size / chunk
                    bar = progressbar.ProgressBar(maxval=num_bars).start()
                    i = 0
                    for chunk in req.iter_content():
                        f.write(chunk)
                        bar.update(i)
                        i += 1
                    f.close()

                click.secho('\nFinished', blink=True)


if __name__ == "__main__":
    main()
