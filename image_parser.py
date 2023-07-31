from html.parser import HTMLParser


class ImageSrcParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.img_src = []
        self.item_id = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for attr in attrs:
                if attr[0] == 'src':
                    self.img_src.append(attr[1])
                elif attr[0] == 'itemid':
                    self.item_id.append(attr[1])

    def clear(self):
        self.img_src.clear()
        self.item_id.clear()

    def replace_img_src(self, content, filename):
        for i in range(len(self.img_src)):
            content = content.replace(self.img_src[i], filename[i])
        return content
