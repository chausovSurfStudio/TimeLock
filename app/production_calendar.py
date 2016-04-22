prod_calendar_dict_2016 = {
	1: 15,
	2: 20,
	3: 21,
	4: 21,
	5: 19,
	6: 21,
	7: 21,
	8: 23,
	9: 22,
	10: 21,
	11: 21,
	12: 22,
}

def work_days_count(year, month):
	count = 0.001
	if year == 2016:
		return prod_calendar_dict_2016[month]
	return count