
def find_max(a1, a2, upper_limit):
    best_slope = -1
    best_x1 = -1
    best_x2 = -1
    # a2x2 <= a1x1
    for x1 in range(1, upper_limit+1):
        x2 = (a1 * x1) // a2
        if x2 / x1 > best_slope:
            if best_x1 != -1 and (best_x2 > 0) and (x1 % best_x1 == 0) and (x2 % best_x2 == 0):
                print(f'x1: {x1} best: {best_x1} mod: {x1 % best_x1}')
                continue
            best_slope = x2 / x1
            best_x1 = x1
            best_x2 = x2
    has_multiple = False
    if best_x1*2 <= upper_limit:
        multiple = upper_limit // best_x1
        best_x1 = best_x1 * multiple
        best_x2 = best_x2 * multiple
        has_multiple = True
    return best_slope, best_x1, best_x2, has_multiple

def find_convex(a1, a2, upper_limit):
    res = []
    cur_x, cur_y = 0, 0
    while 1:
        slope, x1, x2, has_multiple = find_max(a1, a2, upper_limit)
        res.append([slope, x1 + cur_x,x2 + cur_y, has_multiple])
        if x1 >= upper_limit:
            break
        cur_x = x1 + cur_x
        cur_y = x2 + cur_y
        upper_limit = upper_limit - x1
    return res



def find_upper_limit(a1, a2):
    right = a1*a2
    left = 1
    if 0:
        while right-left > 1:
            mid = (right + left)//2
            res = find_convex(a1, a2, mid)
            has_multiple = False
            for element in res:
                has_multiple |= element[3]
            if has_multiple:
                right = mid
            else:
                left = mid
        return left
    else:
        best_len = -1
        best_upper = -1
        for i in range(left, right+1):
            res = find_convex(a1, a2, i)
            has_multiple = False
            for element in res:
                has_multiple |= element[3]
            if has_multiple:
                continue
            if len(res) >= best_len:
                best_len = len(res)
                best_upper = i
        return best_upper
        
def f(n):
    if n < 2:
        return n
    return f(n-1) + f(n-2)

f_base = 8
a1 = f(f_base)
a2 = f(f_base + 1)
cur_x, cur_y = 0, 0
upper_limit = f(f_base + 2)#find_upper_limit(a1, a2)
print(f'Upper limit: {upper_limit}')
res = find_convex(a1, a2, upper_limit)
print(f'0, 0')
for element in res:
    temp_x = element[1]
    temp_y = element[2]
    print(f'{temp_x}, {temp_y}')

    
while 1:
    slope, x1, x2, has_multiple = find_max(a1, a2, upper_limit)
    print(f"Best slope: {slope} with x1: {x1 + cur_x}, x2: {x2 + cur_y},dif: {x1} has multiple: {has_multiple}")
    if x1 >= upper_limit:
        break
    cur_x = x1 + cur_x
    cur_y = x2 + cur_y
    upper_limit = upper_limit - x1
