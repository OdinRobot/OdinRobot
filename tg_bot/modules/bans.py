import html
from typing import Optional, Union

from telegram import Bot, Chat, ChatMember, Message, Update, ParseMode, User
from telegram.error import BadRequest
from telegram.ext import Filters, CallbackContext
from telegram.utils.helpers import mention_html

from tg_bot import (
    BAN_STICKER,
    DEV_USERS,
    MESSAGE_DUMP,
    MOD_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    OWNER_ID,
    SYS_ADMIN,
    WHITELIST_USERS,
    spamcheck,
    log
)

from .helper_funcs.chat_status import connection_status
from .helper_funcs.extraction import extract_user_and_text
from .helper_funcs.string_handling import extract_time
from .log_channel import loggable, gloggable
from .helper_funcs.decorators import kigcmd

def cannot_ban(banner_id, user_id, message) -> bool:
    if banner_id in DEV_USERS:
        if user_id not in DEV_USERS:
            return False
        else:
            message.reply_text("Why are you trying to ban another dev?")
            return True
    else:
        if user_id == OWNER_ID:
            message.reply_text("I'd never ban my owner.")
            return True
        elif user_id in DEV_USERS:
            message.reply_text("This user is one of my Devs, I can't act against our own.")
            return True
        elif user_id in SUDO_USERS:
            message.reply_text("My sudos are ban immune")
            return True
        # elif user_id in SUPPORT_USERS:
        #     message.reply_text("My support users are ban immune")
        #    return True
        elif user_id in WHITELIST_USERS:
            message.reply_text("Let one of my Devs fight a Whitelist user.")
            return True
        elif user_id in MOD_USERS:
            message.reply_text("Moderators cannot be banned, report abuse at @TheBotsSupport.")
            return True
        return False

ban_myself = "Oh yeah, ban myself, noob!"

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    bot_is_admin,
    user_is_admin,
    u_na_errmsg,
)


