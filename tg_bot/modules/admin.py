import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from telegram.utils.helpers import mention_html
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.types import ChannelParticipantCreator
from tg_bot import telethn

from tg_bot import spamcheck
from .helper_funcs.chat_status import connection_status

from .helper_funcs.extraction import extract_user, extract_user_and_text
from .log_channel import loggable
from .language import gs
from .helper_funcs.decorators import kigcmd, register

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)

from typing import Optional


@kigcmd(command="fullpromote", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS, allow_mods = True)
@loggable
def fullpromote(update, context):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    bot, args = context.bot, context.args

    if user_can_promote(chat, user, bot.id) is False:
        message.reply_text("You don't have enough rights to promote someone!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("mention one.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status in ["administrator", "creator"]:
        message.reply_text("This person is already an admin...!")
        return ""

    if user_id == bot.id:
        message.reply_text("I hope, if i could promote myself!")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(
        chat.id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_promote_members=bot_member.can_promote_members,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
        can_manage_voice_chats=bot_member.can_manage_voice_chats,
    )

    title = "admin"
    if " " in message.text:
        title = message.text.split(" ", 1)[1]
        if len(title) > 16:
            message.reply_text(
                "The title length is longer than 16 characters.\nTruncating it to 16 characters."
            )

        try:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)

        except BadRequest:
            message.reply_text(
                "I can't set custom title for admins that I didn't promote!"
            )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="⏬ Demote",
                    callback_data="demote_({})".format(user_member.user.id),
                ),
                InlineKeyboardButton(text="🔄 Cache", callback_data="close2"),
            ]
        ]
    )
    message.reply_text(
        f"♔ {chat.title} Event!\n"
        f"• A new admin has been appointed as Fully Promoted!\n"
        f"• Let's all welcome {mention_html(user_member.user.id, user_member.user.first_name)}",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#FULLPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )


close_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔄 Cache", callback_data="close2")]]
)

@kigcmd(command="promote", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS, allow_mods = True)
@loggable
def promote(update: Update, context: CallbackContext) -> Optional[str]:
    chat_id = update.effective_chat.id
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    bot, args = context.bot, context.args

    if user_can_promote(chat, user, bot.id) is False:
        message.reply_text("You don't have enough rights to promote someone!")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("Mention one.... 🤷🏻‍♂.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status in ["administrator", "creator"]:
        message.reply_text("This person is already an admin...!")
        return ""

    if user_id == bot.id:
        message.reply_text("I hope, if i could promote myself!")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(
        chat_id,
        user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
    )

    title = "admin"
    if " " in message.text:
        title = message.text.split(" ", 1)[1]
        if len(title) > 16:
            message.reply_text(
                "The title length is longer than 16 characters.\nTruncating it to 16 characters."
            )

        try:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)

        except BadRequest:
            message.reply_text(
                "I can't set custom title for admins that I didn't promote!"
            )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="⏬ Demote",
                    callback_data="demote_({})".format(user_member.user.id),
                ),
                InlineKeyboardButton(text="🔄 Cache", callback_data="close2"),
            ]
        ]
    )
    message.reply_text(
        f"♔ {chat.title} Event!\n"
        f"• A new admin has been appointed!\n"
        f"• Let's all welcome {mention_html(user_member.user.id, user_member.user.first_name)}",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )
    # refresh admin cache
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass
    return (
        "<b>{}:</b>"
        "\n#PROMOTED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(user_member.user.id, user_member.user.first_name),
        )
    )


close_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("🔄 Cache", callback_data="close2")]]
)


@kigcmd(command="demote", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS, allow_mods = True)
@loggable
def demote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text(f"Error: {e}")
        return

    if user_member.status == "creator":
        message.reply_text("This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        message.reply_text("This user isn't an admin!")
        return

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
            is_anonymous=False,
        )
        bot.sendMessage(
            chat.id,
            "<b>{}</b> was demoted{}.".format(
                    user_member.user.first_name or user_id,
                    f' by <b>{message.from_user.first_name}</b>' if not message.sender_chat else ''
            ),
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        message.reply_text(
            f"Could not demote!\n{str(e)}"
        )
        return

@kigcmd(command="title", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS, allow_mods = True)
@loggable
def set_title(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        user_id = user.id
        title = " ".join(args)

    try:
        user_member = chat.get_member(user_id)
    except:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    if user_member.status == "creator" and user_id == user.id:
        message.reply_text(
            "Okay -_-"
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "This person is the chat CREATOR, only they can set their title."
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "Titles can only be set to admins."
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "I can't set my own title myself! Get the one who made me admin to do it for me."
        )
        return

    if not title:
        message.reply_text("You can't set an empty title!")
        return

    if len(title) > 16:
        message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("I can only set titles for the admins I promote!")
        return

    bot.sendMessage(
        chat.id,
        f"Successfully set title for <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ADMIN\nTitle set\n"
        f"<b>By Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>To Admin:</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
        f"<b>New Title:</b> '<code>{html.escape(title[:16])}</code>'"

    )
    return log_message


@kigcmd(command=["invitelink", "link"], can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_INVITE_USERS)
@user_admin_check(AdminPerms.CAN_INVITE_USERS, allow_mods = True)
@loggable
def invite(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ADMIN\nInvite link exported\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Invite Link:</b> '<code>{invitelink}</code>'"

            )
            return log_message

        else:
            update.effective_message.reply_text(
                "I don't have access to the invite link, try changing my permissions!"
            )
    else:
        update.effective_message.reply_text(
            "I can only give you invite links for supergroups and channels, sorry!"
        )


@register(pattern="(admin|admins|staff|adminlist)", groups_only=True, no_args=True)
async def adminList(event):
    try:
        _ = event.chat.title
    except:
        return

    temp = await event.reply("Fetching full admins list..")
    text = "Admins in **{}**".format(event.chat.title)

    admn = telethn.iter_participants(
        event.chat_id, 50, filter=ChannelParticipantsAdmins)

    creator = ""
    admin = []
    bots = []

    async for user in admn:

        if isinstance(user.participant, ChannelParticipantCreator):

            if user.first_name == "":
                name = "☠ Zombie"
            else:
                name = "[{}](tg://user?id={})".format(user.first_name.split()[0], user.id)
            creator = "\nㅤㅤ• {}".format(name)
        elif user.bot:
            if user.first_name == "":
                name = "☠ Zombie"
            else:
                name = "[{}](tg://user?id={})".format(user.first_name, user.id)  # .split()[0] bots names arent long ig?
            bots.append("\nㅤㅤ• {}".format(name))

        else:
            try:
                if user.participant.admin_rights.is_anonymous:
                    continue
            except:
                pass

            try:
                if not user.first_name or user.deleted:
                    continue
                else:
                    name = "[{}](tg://user?id={})".format(user.first_name, user.id)
            except AttributeError:
                pass
            admin.append("\nㅤㅤ• {}".format(name))

    text += "\nㅤ**Creator:**"

    text += creator

    text += f"\nㅤ**Admins:** {len(admin)}"

    text += "".join(admin)

    text += f"\nㅤ**Bots:** {len(bots)}"

    text += "".join(bots)

    members = await telethn.get_participants(event.chat_id)
    mm = len(members)

    text += "\n**Members:** {}".format(mm)
    text += "\n**Note:** these values are up to date"

    await temp.edit(text, parse_mode="markdown")


def get_help(chat):
    return gs(chat, "admin_help")


__mod_name__ = "Admin"

