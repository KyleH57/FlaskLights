
def rap1(color, constellation, num, num_segments):
    # multi segment

    # #print("rap1")
    # #print(num)
    # x = num % 10
    # if x == 0:
    #     constellation.clear()
    #     constellation.set_segment_color(0, color)
    # else:
    #     constellation.set_segment_color(x, color)
    #     #print(num % 10)


    # 1 segment at a time
    #print("rap1")
    #print(num)
    x = num % num_segments
    if x == 0:
        constellation.clear()
        constellation.set_segment_color(0, color)
    else:
        constellation.clear()
        constellation.set_segment_color(x, color)
        #print(num % 10)




