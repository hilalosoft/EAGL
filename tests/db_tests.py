import unittest

import psycopg2
from sshtunnel import SSHTunnelForwarder

from Classes import DOM_class
from Classes.DOM_class import DOMClass




class DOMClassTestCase(unittest.TestCase):
    def test_class_constructor(self):
        obj_dom = DOMClass('https://web.archive.org/web/19990202114421/http://www.lamonitor.com:80', 123918293769,
                           'test1')
        obj_dom1 = DOMClass('https://timetravel.mementoweb.org/133918293769/link/', 133918293769, 'test2')
        obj_dom2 = DOMClass('https://timetravel.mementoweb.org/139918293769/link/', 133918293769, 'test2')
        DOM_class.add_dom(obj_dom)
        DOM_class.add_dom(obj_dom1)
        DOM_class.add_dom(obj_dom2)
        self.assertEqual(obj_dom.previous_dom, None)
        self.assertEqual(obj_dom.next_dom, obj_dom1.dom_id)
        self.assertEqual(obj_dom1.next_dom, obj_dom2.dom_id)
        self.assertEqual(obj_dom1.previous_dom, obj_dom.dom_id)
        self.assertEqual(obj_dom2.previous_dom, obj_dom1.dom_id)
        self.assertEqual(obj_dom2.next_dom, None)

    # def test_class_contructor(self):
    #     version = "https://web.archive.org/web/19990202114421/http://www.lamonitor.com:80;asdasd ; datetime=\"Sun, " \
    #               "02 Feb 1999 11:44:21 GMT \" "
    #     request_and_save_page(version, "https://web.archive.org/web/19990202114421/http://www.lamonitor.com:80")
    #     self.assertIsNotNone(DOM_class.get_dom_dict()['None_19990202114421'])
    def test_online_db(self):
        # get_progress()
        with SSHTunnelForwarder(
                ('dompm', 22),
                ssh_password="th123hil",
                ssh_username="hilaltaha",
                remote_bind_address=('127.0.0.1', 5432)) as server:
            # params = config_db()
            # Connect to your postgres DB
            conn = psycopg2.connect("dbname=dom user=postgres password=th123hil",port=server.local_bind_port)

            # Open a cursor to perform database operations
            cur = conn.cursor()

            # Execute a query
            cur.execute("select * from dom where project='Microsoft'")

        # Retrieve query results
        records = cur.fetchall()
        print(records)

if __name__ == '__main__':
    unittest.main()
