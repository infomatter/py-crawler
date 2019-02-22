import re
from simhash import Simhash, SimhashIndex
import jieba
import requests
import json
import ast
import time
import mysql.connector
from sumy.utils import get_stop_words
import nltk
# 注意把password设为你的root口令:
conn = mysql.connector.connect(user='root', password='infomatter666', database='test')

tolerance = 13  # 容忍度，判断是不是相似用的


def is_en(s):
    for uchar in s:
        if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
            return False
    return True


def is_cn(word):
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def get_features(s):
    punc = list('`~!@#$%^&*()_+-={}|:\"<>?[]\\;\',./')
    s = s.lower()
    s = nltk.word_tokenize(s)
    for word in s:
        if word in get_stop_words('english') or word in punc:
            s.remove(word)
    return s


def get_features_cn(s):
    punc = list('·~！!@#￥$%…&*（）()_——+-={}|、：:\'\"\\“”《》<>？?【】[]；‘’，。,./')
    s = s.lower()
    s = (" ".join(jieba.cut(s))).split()
    for word in s:
        if word in get_stop_words('chinese') or word in punc:
            s.remove(word)
    return s


def clustering():
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, cluster, sim_count, link, simhash FROM entries')
    entrylist = cursor.fetchall()
    objs = []
    entrydic = {}
    for item in entrylist:
        if not is_en(item[1]):
            if not item[4].startswith("https://weibo.com"):
                sim = Simhash(get_features_cn(item[1]))
                objs.append((str(item[0]), sim))
                entrydic[str(item[0])] = {
                    'title': item[1],
                    'cluster': 0,
                    'sim_count': 0,
                    'link': item[4],
                    'simhash': sim.value
                }
        else:
            sim = Simhash(get_features(item[1]))
            objs.append((str(item[0]), sim))
            entrydic[str(item[0])] = {
                'title': item[1],
                'cluster': 0,
                'sim_count': 0,
                'link': item[4],
                'simhash': sim.value
            }

    index = SimhashIndex(objs, k=tolerance)
    cluster_num = 1
    for key in entrydic:
        if entrydic[key]['cluster'] == 0:
            sims = index.get_near_dups(
                Simhash(get_features_cn(entrydic[key]['title'])))
            for item in sims:
                entrydic[item]['cluster'] = cluster_num
                # if len(sims) > 1:
                entrydic[item]['sim_count'] = len(sims) - 1
                cursor.execute('UPDATE entries SET cluster=%s, simhash=%s', (cluster_num, len(sims)-1))
                    # fout.write(item + '\t' + str(entrydic[item]['cluster']) + '\t' + entrydic[item]['title'] + '\t' + entrydic[item]['link'] + '\n')
            cluster_num += 1
    conn.commit()
    conn.close()
    # print("--------------------------------------")
    # for key in entrydic:
    #     print(key + '\t' + str(entrydic[key]['cluster']) + '\t' + entrydic[key]['title'])


clustering()