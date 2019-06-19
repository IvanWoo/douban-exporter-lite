# douban-exporter-lite

A lightweight and faster Dòubàn data exporter

## Requirements

* [pyenv](https://github.com/pyenv/pyenv)
* Microsoft Excel

## Building and deployment

```sh
$ pyenv install 3.7.2
$ pyenv virtualenv 3.7.2 douban-exporter-lite
$ pyenv activate douban-exporter-lite

$ pip install -r requirements.txt
```

## How to Use

```sh
$ python worker.py [-h] category user_id
```

## Tips

For macOS users, you may need to give the grants of accessing some specific excel file due to a fantastic ["feature"](https://stackoverflow.com/questions/39604876/using-xlwings-to-open-an-excel-file-on-mac-os-x-el-capitan-requires-grant-access) of Excel 2016 on Mac.

## Acknowledgments

- Inspired by [Wildog](https://github.com/Wildog/douban-exporter).
- To Shinichi Atobe be the glory.