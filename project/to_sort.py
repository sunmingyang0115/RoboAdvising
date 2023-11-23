def merge(l1, l2, to):
    l3 = []
    while(len(l1) != 0 or len(l2) != 0):
        if (len(l1) == 0):
            l3.append(l2[0])
            l2 = l2[1:]
        elif (len(l2) == 0):
            l3.append(l1[0])
            l1 = l1[1:]
        elif (to(l1[0],l2[0])):
            l3.append(l1[0])
            l1 = l1[1:]
        elif (not(to(l1[0],l2[0]))):
            l3.append(l2[0])
            l2 = l2[1:]
    return l3
            
def msort(lst, to):
    nlst = []
    for e in lst:
        nlst.append([e])
        
    while (len(nlst) != 1):
        nnlst = []
        length = (int)(len(nlst)/2)
        for i in range(length+1):
            ind = i*2
            if (ind < len(nlst) - 1):
                nnlst.append(merge(nlst[ind], nlst[ind+1], to))
            elif (ind == len(nlst) - 1):
                nnlst.append(nlst[ind])
        nlst = nnlst
        
    return nlst[0]
