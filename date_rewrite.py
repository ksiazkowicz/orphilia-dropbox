def month_int(month):	
	if month == "Jan":
	   month = "01"
	elif month == "Feb":
	   month = "02"
	elif month == "Mar":
	   month = "03"
	elif month == "Apr":
	   month = "04"
	elif month == "May":
	   month = "05"
	elif month == "Jun":
	   month = "06"
	elif month == "Jul":
	   month = "07"
	elif month == "Aug":
	   month = "08"
	elif month == "Sep":
	   month = "09"
	elif month == "Oct":
	   month = "10"
	elif month == "Nov":
	   month = "11"
	elif month == "Dec":
	   month = "12"
	return month
	
def translate_date(date1):
	day = date1[:2]
	date1 = date1[3:]
	month = month_int(date1[:3])
	date1 = date1[4:]
	year = date1[:4]
	date1 = date1[5:]
	hour = date1[:2]
	date1 = date1[3:]
	minute = date1[:2]
	date1 = date1[3:]
	second = date1[:2]

	hour = str(int(hour) +1)
	return year + month + day + hour + minute + "." + second

def generate_timestampd(date):
	day = date[:2]
	date = date[3:]
	month = month_int(date[:3])
	date = date[4:]
	year = date[:4]
	date = date[5:]
	hour = date[:2]
	date = date[3:]
	minute = date[:2]
	date = date[3:]
	second = date[:2]

	hour = str(int(hour) +1)

	return (((((int(year) * 12) + int(month)) * 30 + int(day)) * 24 + int(hour)) * 60 + int(minute)) * 60

def generate_modifytime(date):
	day = date[:2]
	date = date[3:]
	month = date[:3]
	date = date[4:]
	year = date[:4]
	date = date[5:]
	hour = date[:2]
	date = date[3:]
	minute = date[:2]
	date = date[3:]
	second = date[:2]

	modifytime = day + " " + month + " " + year + " " + hour + ":" + minute
	return modifytime
	
def generate_timestamp(date):
	print date
	month = month_int(date[:3])
	print month
	date = date[4:]
	print date
	day = date[:2]
	print day
	date = date[3:]
	print date
	hour = date[:2]
	print hour
	date = date[3:]
	print date
	minute = date[:2]
	print minute
	date = date[3:]
	print date
	second = date[:2]
	print second
	date = date[3:]
	print date
	year = date
	print year

	return (((((int(year) * 12) + int(month)) * 30 + int(day)) * 24 + int(hour)) * 60 + int(minute)) * 60
