import templates
from database import database
from constants import LANGCODES, C_STRING
import bot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ChatAction
from telegram.utils.helpers import mention_html
from telegram.error import Unauthorized
import utils
import io


def start(update, context):
    if database.get_user(update.effective_user.id):
        string = "The /start command isn't really used here. You can run /setup to set this bot up for you (or " \
                 "override existing values), /custom to add your custom templates, and finally /generate to generate " \
                 "your template file. "
        context.bot.send_message(chat_id=update.message.chat_id, text=string)
    elif str(update.effective_user.id) in database.get_banned():
        update.message.reply_text("You are banned.")
    else:
        button_list = [[InlineKeyboardButton("Yes", callback_data="start_yes_"),
                       InlineKeyboardButton("No", callback_data="start_no")]]
        update.message.reply_html("This bot is for the <b>Telegram Support Force</b> only. Do you think you belong to "
                                  "them (you know if you do)? Then press yes and better not be a troll, or someone will"
                                  " get mad at you.",
                                  reply_markup=InlineKeyboardMarkup(button_list))


def start_inline(update, context):
    query = update.callback_query
    if query.data[6:8] == "no":
        query.edit_message_text("Thanks for being honest. Have a good day.")
    else:
        user_id = update.effective_user.id
        button_list = [InlineKeyboardButton("Accept", callback_data="add_yes_" + str(user_id)),
                       InlineKeyboardButton("Ban", callback_data="add_no__" + str(user_id))]
        string = f"Should the user {mention_html(update.effective_user.id, update.effective_user.first_name)} " \
            f"be accepted?"
        context.bot.send_message(chat_id=208589966, text=string,
                                 reply_markup=InlineKeyboardMarkup(utils.build_menu(button_list, 2)),
                                 parse_mode=ParseMode.HTML)
        query.edit_message_text("Request has been forwarded. You'll be notified if you've been accepted or not.")


def add_inline(update, context):
    query = update.callback_query
    user_id = query.data[8:len(query.data)]
    if query.data[4:6] == "no":
        database.insert_banned_user(user_id)
        try:
            string = "Sorry to tell you that, but you have been banned. Think about which buttons you press (and " \
                     "people you annoy) the next time you may run into <i>for X persons only</i> bots. Have a day! "
            context.bot.send_message(chat_id=user_id, text=string,
                                     parse_mode=ParseMode.HTML)
            query.edit_message_text("User has been BANNED.")
        except Unauthorized:
            query.edit_message_text("User has been BANNED (and blocked this bot lol).")
    else:
        database.insert_user(user_id, [])
        string = "You have been accepted.\n\nIf you want to use this bot, please run /setup.\n\nPlease keep in mind " \
                 "that this bot is fairly new and made by Poolitzer, so expect to encounter bugs (maybe?) and don't " \
                 "hesitate to ping my maker if you encounter issues."
        context.bot.send_message(chat_id=user_id, text=string)
        query.edit_message_text("User has been ADDED.")


def setup(update, context):
    if str(update.effective_user.id) in database.get_users():
        button_list = []
        for name in LANGCODES:
            button_list.append(InlineKeyboardButton(name, callback_data="second_" + LANGCODES[name]))
        update.message.reply_text("Let's do this!\n\nFirst of all, you need to tell me the languages you want to "
                                  "combine.\n\nUse /cancel at any time to cancel this whole setup.",
                                  reply_markup=InlineKeyboardMarkup(utils.build_menu(button_list, 2)))
        context.user_data["languages"] = []
        return bot.SECOND


def second_inline(update, context):
    query = update.callback_query
    user_data = context.user_data["languages"]
    user_data.append(query.data[7:len(query.data)])
    button_list = utils.build_language_keyboard(user_data)
    string = "Tell me a second one now if you want to honour this bots name (press finish if you just want to add " \
             "custom templates)."
    reply_markup = InlineKeyboardMarkup(utils.build_menu(button_list, 2, footer_buttons=[InlineKeyboardButton(
                                                                                    "Finish", callback_data="finish")]))
    query.edit_message_text(string, reply_markup=reply_markup)
    return bot.MORE


