
def additionalTagsString(entries, initialText, isNhentai=True):
    first = True
    replyString = ""
    if isNhentai:
        for entry in entries:
            if first:
                replyString += "**" + initialText + "**: " + entry[0] + " (" + format(entry[1], ',d') + ")"
                first = False
            else:
                replyString += ", " + entry[0] + " (" + format(entry[1], ',d') + ")"
    else:
        for entry in entries:
            if first:
                replyString += "**" + initialText + "**: " + entry
                first = False
            else:
                replyString += ", " + entry
    return replyString


def generate450string(site):
    return f"{site} returned 450 for this number. The gallery information is unavailable at this time.\n\n"

# taken from https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
def removeDuplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


# taken from https://stackoverflow.com/questions/6764909/python-how-to-remove-all-duplicate-items-from-a-list since the other one can't do nested lists
def removeDupes2(X):
    unique_X = []
    for i, row in enumerate(X):
        if row not in X[i + 1:]:
            unique_X.append(row)
    return unique_X