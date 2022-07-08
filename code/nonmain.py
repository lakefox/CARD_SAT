import time

def cleanUsers(users, usersOn2, usersOn3):
    for user in users:
        if users[user].checkin:
            # check is user has checked in within 3 hours
            if time.ticks_ms()-users[user].checkin > 1.08e+7:
                # if not delete the user
                if users[user].freq == 2:
                    usersOn2 -= 1
                elif users[user].freq == 3:
                    usersOn3 -= 1
                del users[user]
    return users, usersOn2, usersOn3;

def userInFootPrint(user, cPos):
    minPos = 101
    maxPos = 0
    for userPos in user["locationList"]:
        if userPos < minPos:
            minPos = userPos
        elif userPos > maxPos:
            maxPos = userPos
    if cPos > minPos and cPos < maxPos:
        return True
    else:
        return False

def cleanAwaitMsg(awaitingMessages):
    for msg in awaitingMessages:
        # check if the qued time is greater than 10 minutes then delete it
        if time.ticks_ms()-msg["quedTime"] > 600000:
            awaitingMessages.remove(msg)
    return awaitingMessages