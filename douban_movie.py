import sys
import requests
import os

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter


class MovieSheet(object):
    def __init__(self, user_id):
        self.category = "movie"
        self.user_id = user_id
        self.sheet_types = ["collect", "do", "wish"]
        self.file_name = f"{self.user_id}_{self.category}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    def __map_chinese_sheet_name(self, english_sheet_name):
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

    def __initial_sheet(self, sheet_type, workbook, global_format, heading_format):
        sheet = workbook.add_worksheet(self.__map_chinese_sheet_name(sheet_type))

        if sheet_type == "collect" or sheet_type == "do":
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 5, 15, global_format)
            sheet.set_column(6, 7, 40, global_format)
            sheet_header = ['片名', '导演', '时长', '上映日期', '标记日期', '我的评分', '我的评语', 'Tags']
        else:
            sheet.set_column(0, 1, 30, global_format)
            sheet.set_column(2, 4, 15, global_format)
            sheet.set_column(5, 6, 40, global_format)
            sheet_header = ['片名', '导演', '时长', '上映日期', '标记日期', '我的评语', 'Tags']

        for col, item in enumerate(sheet_header):
            sheet.write(0, col, item, heading_format)

    def __initial_xlsx(self):
        workbook = xlsxwriter.Workbook(self.file_name, {'constant_memory': True})

        heading_format = workbook.add_format({'bold': True, 'font_name': 'PingFang SC', 'font_size': 11})
        global_format = workbook.add_format({'font_name': 'PingFang SC', 'font_size': 11})

        # initial 3 sheets
        for sheet_type in self.sheet_types:
            self.__initial_sheet(sheet_type, workbook, global_format, heading_format)

        workbook.close()

    def __get_rating(self, rating_class):
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

        movie_items = soup.find_all("div", {"class": "item"})
        if len(movie_items) > 0:
            for item in movie_items:
                # meta data
                douban_link = item.a['href']
                title = item.find("li", {"class": "title"}).em.text

                meta_data_list = item.find("li", {"class": "intro"}).text.split(' / ')

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
                    director = meta_data_list[meta_data_list.index(movie_length) - 1]
                else:
                    director = None

                # user data
                mark_date = item.find("span", {"class": "date"}).text  # .contents[0] = .text

                rating = item.find("span", {"class": "date"}).find_previous_siblings()
                if len(rating) > 0:
                    rating = self.__get_rating(rating[0]['class'][0])
                else:
                    rating = None

                comment = item.find("span", {"class": "comment"})
                if comment is not None:
                    comment = comment.contents[0].strip()

                tags = item.find("span", {"class": "tags"})
                if tags is not None:
                    tags = tags.text[3:].strip()

                info.append([title, director, movie_length, release_date, mark_date, rating, comment, tags, douban_link])
        else:
            return None

        return info

    def get_max_index(self, sheet_type):
        url = f"https://{self.category}.douban.com/people/{self.user_id}/{sheet_type}"
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
            yield f"https://{self.category}.douban.com/people/{self.user_id}/{sheet_type}" \
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
                sht.range(tagB).value = info[1:5] + info[6:8]
        wb.save()

    def start_task(self):
        if not os.path.exists(self.file_name):
            self.__initial_xlsx()

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

if __name__ == "__main__":
    new_task = MovieSheet(sys.argv[1])
    new_task.start_task()
