#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timedelta, time

os.system('clear')

def year_data(year=None):

    if year is None:
        date = datetime.now()
        year = date.strftime("%Y")

    # Create placeholders boundary days of year 
    day_one_obj = datetime(int(year), 1, 1)
    day_last_obj = datetime(int(year), 12, 31)

    # Create placeholder for the date of the day one's week
    DayOneOfFirstDayWeek_obj = day_one_obj - timedelta(days = day_one_obj.weekday())

    # Create placeholder for the date of the day last's week
    DayLastOfLastDayWeek_obj = day_last_obj + timedelta(days = 6 - day_last_obj.weekday())

    # Create a nested dictionary with the week of the year as key and the correponding dates and weekdays as values. 
    calender = {
        (DayOneOfFirstDayWeek_obj + timedelta(days=day)).strftime("%d/%m/%Y"):
        {
            int(
                (DayOneOfFirstDayWeek_obj + timedelta(days=day)).strftime("%W")
                )+1:
            (DayOneOfFirstDayWeek_obj + timedelta(days=day)).strftime("%A"),
        }
        for day in range(
            0, (
                DayLastOfLastDayWeek_obj - DayOneOfFirstDayWeek_obj).days + 1
            )
            }
    print('-'*50,'\n',calender,'\n','-'*50)

    for keys in calender:
        print(keys, calender[keys])

    return calender

def convert_dt_obj(string):
    parser = "%d/%m/%Y"
    date = dict(
        day = datetime.strptime(string,parser).strftime("%d"),
        month = datetime.strptime(string,parser).strftime("%m"),
        year = datetime.strptime(string,parser).strftime("%Y"),
        date_obj = datetime.strptime(string,parser)
    )

    return date

year_data(sys.argv[1])
print(convert_dt_obj(sys.argv[2])['day'])
print(convert_dt_obj(sys.argv[2])['month'])
print(convert_dt_obj(sys.argv[2])['year'])
print(convert_dt_obj(sys.argv[2])['date_obj'])

