import requests

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter


class MusicSheet(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.file_name = self.user_id + " " + datetime.now().strftime("%Y-%m-%d") + ".xlsx"

    def initial_xlsx(self):
        workbook = xlsxwriter.Workbook(self.file_name, {'constant_memory': True})

        heading_format = workbook.add_format({'bold': True, 'font_name': 'PingFang SC', 'font_size': 14})
        global_format = workbook.add_format({'font_name': 'PingFang SC', 'font_size': 14})

        collect_sheet = workbook.add_worksheet(u'听过的音乐')
        collect_sheet.set_column(0, 1, 38, global_format)
        collect_sheet.set_column(2, 3, 25, global_format)
        collect_sheet.set_column(4, 4, 13, global_format)
        collect_sheet.set_column(5, 5, 64, global_format)

        collect_do_sheet_header = [u'专辑名', u'表演者', u'发行日期', u'标记日期', u'我的评分', u'我的评语']

        for col, item in enumerate(collect_do_sheet_header):
            collect_sheet.write(0, col, item, heading_format)

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

        album_item = soup.find_all("div", {"class": "item"})
        for child in album_item:
            # meta data
            douban_link = child.a['href']
            title = child.find("li", {"class": "title"}).em.text
            try:
                artist = str(child.find("li", {"class": "intro"}).text).split(' / ')[0]
            except:
                artist = None

            try:
                release_date = str(child.find("li", {"class": "intro"}).text).split(' / ')[1]
            except:
                release_date = None

            # user data
            mark_date = child.find("span", {"class": "date"}).text  # .contents[0] = .text

            try:
                rating = self.get_rating(child.find("span", class_=lambda x: x != 'date')['class'][0])
            except:
                rating = None

            try:
                comment = child.find_all("li")[3].contents[0].strip()
            except IndexError:
                comment = None
            info.append([title, artist, release_date, mark_date, rating, comment, douban_link])

        return info

    def get_max_index(self):
        url = "https://music.douban.com/people/%s/collect" % self.user_id
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        paginator = soup.find("div", {"class": "paginator"})
        max_index = paginator.find_all("a")[-2].get_text()

        return int(max_index)

    def url_generator(self):
        max_index = self.get_max_index()
        for index in range(0, max_index * 15, 15):
            yield "https://music.douban.com/people/%s/collect?start=%d&sort=time&rating=all&filter=all&mode=grid" \
                  % (self.user_id, index)

    def write_to_xlsx(self, infos, row):
        wb = xw.Book(self.file_name)
        sht = wb.sheets['听过的音乐']
        for index, info in enumerate(infos):
            tagA = 'A' + str(row + index)
            sht.range(tagA).add_hyperlink(info[-1], text_to_display=info[0], screen_tip=None)
            tagB = 'B' + str(row + index)
            sht.range(tagB).value = info[1: len(info) - 1]

    def start_task(self):
        self.initial_xlsx()
        urls = self.url_generator()

        counter = 0
        row = 2
        for url in urls:
            info = self.export(url)
            self.write_to_xlsx(info, row + 15 * counter)
            counter += 1

if __name__ == "__main__":
    new_task = MusicSheet('lhc-creep')
    new_task.start_task()
