import requests
import re
from constants import URL
from utils import build_custom


def template(langcodes, user_id):
    to_return = "{URL}\n" + f"http://example.com/templates/{user_id}.txt\n\n"
    for langcode in langcodes:
        if len(langcodes) == 1:
            if langcode == "redirect":
                r = requests.get("http://data.telegram.wiki/tl_redirect.txt")
                text = '\n'.join(r.text.split('\n')[3:])
                text = "{COMMENT}\nstart of official redirect\n" + text + "\n{COMMENT}\nend of official redirect"
                return to_return + text
            else:
                r = requests.get(URL.format(langcode))
                text = '\n'.join(r.text.split('\n')[3:])
                text = "{COMMENT}\nstart of official language\n" + text + "\n{COMMENT}\nend of official language\n\n"
                return to_return + text
        if langcode == "redirect":
            r = requests.get("http://data.telegram.wiki/tl_redirect.txt")
            text = '\n'.join(r.text.split('\n')[3:])
            text = "{COMMENT}\nstart of official redirect\n" + text + "\n{COMMENT}\nend of official redirect"
            to_return += text
        else:
            r = requests.get(URL.format(langcode))
            if langcode == "es_419":
                langcode = "es_"
            text = '\n'.join(r.text.split('\n')[3:])
            temp_0 = text
            result = re.findall("N}\n(.*?){", text, re.S)
            temp = []
            for keys in result:
                temp.append(f"({langcode.upper()}) " + keys)
            x = 0
            for string in temp:
                temp_0 = temp_0.replace(result[x], string)
                x += 1
            result = re.findall("S}\n(.*?){", r.text, re.S)
            temp = []
            for keys in result:
                temp.append(keys.replace("\n", "{}\n".format(langcode)))
            x = 0
            for string in temp:
                temp_0 = temp_0.replace(result[x], string)
                x += 1
            temp_0 = "{COMMENT}\nstart of official language\n" + temp_0 + "\n{COMMENT}\nend of official language"
            to_return += temp_0
    return to_return


def custom(string, langcodes, user_id):
    m = re.findall("{(.*?)\}\n([^{]*)", string)
    to_return = []
    base = []
    x = 0
    y = 0
    for keys in m:
        values = keys[1].rstrip()
        if keys[0] == "KEYS":
            values = values.split('\n')
            base.append({keys[0]: values})
        elif len(values) > 1:
            base.append({keys[0]: values})
        else:
            base.append({keys[0]: values[0]})
        x += 1
        if x % 3 == 0:
            if base:
                temp = {}
                for dic in base:
                    temp.update(dic)
                to_return.append(temp)
                base.clear()
                y += 1
            else:
                pass
    if not to_return:
        return [None, "nothing"]
    text = template(langcodes, user_id)
    m = re.findall("{(.*?)\}\n([^{]*)", text)
    errors = {"q": [], "k": [], "i": []}
    for dics in to_return:
        try:
            for keys in m:
                values = keys[1].rstrip()
                if keys[0] == "QUESTION":
                    question = dics["QUESTION"]
                    if question == values:
                        errors["q"].append(dics)
                elif keys[0] == "KEYS":
                    for key in dics["KEYS"]:
                        for value in values.split('\n'):
                            if key == value:
                                errors["k"].append(dics)
                                errors["i"].append(dics["KEYS"].index(key))
            for names in dics:
                if names != "QUESTION":
                    if names != "KEYS":
                        if names != "VALUE":
                            raise KeyError
        except KeyError:
            return [to_return, "", dics]
    if errors["q"]:
        if errors["k"]:
            return [to_return, "qk", errors]
        else:
            return [to_return, "q", errors]
    if errors["k"]:
        return [to_return, "k", errors]
    return [to_return]


def generate(user, user_id):
    text = template(user["langcodes"], user_id)
    if user["custom_pre"]:
        pre = build_custom(user["custom_pre"])
        text = "{COMMENT}\nBeginning of custom overriding questions\n\n" + pre + "\n\n" + text
    text = text + "\n\n{COMMENT}\nBeginning of custom template\n\n" + build_custom(user["custom"])
    if user["custom_post"]:
        post = build_custom(user["custom_post"])
        text = text + "\n\n{COMMENT}\nBeginning of custom overriding keys\n\n" + post
    return text


def check_diff(user_id, user):
    new = template(user["langcodes"], user_id)
    try:
        old = open(f"templates/tl_{str(user_id)}.txt", "r", encoding='UTF-8').read()
    except FileNotFoundError:
        return False
    new_strings = re.findall("{COMMENT}\nstart of official language\n(.*?){COMMENT}\nend of official language", new,
                             flags=re.S)
    old_strings = re.findall("{COMMENT}\nstart of official language\n(.*?){COMMENT}\nend of official language", old,
                             flags=re.S)
    x = 0
    for string in new_strings:
        if string == old_strings[x]:
            return True
        x += 1
    return False
