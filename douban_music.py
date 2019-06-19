import sys
import requests
import os

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter

from douban_exporter import DoubanExport


class MusicSheet(DoubanExport):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.category = "music"
        self.file_name = f"{self.user_id}_{self.category}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    def initial_sheet(self, sheet_type, workbook, global_format, heading_format):
        sheet = workbook.add_worksheet(self.map_chinese_sheet_name(sheet_type))

        if sheet_type == "collect" or sheet_type == "do":
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 3, 20, global_format)
            sheet.set_column(4, 4, 10, global_format)
            sheet.set_column(5, 5, 50, global_format)
            sheet.set_column(6, 6, 30, global_format)
            sheet_header = ['专辑名', '表演者', '发行日期',
                            '标记日期', '我的评分', '我的评语', 'Tags']
        else:
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 3, 20, global_format)
            sheet.set_column(4, 4, 50, global_format)
            sheet.set_column(5, 5, 30, global_format)
            sheet_header = ['专辑名', '表演者', '发行日期', '标记日期', '我的评语', 'Tags']

        for col, item in enumerate(sheet_header):
            sheet.write(0, col, item, heading_format)

    def export(self, url):
        info = []

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        album_items = soup.find_all("div", {"class": "item"})
        if len(album_items) > 0:
            for item in album_items:
                # meta data
                douban_link = item.a['href']
                title = item.find("li", {"class": "title"}).em.text
                try:
                    artist = str(
                        item.find("li", {"class": "intro"}).text).split(' / ')[0]
                except:
                    artist = None

                try:
                    release_date = str(
                        item.find("li", {"class": "intro"}).text).split(' / ')[1]
                except:
                    release_date = None

                # user data
                # .contents[0] = .text
                mark_date = item.find("span", {"class": "date"}).text

                try:
                    rating = self.get_rating(
                        item.find("span", class_=lambda x: x != 'date')['class'][0])
                except:
                    rating = None

                try:
                    comment = item.find_all("li")[3].contents[0].strip()
                except IndexError:
                    comment = None

                # the tags is None if not find
                tags = item.find("span", {"class": "tags"})
                if tags is not None:
                    tags = tags.text[3:].strip()

                info.append([title, artist, release_date, mark_date,
                             rating, comment, tags, douban_link])
        else:
            return None

        return info


if __name__ == "__main__":
    new_task = MusicSheet(sys.argv[1])
    new_task.start_task()
