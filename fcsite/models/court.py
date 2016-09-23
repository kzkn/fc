#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import codecs
import json
import re
import requests
from BeautifulSoup import BeautifulSoup
from fcsite.utils import logd

charset = 'Shift_JIS'

placePattern = re.compile(ur'^(.+)テニス.+$')
termPattern = re.compile(r'\d{2}:\d{2}-\d{2}:\d{2}')

bldCd2place = {
	'001': u'雁の巣',	# 雁の巣レクリエーションセンター
	'002': u'舞鶴',	# 舞鶴公園
	'003': u'東平尾',	# 東平尾公園
	'004': u'今津',	# 今津運動公園
	'005': u'西部',	# 西部運動公園
	'006': u'桧原',	# 桧原運動公園
	'010': u'大井',	# 大井中央公園
	'011': u'上月隈',	# 上月隈中央公園
	'013': u'汐井',	# 汐井公園
	'024': u'青葉',	# 青葉公園
	'026': u'西南杜',	# 西南杜の湖畔公園
}

bldCds = [
	'011',	# 上月隈中央公園
	'010',	# 大井中央公園
	'013',	# 汐井公園
	'003',	# 東平尾公園
	'024',	# 青葉公園
	'026',	# 西南杜の湖畔公園
	'006',	# 桧原運動公園
	'005',	# 西部運動公園
	'002',	# 舞鶴公園
	'001',	# 雁の巣レクリエーションセンター
	'004',	# 今津運動公園
]

def get_blds():
	blds = []
	for bldCd in bldCds:
		blds.append({ 'bldCd': bldCd, 'place': bldCd2place[bldCd] })
	return blds

def search(json):
	urlWeb = 'https://www.comnet-fukuoka.jp/web/'
	urlTail = '.do;jsessionid='
	logd('json: ' + str(json))
	jsessionid = json['jsessionid']
	s = requests.Session()

	if jsessionid == '':
		# rsvWTransUserAttestationAction 案内・予約システムへ → メニュー画面
		post(s, urlWeb + 'rsvWTransUserAttestationAction.do', False, { 'displayNo': 'pawaa2000', 'dbInstanceNo': '1' })

		jsessionid = s.cookies.get('JSESSIONID')

		# rsvWTransInstSrchVacantAction 設備の空き状況 → 空き状況の検索画面
		post(s, urlWeb + 'rsvWTransInstSrchVacantAction' + urlTail + jsessionid, False, { 'displayNo': 'pawab2000' })

		# rsvWTransInstSrchMultipleAction 複合検索 → 複合検索条件画面
		post(s, urlWeb + 'rsvWTransInstSrchMultipleAction' + urlTail + jsessionid, False, {
			'displayNo': 'prwaa1000',
			'selectAreaCd': '',
			'selectBldCd': '',
			'selectPpsdCd': '0',
			'selectPpsCd': '0',
			'selectPpsPpsdCd': '0',
			'selectInstNo': '0',
			'dispWeekNum': '0',
			'dispWeek': ['0', '0', '0', '0', '0', '0', '0', '0'],
			'submmitMode': '1',
			'conditionMode': '3',
			'transVacantMode': '8',
			'dispSelectInstBldCd': '',
			'dispSelectInstCd': '',
			'selectCommunityManageCd': '',
			'selectCommunityPlaceCd': '',
			'productMode': '3',
			'areaMode': '2',
			})

	# rsvWGetInstSrchInfAction 検索開始 → 空き状況の検索結果画面
	bldCd = json['bldCd']
	activeDaysCount = 0
	days = json['days']
	for day in days:
		if (day == '1'):
			activeDaysCount += 1
	#logd('activeDaysCount: ' + str(activeDaysCount) + ', days: ' + str(days))
	r = post(s, urlWeb + 'rsvWGetInstSrchInfAction' + urlTail + jsessionid, False, {
		'displayNo': 'prwbb7000',
		'selectAreaCd': '0',
		'selectBldCd': bldCd,
		'selectPpsdCd': '0',
		'selectPpsCd': '8',
		'selectPpsPpsdCd': '1',
		'selectInstNo': '0',
		'dispWeekNum': activeDaysCount,
		'dispWeek': days,
		'submmitMode': '1',
		'conditionMode': '3',
		'transVacantMode': '8',
		'dispSelectInstBldCd': '0',
		'dispSelectInstCd': '0',
		'selectCommunityManageCd': '0',
		'selectCommunityPlaceCd': '0',
		'productMode': '3',
		'areaMode': '2',
		})
	(place, dates) = toJson(r)
	if bldCd == '001' or bldCd == '003':
		if bldCd == '001':	# 雁の巣次設備 (テニスバレーコート)
			r = post(s, urlWeb + 'rsvWInstSrchVacantAction' + urlTail + jsessionid, False, {
				'displayNo': 'prwcb1000',
				'transVacantMode': '6',
				'srchSelectInstNo': '1',
				})
		if bldCd == '003':	# 東平尾屋内
			r = post(s, urlWeb + 'rsvWGetInstSrchInfAction' + urlTail + jsessionid, False, {
				'displayNo': 'prwbb7000',
				'selectAreaCd': '0',
				'selectBldCd': bldCd,
				'selectPpsdCd': '0',
				'selectPpsCd': '24',
				'selectPpsPpsdCd': '2',
				'selectInstNo': '0',
				'dispWeekNum': activeDaysCount,
				'dispWeek': days,
				'submmitMode': '1',
				'conditionMode': '3',
				'transVacantMode': '8',
				'dispSelectInstBldCd': '0',
				'dispSelectInstCd': '0',
				'selectCommunityManageCd': '0',
				'selectCommunityPlaceCd': '0',
				'productMode': '3',
				'areaMode': '2',
				})
		(place2, dates2) = toJson(r)
		for di, date2 in enumerate(dates2):
			if di >= len(dates) or date2['date'] != dates[di]['date']:
				continue
			dates[di]['courts'].extend(date2['courts'])
	#printPlace2dates(place2dates)
	#logd(json.dumps(place2dates, sort_keys = True, indent = 2, ensure_ascii = False))
	#with codecs.open('comnet.json', 'w', 'utf-8') as out:
	#	json.dump(place2dates, out, sort_keys = True, indent = 2, ensure_ascii = False)
	return { 'jsessionid': jsessionid, 'bldCd': bldCd, 'place': place, 'dates': dates }