def more_inline(update, context):
    messages = ["nothing", "lol", "Great. You can either add more languages (you bilingual monster) or finish this "
                                  "part of the setup.",
                "Ok, you got three now, that's cool. Lets not do more",
                "Four? Really? Now it's time to stop", "You speak five languages? Nah, that's a joke",
                "Six? You must be kidding me.", "Just gonna stop counting. You do you."]
    query = update.callback_query
    user_data = context.user_data["languages"]
    user_data.append(query.data[5:len(query.data)])
    button_list = utils.build_language_keyboard(user_data)
    if len(user_data) > 7:
        string = messages[7]
    else:
        string = messages[len(user_data)]
    reply_markup = InlineKeyboardMarkup(utils.build_menu(button_list, 2, footer_buttons=[InlineKeyboardButton(
                                                                                    "Finish", callback_data="finish")]))
    query.edit_message_text(string, reply_markup=reply_markup)
    return bot.MORE


def finish_inline(update, context):
    query = update.callback_query
    user_data = context.user_data["languages"]
    user_id = update.effective_user.id
    database.insert_user(user_id, user_data)
    database.to_file(templates.generate(database.get_user(user_id), user_id), user_id)
    string = "Great. You are in the system now. Do you want to add your custom templates as well?"
    button_list = [InlineKeyboardButton("Yes", callback_data="custom"),
                   InlineKeyboardButton("No", callback_data="create")]
    query.edit_message_text(string, reply_markup=InlineKeyboardMarkup([button_list]))
    return bot.ConversationHandler.END


def cancel_setup(update, _):
    update.message.reply_text("Setup cancelled. Run it again with /setup if you want ;P")
    return bot.ConversationHandler.END


def create(update, _):
    query = update.callback_query
    query.edit_message_text("Cool. If you want to see your language file, send /generate.")


def custom_start_inline(update, context):
    user_data = context.user_data
    query = update.callback_query
    query.edit_message_text(C_STRING, parse_mode=ParseMode.HTML)
    user_data["custom"] = []
    user_data["error_q"] = []
    user_data["error_k"] = []
    return bot.CUSTOM_RECEIVE


def custom_start_command(update, _):
    if str(update.effective_user.id) in database.get_users():
        string = "Hey. Do you want to append your current custom templates? Or override it? In case of the " \
                 "latter, I'd suggest you /generate your file one last time, so if you mess up, you can copy them " \
                 "again. Don't tell me I didn't warn you, and never forget /cancel."
        buttons = [[InlineKeyboardButton("Append", callback_data="custom_a"),
                   InlineKeyboardButton("Override", callback_data="custom_o")]]
        update.message.reply_html(string, reply_markup=InlineKeyboardMarkup(buttons))
        return bot.CUSTOM_CHOOSE


