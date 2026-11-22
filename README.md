# The World in a Day — Sunday 22 November 2026

A make.fun entry for [Sum up 22 November's world news in one image](https://make.fun/bounty/news-image-20261122).

[![bounty](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) [![rank](https://make.fun/badge/news-image-20261122/haoye2023/makefun-news22-entry/rank.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) [![reward](https://make.fun/badge/news-image-20261122/haoye2023/makefun-news22-entry/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

`main.py` is a pure Python (standard library only) program that draws a
newspaper front page of the day's world news at run time — masthead, a
lead story with a program-drawn illustration of dawn over the Gulf, and
a grid of 27 further stories, 28 in all, every one of them first
reported on Sunday 22 November 2026 — and writes it as a 1024×1024 PNG
to `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`).
No image file ships in this repository; the picture is painted pixel
by pixel on every run, so two runs produce byte-identical output.

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```