def search2(json):
	bldCd = json['bldCd']
	logd('bldCd: ' + bldCd)
	if bldCd == '':
		bldCd = bldCds[0]

	with open('work/comnet.json', 'r') as input:
		place2dates = json.load(input, encoding='utf-8')

		if bldCd not in bldCd2place.keys():
			return

		else:
			place = bldCd2place[bldCd]
			return { 'bldCd': bldCd, 'place': place, 'dates': place2dates[place] }

def get(s, url):
	logd(url + ':')
	r = s.get(url)
	#printResponse(r)

def post(s, url, shouldPrint, param):
	logd(url)
	r = s.post(url, data = param)
	if shouldPrint:
		printResponse(r)
	return r

def printResponse(r):
	logd('encoding: ' + r.encoding)
	logd('cookies: ' + str(r.cookies))
	logd()
	
	logd('cookies:')
	c = r.cookies.items()
	for k, v in c:
		logd(k + ': ' + v)
	logd()
	
	logd('content:')
	logd(r.content.decode(charset))

def toJson(r):
	soup = BeautifulSoup(r.content.decode(charset))
	placeTag = soup.find('font', { 'size': '+1' })
	place = placePattern.match(placeTag.text).group(1)
	#logd('place: [' + place + '], placeTag: ' + str(placeTag))

	dates = []
	table = soup.find('table', { 'border': '2' })
	trs = table.findAll('tr')
	for ri, tr in enumerate(trs):
		courtName = ''
		tds = tr.findAll('td')
		for ci, td in enumerate(tds):
			if ri == 0 and ci == 0:
				continue
			if ri == 0:
				date = td.text.strip()
				dates.append({ 'date': date, 'courts': [] })
				#logd('date: ' + date)
				continue
			courtIndex = ri - 1
			if ci == 0:
				courtName = td.text.strip()
				#logd('court: ' + courtName)
				for date in dates:
					date['courts'].append({ 'name': courtName, 'states': [] })
				continue
			dateIndex = ci - 1
			states = dates[dateIndex]['courts'][courtIndex]['states']
			termsText = td.text
			#logd('td: [' + termsText + ']')
			terms = termPattern.findall(termsText)
			for i, img in enumerate(td.findAll('img')):
				reservable = re.search(r'lw_emptybs\.gif', img['src'])
				states.append({ 'term': terms[i], 'reservable': reservable != None })
	return (place, dates)

def printPlace2dates(place2dates):
	for place in sorted(place2dates.keys()):
		logd(place + ': {')
		for date in place2dates[place]:
			logd('  ' + date['date'] + ': {')
			for court in date['courts']:
				logd('    ' + court['name'] + ': {')
				for state in court['states']:
					logd('      ' + state['term'] + ': ' + str(state['reservable']))
				logd('    }')
			logd('  }')
		logd('}')

if __name__ == '__main__':
	search()
