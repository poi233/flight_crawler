# coding=UTF-8
import multiprocessing

import sys

from Crawler import Crawler
import const


def main(start=0, end=len(const.city_code)):
    city_list = const.city_code
    c = Crawler()
    pool = multiprocessing.Pool(multiprocessing.cpu_count() - 2)
    for i in range(int(start), int(end)):
        if c.check_compete(city_list[i]):
            continue
        for j in range(0, len(city_list)):
            if i != j:
                pool.apply_async(c.get_all_info, (city_list[i], city_list[j],))
    pool.close()
    pool.join()


if __name__ == "__main__":
    print('Usage: python main.py [start_index] [end_index]')
    if len(sys.argv) == 1:
        print("start at {}, end at {}".format(0, len(const.city_code)))
        main()
    elif len(sys.argv) == 2:
        print("start at {}, end at {}".format(sys.argv[1], len(const.city_code)))
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        print("start at {}, end at {}".format(sys.argv[1], sys.argv[2]))
        main(sys.argv[1], sys.argv[2])
    else:
        exit(1)
