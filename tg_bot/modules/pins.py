import html


from telegram import Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters
from telegram.utils.helpers import mention_html

from tg_bot import SUDO_USERS, spamcheck, dispatcher

from .helper_funcs.chat_status import connection_status
from .log_channel import loggable
from .language import gs
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback
from .helper_funcs.misc import get_message_type,\
    build_keyboard_alternate
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from .connection import connected
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.parsemode import ParseMode

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)

@kigcmd(command="pin", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        msg.reply_text("Reply a message to pin it!")
        return

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            msg.reply_text(
                "Success! Pinned this message on this group",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 View Messages", url=f"{message_link}"
                            ),
                            InlineKeyboardButton(
                                text="❌ Delete", callback_data="close2"
                            ),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


close_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("❌ Delete", callback_data="close2")]]
)


@kigcmd(command="unpin", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    message = update.effective_message



    reply_msg = message.reply_to_message
    if not reply_msg:
        print("not rp")
        try:
            bot.unpinChatMessage(chat.id)
            dispatcher.bot.sendMessage(chat.id, "Unpinned the last pinned message successfully!", parse_mode=ParseMode.MARKDOWN)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"I couldn't unpin the message from some reason.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNPINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message

    else:
        print("rp")
        unpinthis = reply_msg.message_id
        try:
            bot.unpinChatMessage(chat.id, unpinthis)

            if chat.username:
                pinmsg = "https://t.me/{}/{}".format(chat.username, unpinthis)
            else:
                pinmsg = "https://t.me/c/{}/{}".format(str(chat.id)[4:], unpinthis)

            dispatcher.bot.sendMessage(chat.id, "I have unpinned [this message]({})".format(pinmsg), parse_mode=ParseMode.MARKDOWN)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"I couldn't unpin the message from some reason.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNPINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message

@kigcmd(command="unpinall", filters=Filters.chat_type.groups)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@spamcheck
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Only the chat owner can unpin all messages at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Unpin all messages", callback_data="pinned_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="pinned_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"Are you sure you would like unpin all pinned messages in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )

@kigcallback(pattern=r"pinned_.*")
@loggable
def unpin_callback(update, context: CallbackContext) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    bot = context.bot
    member = chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "pinned_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:

            try:
                bot.unpinAllChatMessages(chat.id)
            except BadRequest as excp:
                if excp.message == "Chat_not_modified":
                    pass
                else:
                    raise
            msg.edit_text(f"Unpinned all messages in {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNPINNED_ALL\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        else:
            query.answer("Only owner of the chat can do this.")
            return ""

    elif query.data == "pinned_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("Unpinning all pinned messages has been cancelled.")
            return ""
        else:
            query.answer("Only owner of the chat can do this.")
            return ""




# cherry-picked from emilia hikari (https://github.com/AyraHikari/EmiliaHikari)
# commits:
# 4ad807aa1d9615993db0e135d910d70bc4cbf767
# 049e735dd51694ae736749b9c9523499aaca8862
# cb9194dffc588c564f3dd6bdf75c1e712dc05e59
# ab26b958adca851eb749398d1683280896cfb633
# 94348c615c5364c13d32393d588838eaf1501f59
# ab26b958adca851eb749398d1683280896cfb633


ENUM_FUNC_MAP = {
	'Types.TEXT': dispatcher.bot.send_message,
	'Types.BUTTON_TEXT': dispatcher.bot.send_message,
	'Types.STICKER': dispatcher.bot.send_sticker,
	'Types.DOCUMENT': dispatcher.bot.send_document,
	'Types.PHOTO': dispatcher.bot.send_photo,
	'Types.AUDIO': dispatcher.bot.send_audio,
	'Types.VOICE': dispatcher.bot.send_voice,
	'Types.VIDEO': dispatcher.bot.send_video
}

@kigcmd(command="permapin", filters=Filters.chat_type.groups, run_async=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
def permapin(update, context):

    message = update.effective_message  # type: Optional[Message]

    chat_id = update.effective_chat.id

    text, data_type, content, buttons = get_message_type(message)
    tombol = build_keyboard_alternate(buttons)
    try:
        message.delete()
    except BadRequest:
        pass
    if str(data_type) in ('Types.BUTTON_TEXT', 'Types.TEXT'):
        try:
            sendingmsg = context.bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN,
                                 disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(tombol))
        except BadRequest:
            context.bot.send_message(chat_id, "Incorrect markdown text!\nIf you don't know what markdown is, please send `/markdownhelp` in PM.", parse_mode=ParseMode.MARKDOWN)
            return
    else:
        sendingmsg = ENUM_FUNC_MAP[str(data_type)](chat_id, content, caption=text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(tombol))
    if sendingmsg is None:
        context.bot.send_message(chat_id, "Specify what to pin!")
        
    try:
        context.bot.pinChatMessage(chat_id, sendingmsg.message_id)
    except BadRequest:
        context.bot.send_message(chat_id, "I don't have access to message pins!")


def get_help(chat):
    return gs(chat, "pins_help")

__mod_name__ = "Pins"
