import lz4.frame


def add_dom(dom_object):
    if DOMClass.previous_dom is None:
        DOMClass.previous_dom = dom_object.dom_id
        # DOM_dict = {}
    else:
        DOMClass.DOM_list[DOMClass.count - 1].next_dom = dom_object.dom_id
        dom_object.previous_dom = DOMClass.previous_dom
        DOMClass.previous_dom = dom_object.dom_id
    DOMClass.count = DOMClass.count + 1
    DOMClass.DOM_list.append(dom_object)


def set_project(project_name):
    DOMClass.previous_dom = None
    DOMClass.count = 0
    DOMClass.DOM_list = []
    DOMClass.current_project = project_name


def get_dom_list():
    return DOMClass.DOM_list


def lz4_compress(dom):
    dom_bytes = bytes(dom, 'utf8')
    return str(lz4.frame.compress(dom_bytes))


def process_dom_string(dom):
    # final_dom = ""
    # for character in dom:
    #     final_dom = final_dom.join(str(ord(character)))
    return lz4_compress(dom)


class DOMClass:
    DOM_list = []
    count = 0
    current_project = None
    previous_dom = None
    current_timestamp = 0

    def __init__(self, url, timestamp, dom):
        self.dom_id = str(DOMClass.current_project) + "_" + str(timestamp)
        self.dom = dom
        self.url = url
        self.time = timestamp
        DOMClass.current_timestamp = timestamp
        self.project = DOMClass.current_project
        self.next_dom = None
        self.previous_dom = DOMClass.previous_dom


def remove_special_characters(character):
    if character.isascii() or character == ' ':
        return True
    else:
        return False
