import sys
import requests
import os
from typing import List

from datetime import datetime
from bs4 import BeautifulSoup
import xlwings as xw
import xlsxwriter

from douban_exporter_lite.douban_exporter import DoubanExporter
from douban_exporter_lite.misc import HEADERS


class BookSheet(DoubanExporter):
    def __init__(self, user_id):
        super().__init__(user_id)
        self.category = "book"
        self.file_name = (
            f"{self.user_id}_{self.category}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        )

    def initial_sheet(self, sheet_type, workbook, global_format, heading_format):
        sheet = workbook.add_worksheet(self.map_chinese_sheet_name(sheet_type))

        if sheet_type == "collect" or sheet_type == "do":
            sheet.set_column(0, 2, 30, global_format)
            sheet.set_column(3, 5, 15, global_format)
            sheet.set_column(6, 7, 40, global_format)
            sheet_header = ["书名", "作者", "出版社", "出版日期", "标记日期", "我的评分", "我的评语", "Tags"]
        elif sheet_type == "wish":
            sheet.set_column(0, 2, 30, global_format)
            sheet.set_column(3, 4, 15, global_format)
            sheet.set_column(5, 6, 40, global_format)
            sheet_header = ["书名", "作者", "出版社", "出版日期", "标记日期", "我的评语", "Tags"]
        else:
            raise ValueError("wrong sheet type!")

        for col, item in enumerate(sheet_header):
            sheet.write(0, col, item, heading_format)

    def export(self, url: str) -> List[str]:
        infos = []
        info_keys = [
            "title",
            "writer",
            "publishing_company",
            "publish_date",
            "mark_date",
            "rating",
            "comment",
            "tags",
            "douban_link",
        ]
        r = requests.get(url, cookies=self.cookies, headers=HEADERS)
        soup = BeautifulSoup(r.text, "lxml")
        book_items = soup.find_all("li", {"class": "subject-item"})
        if len(book_items) > 0:
            for item in book_items:
                info_dict = dict.fromkeys(info_keys)
                # meta data
                info_dict["douban_link"] = item.a["href"]
                title = item.find("h2").text.strip()
                # gibberish of douban front-end
                info_dict["title"] = (
                    ": ".join(list(map(lambda x: x.strip(), title.split(" : "))))
                    if ":" in title
                    else title
                )
                meta_data_list = list(
                    map(
                        lambda x: x.strip(),
                        item.find("div", {"class": "pub"}).text.split(" / "),
                    )
                )
                if len(meta_data_list[0]) > 0:
                    info_dict["writer"] = meta_data_list[0]
                    try:
                        publish_date = next(
                            meta_data
                            for meta_data in meta_data_list
                            if meta_data[0].isdigit()
                        )
                    except StopIteration:
                        publish_date = None
                    info_dict["publish_date"] = publish_date

                    if publish_date:
                        info_dict["publishing_company"] = meta_data_list[
                            meta_data_list.index(publish_date) - 1
                        ]

                # user data
                # .contents[0] = .text
                info_dict["mark_date"] = item.find(
                    "span", {"class": "date"}
                ).text.split("\n")[0]

                rating = item.find("span", {"class": "date"}).find_previous_siblings()
                if len(rating) > 0:
                    info_dict["rating"] = DoubanExporter.get_rating(
                        rating[0]["class"][0]
                    )

                comment = item.find("p", {"class": "comment"})
                if comment:
                    info_dict["comment"] = comment.contents[0].strip()

                tags = item.find("span", {"class": "tags"})
                if tags:
                    info_dict["tags"] = tags.text[3:].strip()

                infos.append([info_dict[key] for key in info_keys])
        else:
            return None

        return infos


if __name__ == "__main__":
    new_task = BookSheet(sys.argv[1])
    new_task.start_task()