def custom_generate(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
    context.bot.send_document(chat_id=update.message.chat_id,
                              document=open(f"templates/tl_{update.effective_user.id}.txt", "rb"),
                              filename="tl_multilanguage.txt")
    return bot.CUSTOM_CHOOSE


def custom_append(update, context):
    query = update.callback_query
    user_data = context.user_data
    user = database.get_user(update.effective_user.id)
    user_data["custom"] = user["custom"]
    user_data["error_q"] = user["custom_post"]
    user_data["error_k"] = user["custom_pre"]
    query.edit_message_text(C_STRING, parse_mode=ParseMode.HTML)
    return bot.CUSTOM_RECEIVE


def custom_override(update, context):
    query = update.callback_query
    user_data = context.user_data
    user_data["custom"] = []
    user_data["error_q"] = []
    user_data["error_k"] = []
    query.edit_message_text(C_STRING, parse_mode=ParseMode.HTML)
    return bot.CUSTOM_RECEIVE


def custom_receive(update, context):
    user_data = context.user_data
    custom_incoming = update.message.text
    user_id = update.effective_user.id
    user = database.get_user(user_id)
    returned_dic = templates.custom(custom_incoming, user["langcodes"], user_id)
    if len(returned_dic) > 1:
        if returned_dic[1] == "nothing":
            update.message.reply_text("You need to send me something with the three values and stuff. This txt should "
                                      "work on all platforms, no escape from adding dummy questions, sorry. You can "
                                      "send me real custom templates now or use /cancel to escape this madness.")
            return bot.CUSTOM_RECEIVE
        user_data["custom"] = user_data["custom"] + returned_dic[0]
        if returned_dic[1] == "qk":
            string_main = "One or more of your custom keys and question have resulted in a duplicate error. This " \
                          "means the following: In case of the <b>questions</b>, the <b>TDesktop client</b> will show "\
                          "yours and not the one from the official source. In case of the <b>keys</b>, the <b>android "\
                          "client</b> will only show yours and not the one from the official source. If you decide to "\
                          "proceed, updates to these templates will be overridden by your custom ones, meaning you " \
                          "have to check by yourself if something important changed. Now to the duplicate " \
                          "questions:\n\n "
            string_q = ""
            for error in returned_dic[2]["q"]:
                string_q = string_q + "<i>" + error["QUESTION"] + "</i>\n"
            string_k = ""
            for error in returned_dic[2]["k"]:
                string_k = string_k + "<i>" + error["KEYS"][returned_dic[2]["i"][returned_dic[2]["k"].index(error)]] + \
                           "</i>\n"
            string_between = "\nAnd the duplicate keys:\n\n"
            string = string_main + string_q + string_between + string_k.rstrip()
            user_data["error_q"] = user_data["error_q"] + returned_dic[2]["q"]
            user_data["error_k"] = user_data["error_k"] + returned_dic[2]["k"]
        elif returned_dic[1] == "q":
            string_main = "One or more of your custom question have resulted in a duplicate error. This means that if" \
                          " you choose to ignore this warning, the TSupport desktop client will show your question " \
                          "instead of the one from the official source. This also means that if this template gets " \
                          "updated, you won't receive the updated version and have to make sure that your custom " \
                          "template is up-to-date!\n\n "
            string_q = ""
            for error in returned_dic[2]["q"]:
                string_q = string_q + error["QUESTION"] + "\n"
            string = string_main + string_q.rstrip()
            user_data["error_q"] = user_data["error_q"] + returned_dic[2]["q"]
        elif returned_dic[1] == "k":
            string_main = "One or more of your custom keys have resulted in a duplicate error. This means that the " \
                          "Tsupport android client will only show your custom values instead of the official ones. If "\
                          "you choose to ignore this warning, this also means that you wont receive updates to this " \
                          "template since your custom ones are shown instead. So you have to make sure by yourself " \
                          "that these templates are always up-to-date!\n\n "
            string_k = ""
            for error in returned_dic[2]["k"]:
                string_k = string_k + error["KEYS"][returned_dic[2]["i"][returned_dic[2]["k"].index(error)]] + "\n"
            string = string_main + string_k.rstrip()
            user_data["error_k"] = user_data["error_k"] + returned_dic[2]["k"]
        else:
            string_main = "Oh no. One of your custom tags are wrong. Instead of {QUESTION}, {KEYS}, {VALUE}, " \
                          "I received this:\n\n "
            string_after = "\n\nIf you want to, you can send me the fixed version now and I will go through it again." \
                           " Or you can send /cancel to escape this madness."
            string = string_main + str(returned_dic[2]) + string_after
            update.message.reply_text(string)
            return bot.CUSTOM_RECEIVE
        buttons = [InlineKeyboardButton("Proceed", callback_data="custom_proceed"),
                   InlineKeyboardButton("Rename", callback_data="custom_receive"),
                   InlineKeyboardButton("Cancel", callback_data="custom_cancel")]
        reply_markup = InlineKeyboardMarkup(utils.build_menu(buttons, 2))
        update.message.reply_text(string, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return bot.CUSTOM_ERROR
    else:
        user_data["custom"] = user_data["custom"] + returned_dic[0]
        database.insert_custom(update.effective_user.id, user_data["custom"])
        database.to_file(templates.generate(database.get_user(user_id), user_id), user_id)
        update.message.reply_text("Great. Your custom templates have been added. If you want to generate your "
                                  "language file, send me /generate.")
        return bot.ConversationHandler.END


def custom_error_proceed(update, context):
    query = update.callback_query
    user_data = context.user_data
    user_id = update.effective_user.id
    database.insert_custom(update.effective_user.id, user_data["custom"])
    database.insert_custom_overrides(user_id, user_data["error_q"], user_data["error_k"])
    database.to_file(templates.generate(database.get_user(user_id), user_id), user_id)
    string = "Great. Your custom duplicates have been added and will override the originals in the respective apps " \
             "now. If you want to see your language file, send /generate."
    query.edit_message_text(string)
    return bot.ConversationHandler.END


def custom_error_receive(update, _):
    query = update.callback_query
    query.edit_message_text("Ok. Please rename your duplicates as you wish, then send me your template(s) again :)")
    return bot.CUSTOM_RECEIVE


def custom_error_cancel(update, _):
    query = update.callback_query
    query.edit_message_text("Ok. If you want to try again, run /custom. If you just want to see the file without your "
                            "custom templates, send me /generate :)")
    return bot.ConversationHandler.END


def custom_cancel(update, _):
    update.message.reply_text("Adding custom template cancelled. Run it again with /custom if you want ;P")
    return bot.ConversationHandler.END


def generate_file(update, context):
    if str(update.effective_user.id) in database.get_users():
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        context.bot.send_document(chat_id=update.message.chat_id,
                                  document=open(f"templates/tl_{update.effective_user.id}.txt", "rb"),
                                  filename="tl_multilanguage.txt")


def update_start(_, context):
    jobs = context.job_queue.jobs()
    if not jobs:
        buttons = [[InlineKeyboardButton("Update", callback_data="update_g"),
                    InlineKeyboardButton("Typo", callback_data="update_t")]]
        string = "Hey Daria. Deep told me there is an update for the english template, is this a global update or a " \
                 "just a typo one?"
        context.bot.send_message(chat_id=7116037, text=string, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        context.bot.send_message(chat_id=7116037, text="Silent update pushing")
        for user in database.get_all_users():
            if not templates.check_diff(user[0], user[1]):
                string = templates.generate(user[1], user[0])
                database.to_file(string, user[0])
                desc = "A little update for one of your languages. You can also press reload in the desktop app."
                send(desc, context, user[0])


def update_global(update, _):
    query = update.callback_query
    query.edit_message_text("A new template? Neat. Please send me a description of it.")
    return bot.UPDATE_RECEIVE


def update_typo(update, context):
    query = update.callback_query
    query.edit_message_text("Great. Going to notify the users then \o/")
    for user in database.get_all_users():
        for user_langcode in user[1]["langcodes"]:
            if user_langcode == "en":
                string = templates.generate(user[1], user[0])
                database.to_file(string, user[0])
                desc = "A little update for one of your languages. You can also press reload in the desktop app."
                send(desc, context, user[0])
                break
    return bot.ConversationHandler.END


def update_receive(update, context):
    desc = update.message.text
    update.message.reply_text("Great, going to start the update phase :)")
    for user in database.get_all_users():
        if not templates.check_diff(user[0], user[1]):
            string = templates.generate(user[1], user[0])
            database.to_file(string, user[0])
            send(desc, context, user[0])
        else:
            context.job_queue.run_once(update_second_check, 2*60*60, context=desc, name=str(user[0]))

    return bot.ConversationHandler.END


def update_second_check(context):
    user_id = int(context.job.name)
    desc = context.job.context
    string = "Hey there, bot here. An update happend, but not all of your local translators were able to submit an " \
             "updated version of their templates in time. I will send you theirs once they submit it, for now, " \
             "enjoy this half-baked one"
    context.bot.send_message(chat_id=int(user_id), text=string)
    temp = templates.generate(database.get_user(user_id), user_id)
    send(desc, context, user_id, temp)


def send(desc, context, user_id, string=None):
    if string:
        document = io.BytesIO(string.encode('utf-8'))
    else:
        document = open(f"templates/tl_{str(user_id)}.txt", "rb")
    if len(desc) > 1024:
        context.bot.send_document(chat_id=int(user_id), document=document, filename="tl_multilanguage.txt")
        context.bot.send_message(chat_id=int(user_id), text=desc)
    else:
        context.bot.send_document(chat_id=int(user_id), document=document, filename="tl_multilanguage.txt",
                                  caption=desc)


def update_cancel(update, _):
    update.message.reply_text("Updating the templates cancelled.")
    return bot.ConversationHandler.END


def deep(update, context):
    jobs = context.job_queue.jobs()
    if jobs:
        for job in jobs:
            user_id = job.name
            user = database.get_user(user_id)
            if not templates.check_diff(user_id, user):
                string = templates.generate(user, user_id)
                database.to_file(string, user_id)
                send(job.context, context, user_id)
                job.schedule_removal()
    else:
        langcode = update.message.text
        for user in database.get_all_users():
            for user_langcode in user[1]["langcodes"]:
                if user_langcode == langcode:
                    string = templates.generate(user[1], user[0])
                    database.to_file(string, user[0])
                    desc = "A little update for one of your languages. You can also press reload in the desktop app."
                    send(desc, context, user[0])
                    break
