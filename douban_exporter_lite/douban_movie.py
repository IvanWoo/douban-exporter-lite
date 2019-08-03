import sys
import requests
import os

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter

from douban_exporter_lite.douban_exporter import DoubanExporter


class MovieSheet(DoubanExporter):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.category = "movie"
        self.file_name = f"{self.user_id}_{self.category}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    def initial_sheet(self, sheet_type, workbook, global_format, heading_format):
        sheet = workbook.add_worksheet(self.map_chinese_sheet_name(sheet_type))

        if sheet_type == "collect" or sheet_type == "do":
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 5, 15, global_format)
            sheet.set_column(6, 7, 40, global_format)
            sheet_header = ['片名', '导演', '时长', '上映日期',
                            '标记日期', '我的评分', '我的评语', 'Tags']
        else:
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 4, 15, global_format)
            sheet.set_column(5, 6, 40, global_format)
            sheet_header = ['片名', '导演', '时长', '上映日期', '标记日期', '我的评语', 'Tags']

        for col, item in enumerate(sheet_header):
            sheet.write(0, col, item, heading_format)

    def export(self, url):
        info = []

        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        movie_items = soup.find_all("div", {"class": "item"})
        if len(movie_items) > 0:
            for item in movie_items:
                # meta data
                douban_link = item.a['href']
                title = item.find("li", {"class": "title"}).em.text

                meta_data_list = item.find(
                    "li", {"class": "intro"}).text.split(' / ')

                try:
                    movie_length = next(
                        meta_data for meta_data in meta_data_list if '分钟' in meta_data or 'minutes' in meta_data)
                except StopIteration:
                    movie_length = None
                # if not movie_length[0].isdigit():
                #     movie_length = None
                release_date = meta_data_list[0]
                if not release_date[0].isdigit():
                    release_date = None

                if movie_length is not None:
                    director = meta_data_list[meta_data_list.index(
                        movie_length) - 1]
                else:
                    director = None

                # user data
                # .contents[0] = .text
                mark_date = item.find("span", {"class": "date"}).text

                rating = item.find(
                    "span", {"class": "date"}).find_previous_siblings()
                if len(rating) > 0:
                    rating = DoubanExporter.get_rating(rating[0]['class'][0])
                else:
                    rating = None

                comment = item.find("span", {"class": "comment"})
                if comment is not None:
                    comment = comment.contents[0].strip()

                tags = item.find("span", {"class": "tags"})
                if tags is not None:
                    tags = tags.text[3:].strip()

                info.append([title, director, movie_length, release_date,
                             mark_date, rating, comment, tags, douban_link])
        else:
            return None

        return info


if __name__ == "__main__":
    new_task = MovieSheet(sys.argv[1])
    new_task.start_task()
