#参数datetime.time，对比time1是否小于time2
def compare_time(time1, time2):
    if (time1.hour < time2.hour) or (time1.hour == time2.hour and time1.minute < time2.minute)\
            or (time1.hour == time2.hour and time1.minute == time2.minute and time1.second < time2.second):
        return True
    else:
        False

#time_list is datetime.time list
def quite_sort_time_list(time_list, start, end):
    if start < end:
        mid = time_list[start]
        low = start
        high = end
        while low < high:
            while low < high and compare_time(mid, time_list[high]):
                high -= 1
            time_list[low] = time_list[high]
            while low < high and compare_time(time_list[low], mid):
                low += 1
            time_list[high] = time_list[low]
        time_list[low] = mid
        quite_sort_time_list(time_list, start, low - 1)
        quite_sort_time_list(time_list, low + 1, end)
