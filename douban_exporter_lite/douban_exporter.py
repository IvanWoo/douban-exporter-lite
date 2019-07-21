import sys
import requests
import os

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter


class DoubanExport(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.sheet_types = ["collect", "do", "wish"]

        r = requests.get(
            f"https://movie.douban.com/people/{self.user_id}/collect")
        self.cookies = r.cookies

    def map_chinese_sheet_name(self, english_sheet_name):
        category_dictionary = {
            "music": "音乐",
            "movie": "电影",
            "book": "书",
        }
        keyword_dictionary = {
            "music": "听",
            "movie": "看",
            "book": "读",
        }
        category = category_dictionary.get(self.category)
        keyword = keyword_dictionary.get(self.category)
        translator = {
            "collect": f"{keyword}过的{category}",
            "do": f"在{keyword}的{category}",
            "wish": f"想{keyword}的{category}",
        }
        return translator.get(english_sheet_name, "invalid sheet name")

    def initial_sheet(self, sheet_type, workbook, global_format, heading_format):
        pass

    def initial_xlsx(self):
        workbook = xlsxwriter.Workbook(
            self.file_name, {'constant_memory': True})

        heading_format = workbook.add_format(
            {'bold': True, 'font_name': 'PingFang SC', 'font_size': 11})
        global_format = workbook.add_format(
            {'font_name': 'PingFang SC', 'font_size': 11})

        # initial 3 sheets
        for sheet_type in self.sheet_types:
            self.initial_sheet(sheet_type, workbook,
                               global_format, heading_format)

        workbook.close()

    def get_rating(self, rating_class):
        """
        :param rating_class: string
        :return: int
        example: "rating1-t" => 1
                 "rating2-t" => 2
        """
        return int(rating_class[6])

    def export(self, url):
        pass

    def get_max_index(self, sheet_type):
        url = f"https://{self.category}.douban.com/people/{self.user_id}/{sheet_type}"
        r = requests.get(url, cookies=self.cookies)
        soup = BeautifulSoup(r.text, "lxml")

        paginator = soup.find("div", {"class": "paginator"})
        if paginator is not None:
            max_index = paginator.find_all("a")[-2].get_text()
        else:
            max_index = 1

        return int(max_index)

    def url_generator(self, sheet_type):
        max_index = self.get_max_index(sheet_type)
        for index in range(0, max_index * 15, 15):
            yield f"https://{self.category}.douban.com/people/{self.user_id}/{sheet_type}" \
                  f"?start={index}&sort=time&rating=all&filter=all&mode=grid"

    # TODO: refactor the data structure of infos into a dictionary rather than relying on the position of list
    def write_to_xlsx(self, infos, row, sheet_type):
        wb = xw.Book(self.file_name)
        sht = wb.sheets[self.map_chinese_sheet_name(sheet_type)]
        if sheet_type == "collect" or sheet_type == "do":
            for index, info in enumerate(infos):
                tagA = 'A' + str(row + index)
                sht.range(tagA).add_hyperlink(
                    info[-1], text_to_display=info[0], screen_tip=None)
                tagB = 'B' + str(row + index)
                sht.range(tagB).value = info[1: len(info) - 1]
        else:
            for index, info in enumerate(infos):
                tagA = 'A' + str(row + index)
                sht.range(tagA).add_hyperlink(
                    info[-1], text_to_display=info[0], screen_tip=None)
                tagB = 'B' + str(row + index)
                # no rating for 想读/听/看
                sht.range(tagB).value = info[1:5] + info[6:8]
        wb.save()

    def start_task(self):
        if not os.path.exists(self.file_name):
            self.initial_xlsx()

        for sheet_type in self.sheet_types:
            print(f'{sheet_type} sheet started!')
            urls = self.url_generator(sheet_type)

            counter = 0
            row = 2
            for url in urls:
                info = self.export(url)
                try:
                    self.write_to_xlsx(info, row + 15 * counter, sheet_type)
                except TypeError:
                    continue
                counter += 1
            print(f'{sheet_type} sheet finished!')
