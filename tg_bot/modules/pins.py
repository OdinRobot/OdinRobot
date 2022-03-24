import html
from typing import Optional

from telegram import Bot, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters
from telegram.utils.helpers import mention_html

from tg_bot import SUDO_USERS, spamcheck, dispatcher

from .helper_funcs.chat_status import connection_status
from .helper_funcs.string_handling import escape_invalid_curly_brackets
from .log_channel import loggable
from .language import gs
from .helper_funcs.decorators import kigcmd, kigcallback
from .helper_funcs.parsing import Types, VALID_FORMATTERS, get_data, ENUM_FUNC_MAP, build_keyboard_from_list
from .sql.antilinkedchannel_sql import enable_linked
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.parsemode import ParseMode

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin,
)


@kigcmd(command="pinned", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
def pinned(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )

    chat = bot.getChat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        message_link = f"https://t.me/c/{str(chat.id)[4:]}/{pinned_id}"

        msg.reply_text(
            f"Click the button below to go to the pinned message in {html.escape(chat.title)}.",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="📌 Pinned Message",
                            url=message_link,
                        )
                    ]
                ]
            ),
        )

    else:
        msg.reply_text(
            f"There is no pinned message in <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )


@kigcmd(command="pin", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
def pin(update: Update, context: CallbackContext) -> Optional[str]:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    message_link = f"https://t.me/c/{str(chat.id)[4:]}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        msg.reply_text("Reply a message to pin it!")
        return

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() != "loud"
            or args[0].lower() != "violent"
        )
        
    message = update.effective_message
    pinner = chat.get_member(user.id)

    if (
        not (pinner.can_pin_messages or pinner.status == "creator")
        and user.id not in SUDO_USERS
    ):
        message.reply_text("You don't have the necessary rights to do that!")
        return

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            msg.reply_text(
                "I have pinned this message in <b>{}</b>!".format(html.escape(chat.title)),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 View Message", url=f"{message_link}"
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
            f"\n<b>Message:</b> <a href='{message_link}'>Pinned Message</a>\n"
        )

        return log_message


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
    unpinner = chat.get_member(user.id)

    if (
        not (unpinner.can_pin_messages or unpinner.status == "creator")
        and user.id not in SUDO_USERS
    ):
        message.reply_text("You don't have the necessary rights to do that!")
        return
    
    if not reply_msg:
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
        unpinthis = reply_msg.message_id
        try:
            bot.unpinChatMessage(chat.id, unpinthis)

            pinmsg = "https://t.me/c/{}/{}".format(str(chat.id)[4:], unpinthis)

            message.reply_text(
                "I have unpinned this message in <b>{}</b>!".format(html.escape(chat.title)),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 View Message", url=f"{pinmsg}"
                            ),
                        ]
                    ]
                )
            )
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


@kigcmd(command="permapin", run_async = True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
def permapin(update: Update, ctx: CallbackContext) -> Optional[str]:
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    bot = ctx.bot  # type: Optional[Bot]
    preview = True
    protect = False

    m = msg.text.split(' ', 1)
    if len(m) == 1 and not msg.reply_to_message:
        msg.reply_text("Provide something to pin.")
        return
    _, text, data_type, content, buttons = get_data(msg, True)
    if text == "":
        msg.reply_text("Should I pin... nothing?")
        return
    msg.delete()
    keyboard = InlineKeyboardMarkup(build_keyboard_from_list(buttons))

    if escape_invalid_curly_brackets(text, VALID_FORMATTERS):
        if "{admin}" in text and user_is_admin(update, user.id):
            return
        if "{user}" in text and not user_is_admin(update, user.id):
            return
        if "{preview}" in text:
            preview = False
        if "{protect}" in text:
            protect = True
        text = text.format(
                first = html.escape(msg.from_user.first_name),
                last = html.escape(
                        msg.from_user.last_name
                        or msg.from_user.first_name,
                ),
                fullname = html.escape(
                        " ".join(
                                [
                                    msg.from_user.first_name,
                                    msg.from_user.last_name or "",
                                ]
                        ),
                ),
                username = f'@{msg.from_user.username}'
                if msg.from_user.username
                else mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                mention = mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                chatname = html.escape(
                        msg.chat.title
                        if msg.chat.type != "private"
                        else msg.from_user.first_name,
                ),
                id = msg.from_user.id,
                user = "",
                admin = "",
                preview = "",
                protect = "",
        )

    else:
        text = ""

    try:
        if data_type in (Types.BUTTON_TEXT, Types.TEXT):
            pin_this = bot.send_message(
                chat.id,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=bool(preview),
                protect_content=bool(protect)
            )
        elif ENUM_FUNC_MAP[data_type] == dispatcher.bot.send_sticker:
            pin_this = ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                reply_markup=keyboard,
            )
        else:
            pin_this = ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                protect_content=bool(protect)
            )

        bot.pinChatMessage(chat.id, pin_this.message_id, disable_notification=False)

        enable_linked(chat.id)  # enable cleanlinked for this chat
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            f"\n<b>Message:</b> <a href='t.me/c/{str(chat.id)[4:]}''>Pinned Message</a>\n"
        )
        return log_message

    except BadRequest as excp:
        if excp.message == "Entity_mention_user_invalid":
            msg.reply_text(
                "Looks like you tried to mention someone I've never seen before. If you really "
                "want to mention them, forward one of their messages to me, and I'll be able "
                "to tag them!"
            )
        else:
            msg.reply_text(
                "Could not pin the message. Error: <code>{}</code>".format(
                    excp.message
                )
            )
        return


def get_help(chat):
    return gs(chat, "pins_help")

__mod_name__ = "Pins"
