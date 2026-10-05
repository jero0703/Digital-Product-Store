from math import ceil

def page_meta(total:int,page:int,limit:int):
    return {"page":page,"limit":limit,"total":total,"total_pages":ceil(total/limit) if total else 0}