def ban_chat(bot: Bot, who: Chat, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.banChatSenderChat(where_chat_id, who.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("error banning channel {}:{} in {} because: {}".format(
                    who.title, who.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>Channel:</b> <a href=\"t.me/{who.username}\">{html.escape(who.title)}</a>"
        f"<b>Channel ID:</b> {who.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )


def ban_user(bot: Bot, who: ChatMember, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.banChatMember(where_chat_id, who.user.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("error banning user {}:{} in {} because: {}".format(
                    who.user.first_name, who.user.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>User:</b> <a href=\"tg://user?id={who.user.id}\">{html.escape(who.user.first_name)}</a>"
        f"<b>User ID:</b> {who.user.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )

def unban_chat(bot: Bot, who: Chat, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.unbanChatSenderChat(where_chat_id, who.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("error banning channel {}:{} in {} because: {}".format(
                    who.title, who.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>Channel:</b> <a href=\"t.me/{who.username}\">{html.escape(who.title)}</a>"
        f"<b>Channel ID:</b> {who.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )


def unban_user(bot: Bot, who: ChatMember, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.unbanChatMember(where_chat_id, who.user.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("error banning user {}:{} in {} because: {}".format(
                    who.user.first_name, who.user.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>User:</b> <a href=\"tg://user?id={who.user.id}\">{html.escape(who.user.first_name)}</a>"
        f"<b>User ID:</b> {who.user.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )


@kigcmd(command=['ban', 'dban', 'sban', 'dsban'], pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def ban(update: Update, context: CallbackContext) -> Optional[str]:  # sourcery no-metrics
    global delsilent
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    bot = context.bot

    if message.text.startswith(('/s', '!s', '>s')):
        silent = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("I don't have permission to delete messages here!")
            return
    else:
        silent = False
    if message.text.startswith(('/d', '!d', '>d')):
        delban = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("I don't have permission to delete messages here!")
            return
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("You don't have permission to delete messages here!")
            return
    else:
        delban = False
    if message.text.startswith(('/ds', '!ds', '>ds')):
        delsilent = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("I don't have permission to delete messages here!")
            return
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("You don't have permission to delete messages here!")
            return

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.is_automatic_forward:
            message.reply_text("This is a pretty bad idea, isn't it?")
            return

        if did_ban := ban_chat(bot, message.reply_to_message.sender_chat, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#BANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("Channel {} was banned successfully from {}".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("Failed to ban channel")
            return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return ''

    member = None
    chan = None
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        try:
            chan = bot.get_chat(user_id)
        except BadRequest as excp:
            if excp.message != "Chat not found":
                raise
            message.reply_text("Can't seem to find this person.")
            return ""

    if chan:
        if did_ban := ban_chat(bot, chan, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#BANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("Channel {} was banned successfully from {}".format(
                html.escape(chan.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("Failed to ban channel")
            return ""

    elif user_id == context.bot.id:
        message.reply_text(ban_myself)
        return ''

    elif cannot_ban(user.id, user_id, message):
        return ''
    
    elif user_is_admin(update, user_id) and user.id not in DEV_USERS:
        message.reply_text("This user has immunity and cannot be banned.")
        return ''

    elif did_ban := ban_user(bot, member, chat.id, reason = " ".join(args) or None):
        logmsg  = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        logmsg += did_ban

        message.reply_text("User {} was banned successfully from {}".format(
            mention_html(member.user.id, member.user.first_name),
            html.escape(chat.title),
        ),
            parse_mode="html"
        )

    else:
        message.reply_text("Failed to ban user")
        return ""

    if silent:
        if delsilent and message.reply_to_message:
            message.reply_to_message.delete()
        message.delete()
    elif delban and message.reply_to_message:
        message.reply_to_message.delete()
    context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker

    return logmsg


@kigcmd(command='tban', pass_args=True)
@connection_status
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        message.reply_text(ban_myself)
        return log_message

    elif cannot_ban(user.id, user_id, message):
        return ''
    
    elif user_is_admin(update, user_id) and user.id not in DEV_USERS:
        message.reply_text("This user has immunity and cannot be banned.")
        return ''

    if not reason:
        message.reply_text("You haven't specified a time to ban this user for!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP_BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.ban_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker

        if reason:
            bot.sendMessage(
                chat.id,
                f"Banned! User {mention_html(member.user.id, member.user.first_name)} will be banned for {time_val}.\nReason: {reason}",
                parse_mode=ParseMode.HTML,
            )

        else:
            bot.sendMessage(
                chat.id,
                f"Banned! User {mention_html(member.user.id, member.user.first_name)} will be banned for {time_val}.",
                parse_mode=ParseMode.HTML,
            )

        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                f"Banned! User will be banned for {time_val}.", quote=False
            )
            return log
        else:
            bot.sendMessage(MESSAGE_DUMP, str(update))
            bot.sendMessage(MESSAGE_DUMP, 
                "ERROR banning user {} in chat {} ({}) due to {}".format(
                user_id,
                chat.title,
                chat.id,
                excp.message)
            )
            message.reply_text("Well damn, I can't ban that user.")

    return log_message


@kigcmd(command=['kick', 'skick', 'dkick', 'dskick', 'punch'], pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def kick(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    silent = message.text[1] == 's' or message.text[2] == 's'
    delete = message.text[1] == 'd'
    if message.reply_to_message and message.reply_to_message.sender_chat:
        message.reply_text("This command doesn't work on channels, but I can ban them if u want.")
        return log_message

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Yeahhh I'm not gonna do that.")
        return log_message

    elif cannot_ban(user.id, user_id, message):
        return ''
    
    elif user_is_admin(update, user_id) and user.id not in DEV_USERS:
        message.reply_text("This user has immunity and cannot be banned.")
        return ''

    if delete and message.reply_to_message:
        if user_is_admin(update, message.from_user.id, perm=AdminPerms.CAN_DELETE_MESSAGES):
            if bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                message.reply_to_message.delete()
            else:
                update.effective_message.reply_text(
                    f"I can't perform this action due to missing permissions;\n"
                    f"Make sure i am an admin and {AdminPerms.CAN_DELETE_MESSAGES.name.lower().replace('is_', 'am ').replace('_', ' ')}!")
                return
        else:
            return u_na_errmsg(message, AdminPerms.CAN_DELETE_MESSAGES)


    if chat.unban_member(user_id):
        if not silent:
            bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
            if reason:
                bot.sendMessage(
                    chat.id,
                    f"{mention_html(member.user.id, member.user.first_name)} was kicked by {mention_html(user.id, user.first_name)} in {message.chat.title}\n<b>Reason</b>: <code>{reason}</code>",
                    parse_mode=ParseMode.HTML,
                )
            else:
                bot.sendMessage(
                    chat.id,
                    f"{mention_html(member.user.id, member.user.first_name)} was kicked by {mention_html(user.id, user.first_name)} in {message.chat.title}",
                    parse_mode=ParseMode.HTML,
                )

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        message.reply_text("Well damn, I can't kick that user.")

    return log_message


@kigcmd(command='kickme', pass_args=True, filters=Filters.chat_type.groups)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
@spamcheck
def kickme(update: Update, _: CallbackContext) -> Optional[str]:
    user_id = update.effective_message.from_user.id
    user = update.effective_message.from_user
    chat = update.effective_chat
    if user_is_admin(update, user_id):
        update.effective_message.reply_text("Haha you're stuck with us here.")
        return ''

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("*kicks you out of the group*")

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            "self kick"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
        )

        return log

    else:
        update.effective_message.reply_text("Huh? I can't :/")


@kigcmd(command='unban', pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def unban(update: Update, context: CallbackContext) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    bot = context.bot

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.is_automatic_forward:
            message.reply_text("This command doesn't work like this!")
            return

        if did_ban := unban_chat(bot, message.reply_to_message.sender_chat, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNBANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("Channel {} was unbanned successfully from {}".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("Failed to unban channel")
            return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return ''

    member = None
    chan = None
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        try:
            chan = bot.get_chat(user_id)
        except BadRequest as excp:
            if excp.message != "Chat not found":
                raise
            message.reply_text("Can't seem to find this person.")
            return ""

    if chan:
        if did_ban := unban_chat(bot, chan, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNBANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("Channel {} was unbanned successfully from {}".format(
                html.escape(chan.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("Failed to unban channel")
            return ""

    elif user_id == context.bot.id:
        message.reply_text(ban_myself)
        return ''

    # elif cannot_ban(user.id, user_id, message):
    #     return ''
    
    elif user_is_admin(update, user_id):
        message.reply_text("This user is an admin, so is not banned.")
        return ''

    elif member.status not in ["banned", "kicked"]:
        message.reply_text("This user isn't banned!")
        return ''

    elif did_ban := unban_user(bot, member, chat.id, reason = " ".join(args) or None):
        logmsg  = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        logmsg += did_ban

        message.reply_text("User {} was unbanned successfully from {}".format(
            mention_html(member.user.id, member.user.first_name),
            html.escape(chat.title),
        ),
            parse_mode="html"
        )

    else:
        message.reply_text("Failed to unban user")
        return ""

    return logmsg


WHITELISTED_USERS = [OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + WHITELIST_USERS


@kigcmd(command='selfunban', pass_args=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@gloggable
def selfunban(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in WHITELISTED_USERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Give a valid chat ID.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return
        else:
            raise

    if member.status not in ("left", "kicked"):
        message.reply_text("Aren't you already in the chat??")
        return

    chat.unban_member(user.id)
    message.reply_text("Yep, I have unbanned you.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log


from .language import gs


def get_help(chat):
    return gs(chat, "bans_help")


__mod_name__ = "Bans"
