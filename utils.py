from constants import LANGCODES
from telegram import InlineKeyboardButton


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def build_language_keyboard(user_data):
    button_list = []
    for name in LANGCODES:
        skip = False
        for already_chosen in user_data:
            if LANGCODES[name] == already_chosen:
                skip = True
            else:
                pass
        if skip:
            pass
        else:
            button_list.append(InlineKeyboardButton(name, callback_data="more_" + LANGCODES[name]))
    return button_list


def build_custom(user_data):
    to_return = ""
    for template in user_data:
        question = "\n{QUESTION}\n" + template["QUESTION"] + "\n"
        value = "{VALUE}\n" + template["VALUE"]
        keys = "{KEYS}\n"
        for real_key in template["KEYS"]:
            keys = keys + real_key + "\n"
        to_return = to_return + question + keys + value
    return to_return
