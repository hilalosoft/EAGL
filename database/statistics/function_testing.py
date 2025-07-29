import unittest

from bs4 import BeautifulSoup

from Classes.soup_operations import  cal_depth, get_siblings_soup, \
    generate_vectors_for_attr, generate_vectors_from_soup, xpath_soup, find_element_by_xpath_soup, \
    element_changed


class dataTestCase(unittest.TestCase):
    def test_cal_depth(self):
        html_doc = """
                <html><head><title>The Dormouse's story</title></head>
                <body>
                <p class="title"><b>The Dormouse's story</b></p>

                <p class="story">Once upon a time there were three little sisters; and their names were
                <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                and they lived at the bottom of a well.</p>

                <p class="story">...</p>
                </body>
                </html>
                """
        parsed_dom = BeautifulSoup(html_doc, 'html.parser')
        depth = cal_depth(parsed_dom.a, 5)
        self.assertEqual(depth, 4 / 5)  # add assertion here

    def test_siblings_soup(self):
        html_doc = """
                        <html><head><title>The Dormouse's story</title></head>
                        <body>
                        <p class="title"><b>The Dormouse's story</b></p>

                        <p class="story">Once upon a time there were three little sisters; and their names were
                        <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                        <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                        <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                        and they lived at the bottom of a well.</p>

                        <p class="story">...</p>
                        </body>
                        </html>
                        """
        parsed_dom = BeautifulSoup(html_doc, 'html.parser')
        position, siblings_list = get_siblings_soup(parsed_dom.body.a)
        siblings_dictionary = {"id": 0, "string": 0, "ul": 0, "li": 0, "h1": 0, "h2": 0, "h3": 0, "h4": 0,
                               "h5": 0,
                               "div": 0
            , "span": 0, "form": 0, "input": 0, "p": 0, "img": 0, 'a': 2 / 7, "dl": 0, "dt": 0, "dd": 0, "svg": 0,
                               "path": 0, "g": 0
            , "option": 0, "i": 0, "attribute": 0, "button": 0, "class": 0, "href": 0}
        self.assertEqual(siblings_list, siblings_dictionary)  # add assertion here
        self.assertEqual(position, 2 / 7)  # add assertion here

    # def test_xpath_soup(self):
    #     self.assertEqual(True, False)  # add assertion here

    # def test_generate_vectors_for_attr(self):
    #     html_doc = """
    #                 <html><head><title>The Dormouse's story</title></head>
    #                 <body>
    #                 <p class="title"><b>The Dormouse's story</b></p>
    #
    #                 <p class="story">Once upon a time there were three little sisters; and their names were
    #                 <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
    #                 <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
    #                 <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
    #                 and they lived at the bottom of a well.</p>
    #
    #                 <p class="story">...</p>
    #                 </body>
    #                 </html>
    #                 """
    #     parsed_dom = BeautifulSoup(html_doc, 'html.parser')
    #
    #     vectors = generate_vector_from_soup(parsed_dom.body.a, 5)
    #     # vectors = generate_vectors_for_attr(parsed_dom.body.a)
    #     self.assertEqual(True, False)  # add assertion here

    # def test_element_changed(self):
    #     html_doc = """
    #                 <html><head><title>The Dormouse's story</title></head>
    #                 <body>
    #                 <p class="title"><b>The Dormouse's story</b></p>
    #
    #                 <p class="story">Once upon a time there were three little sisters; and their names were
    #                 <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
    #                 <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
    #                 <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
    #                 and they lived at the bottom of a well.</p>
    #
    #                 <p class="story">...</p>
    #                 </body>
    #                 </html>
    #                 """
    #     parsed_dom = BeautifulSoup(html_doc, 'html.parser')
    #     xpath = xpath_soup(parsed_dom.a)
    #     DO = DriverObject()
    #     DO.get_page(html_doc)
    #     changed = DO.element_changed(xpath, parsed_dom.a)
    #     # changed = element_changed(xpath, parsed_dom.a, parsed_dom2)
    #
    #     self.assertEqual(changed, False)  # add assertion here

    def test_find_element_by_xpath_soup(self):
        html_doc = """
                    <html><head><title>The Dormouse's story</title></head>
                    <body>
                    <p class="title"><b>The Dormouse's story</b></p>

                    <p class="story">Once upon a time there were three little sisters; and their names were
                    <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
                    <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                    <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                    and they lived at the bottom of a well.</p>

                    <p class="story">...</p>
                    </body>
                    </html>
                    """

        html_doc2 = """
                        <html><head><title>The Dormouse's story</title></head>
                        <body>
                        <p class="title"><b>The Dormouse's story</b></p>

                        <p class="story">Once upon a time there were three little sisters; and their names were
                        <a href="http://example.com/elsiea" class="sister" id="link1">Elsiea</a>,
                        <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
                        <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
                        and they lived at the bottom of a well.</p>

                        <p class="story">...</p>
                        </body>
                        </html>
                        """
        parsed_dom = BeautifulSoup(html_doc, 'html.parser')
        parsed_dom2 = BeautifulSoup(html_doc2, 'html.parser')
        xpath = xpath_soup(parsed_dom.a)
        changed = element_changed(parsed_dom2, xpath, parsed_dom.a, attribute=None, text_content="Elsie")
        changed2 = element_changed(parsed_dom2, xpath, parsed_dom.a, attribute="href", text_content="http://example"
                                                                                                    ".com/elsie")

        self.assertEqual(changed, True)  # add assertion here
        self.assertEqual(changed2, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
