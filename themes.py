import random

def scene(theme):
    if theme == "pop":
        return pop()
    elif theme == "punk":
        return punk()
    elif theme == "garage_rock":
        return garage_rock()
    elif theme == "disco":
        return disco()
    elif theme == "jazz":
        return jazz()
    elif theme == "dance":
        return dance()
    elif theme == "hip_hop":
        return hip_hop()
    elif theme == "psychedelic_rock":
        return psychedelic_rock()
    elif theme == "classic_rock":
        return classic_rock()
    elif theme == "funk":
        return funk()
    elif theme == "classical":
        return classical()
    elif theme == "lofi":
        return lofi()
    elif theme == "indie":
        return indie()
    elif theme == "romance":
        return romance()
    elif theme == "dining_chill":
        return dining_chill()
    else:
        return synthwave()


def synthwave():
    return random.choice([(267, 70), (329, 100), (253, 70), (170, 70)])


def pop():
    return random.choice([(57, 40), (193, 50), (348, 60), (9, 80), (41, 100), (359, 40)])


def punk():
    return random.choice([(76, 100), (207, 100), (270, 80)])


def garage_rock():
    return random.choice([(339, 100), (48, 100), (148, 70)])


def disco():
    return random.choice([(255, 80), (20, 79), (20, 80), (304, 50), (42, 60), (9, 99), (304, 49), (9, 100)])


def jazz():
    return random.choice([(24, 100), (24, 90), (34, 90), (4, 70), (20, 80), (55, 80), (54, 20)])


def dance():
    return random.choice([(30, 90), (198, 100), (6, 90), (181, 50), (220, 100)])


def hip_hop():
    return random.choice([(341, 100), (307, 100), (126, 90), (151, 60), (45, 90), (17, 70), (151, 59)])


def psychedelic_rock():
    return random.choice([(354, 70), (8, 80), (25, 80), (312, 100), (338, 60), (209, 80), (195, 50), (35, 90), (199, 80)])


def classic_rock():
    return random.choice([(178, 60), (0, 100), (355, 80), (59, 87), (27, 80)])


def funk():
    return random.choice([(359, 100), (346, 60), (322, 30), (45, 20), (286, 50), (14, 50), (360, 98)])


def classical():
    return random.choice([(219, 100), (86, 30), (219, 79), (49, 2), (219, 80), (219, 99), (41, 70)])


def lofi():
    return random.choice([(300, 10), (195, 44), (223, 59), (247, 50), (223, 60), (298, 20), (255, 60)])


def indie():
    return random.choice([(312, 100), (347, 60), (312, 40), (50, 59), (15, 100), (50, 60), (179, 50), (318, 44), (333, 100), (11, 100), (31, 39)])


def romance():
    return random.choice([(307, 38), (267, 48), (287, 38), (327, 38), (347, 38)])


def dining_chill():
    return random.choice([(22.733, 63.137), (263.01, 80.784), (160, 43.529)])
