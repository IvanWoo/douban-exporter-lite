import argparse

from douban_exporter_lite.douban_book import BookSheet
from douban_exporter_lite.douban_music import MusicSheet
from douban_exporter_lite.douban_movie import MovieSheet


def dispatch(category, user_id):
    if category == "book":
        new_task = BookSheet(user_id)
    elif category == "music":
        new_task = MusicSheet(user_id)
    elif category == "movie":
        new_task = MovieSheet(user_id)
    else:
        print("invalid category")
        return
    return new_task.start_task()


parser = argparse.ArgumentParser(description="Douban Data Exporter")
parser.add_argument("category", type=str, help="options: book, music, movie")
parser.add_argument("user_id", type=str, help="user handler")
args = parser.parse_args()

dispatch(args.category, args.user_id)
