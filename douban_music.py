import requests

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter


class MusicSheet(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.sheet_types = ["collect", "do", "wish"]
        self.file_name = self.user_id + " " + datetime.now().strftime("%Y-%m-%d") + ".xlsx"

    def __map_chinese_sheet_name(self, english_sheet_name):
        switcher = {
            "collect": "听过的音乐",
            "do": "在听的音乐",
            "wish": "想听的音乐",
        }
        return switcher.get(english_sheet_name, "nothing")

    def __initial_sheet(self, sheet_type, workbook, global_format, heading_format):
        sheet = workbook.add_worksheet(self.__map_chinese_sheet_name(sheet_type))

        if sheet_type == "collect" or sheet_type == "do":
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 3, 20, global_format)
            sheet.set_column(4, 4, 10, global_format)
            sheet.set_column(5, 5, 50, global_format)
            sheet_header = [u'专辑名', u'表演者', u'发行日期', u'标记日期', u'我的评分', u'我的评语']
        else:
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 3, 20, global_format)
            sheet.set_column(4, 4, 50, global_format)
            sheet_header = [u'专辑名', u'表演者', u'发行日期', u'标记日期', u'我的评语']

        for col, item in enumerate(sheet_header):
            sheet.write(0, col, item, heading_format)

    def initial_xlsx(self):
        workbook = xlsxwriter.Workbook(self.file_name, {'constant_memory': True})

        heading_format = workbook.add_format({'bold': True, 'font_name': 'PingFang SC', 'font_size': 11})
        global_format = workbook.add_format({'font_name': 'PingFang SC', 'font_size': 11})

        # initial 3 sheets
        for sheet_type in self.sheet_types:
            self.__initial_sheet(sheet_type, workbook, global_format, heading_format)

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
        info = []

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        album_items = soup.find_all("div", {"class": "item"})
        if album_items is not None:
            for item in album_items:
                # meta data
                douban_link = item.a['href']
                title = item.find("li", {"class": "title"}).em.text
                try:
                    artist = str(item.find("li", {"class": "intro"}).text).split(' / ')[0]
                except:
                    artist = None

                try:
                    release_date = str(item.find("li", {"class": "intro"}).text).split(' / ')[1]
                except:
                    release_date = None

                # user data
                mark_date = item.find("span", {"class": "date"}).text  # .contents[0] = .text

                try:
                    rating = self.get_rating(item.find("span", class_=lambda x: x != 'date')['class'][0])
                except:
                    rating = None

                try:
                    comment = item.find_all("li")[3].contents[0].strip()
                except IndexError:
                    comment = None
                info.append([title, artist, release_date, mark_date, rating, comment, douban_link])
        else:
            return None

        return info

    def get_max_index(self, sheet_type):
        url = f"https://music.douban.com/people/{self.user_id}/{sheet_type}"
        r = requests.get(url)
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
            yield f"https://music.douban.com/people/{self.user_id}/{sheet_type}" \
                  f"?start={index}&sort=time&rating=all&filter=all&mode=grid"

    def write_to_xlsx(self, infos, row, sheet_type):
        wb = xw.Book(self.file_name)
        sht = wb.sheets[self.__map_chinese_sheet_name(sheet_type)]
        if sheet_type == "collect" or sheet_type == "do":
            for index, info in enumerate(infos):
                tagA = 'A' + str(row + index)
                sht.range(tagA).add_hyperlink(info[-1], text_to_display=info[0], screen_tip=None)
                tagB = 'B' + str(row + index)
                sht.range(tagB).value = info[1: len(info) - 1]
        else:
            for index, info in enumerate(infos):
                tagA = 'A' + str(row + index)
                sht.range(tagA).add_hyperlink(info[-1], text_to_display=info[0], screen_tip=None)
                tagB = 'B' + str(row + index)
                sht.range(tagB).value = info[1:4] + [info[5]]
        wb.save()

    def start_task(self):
        self.initial_xlsx()

        for sheet_type in self.sheet_types:
            urls = self.url_generator(sheet_type)

            counter = 0
            row = 2
            for url in urls:
                info = self.export(url)
                self.write_to_xlsx(info, row + 15 * counter, sheet_type)
                counter += 1

if __name__ == "__main__":
    new_task = MusicSheet('Davidchili')
    new_task.start_task()
