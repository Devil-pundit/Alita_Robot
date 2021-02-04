from io import BytesIO
from datetime import datetime
from alita.db import antispam_db as db
from alita.__main__ import Alita
from pyrogram import filters, errors
from pyrogram.types import Message
from alita import SUPPORT_STAFF, MESSAGE_DUMP, PREFIX_HANDLER, SUPPORT_GROUP, LOGGER
from alita.utils.custom_filters import sudo_filter
from alita.utils.extract_user import extract_user
from alita.utils.parser import mention_html


@Alita.on_message(filters.command(["jban", "justiceban"], PREFIX_HANDLER) & sudo_filter)
async def gban(c: Alita, m: Message):

    if len(m.text.split()) == 1:
        await m.reply_text("<b>How to jban?</b>\n<b>Answer:</b> `/jban user_id reason`")
        return

    if len(m.text.split()) == 2 and not m.reply_to_message:
        await m.reply_text("Please enter a reason to jban user!")
        return

    user_id, user_first_name = extract_user(m)
    me = await c.get_me()

    if m.reply_to_message:
        gban_reason = m.text.split(None, 1)[1]
    else:
        gban_reason = m.text.split(None, 2)[2]

    if user_id in SUPPORT_STAFF:
        await m.reply_text(f"This user is part of support users!, Can't ban our own!")
        return

    if user_id == me.id:
        await m.reply_text("You can't gban me nigga!\nNice Try...!")
        return

    if db.is_user_gbanned(user_id):
        old_reason = db.update_gban_reason(user_id, user_first_name, gban_reason)
        await m.reply_text(
            (
                f"Updated Jban reason to: `{gban_reason}`.\n"
                f"Old Reason was: `{old_reason}`"
            )
        )
        return

    db.gban_user(user_id, user_first_name, gban_reason)
    await m.reply_text(
        (
            f"Added {user_first_name} to Justice Ban List.\n"
            "They will now be banned in all groups where I'm admin!"
        )
    )
    log_msg = (
        f"#JBAN\n"
        f"<b>Originated from:</b> {m.chat.id}\n"
        f"<b>Admin:</b> {mention_html(m.from_user.first_name, m.from_user.id)}\n"
        f"<b>Jbanned User:</b> {mention_html(user_first_name, user_id)}\n"
        f"<b>Jbanned User ID:</b> {user_id}\n"
        f"<b>Event Stamp:</b> {datetime.utcnow().strftime('%H:%M - %d-%m-%Y')}"
    )
    await c.send_message(MESSAGE_DUMP, log_msg)
    try:
        # Send message to user telling that he's gbanned
        await c.send_message(
            user_id,
            (
                "You have been added to my justice ban list!\n"
                f"Reason: `{gban_reason}`\n\n"
                f"Appeal Chat: @{SUPPORT_GROUP}"
            ),
        )
    except:  # TO DO: Improve Error Detection
        pass
    return


@Alita.on_message(
    filters.command(["unjban", "unjusticeban", "justiceunban"], PREFIX_HANDLER)
    & sudo_filter
)
async def ungban(c: Alita, m: Message):

    if len(m.text.split()) == 1:
        await m.reply_text("Pass a user id or username as an argument!")
        return

    user_id, user_first_name = extract_user(m)
    me = await c.get_me()

    if user_id in SUPPORT_STAFF:
        await m.reply_text("They can't be banned, so how am I supposed to unjban them?")
        return

    if user_id == me.id:
        await m.reply_text("Nice Try...!")
        return

    if db.is_user_gbanned(user_id):
        db.ungban_user(user_id)
        await m.reply_text(f"Removed {user_first_name} from Justice Ban List.")
        log_msg = (
            f"#UNJBAN\n"
            f"<b>Originated from:</b> {m.chat.id}\n"
            f"<b>Admin:</b> {mention_html(m.from_user.first_name, m.from_user.id)}\n"
            f"<b>UnJbanned User:</b> {mention_html(user_first_name, user_id)}\n"
            f"<b>UnJbanned User ID:</b> {user_id}\n"
            f"<b>Event Stamp:</b> {datetime.utcnow().strftime('%H:%M - %d-%m-%Y')}"
        )
        await c.send_message(MESSAGE_DUMP, log_msg)
        try:
            # Send message to user telling that he's ungbanned
            await c.send_message(
                user_id, "You have been removed from my justice ban list!\n"
            )
        except:  # TO DO: Improve Error Detection
            pass
        return

    await m.reply_text("User is not jbanned!")
    return


@Alita.on_message(
    filters.command(["jbanlist", "justicebanlist"], PREFIX_HANDLER) & sudo_filter
)
async def gban_list(c: Alita, m: Message):
    banned_users = db.get_gban_list()

    if not banned_users:
        await m.reply_text("There aren't any jbanned users...!")
        return

    banfile = "Banned geys!.\n"
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "jbanlist.txt"
        await m.reply_document(
            document=output,
            caption="Here is the list of currently jbanned users.",
        )

        return


@Alita.on_message(filters.group, group=6)
async def gban_watcher(c: Alita, m: Message):
    try:
        if db.is_user_gbanned(m.from_user.id):
            try:
                await c.kick_chat_member(m.chat.id, m.from_user.id)
                await m.reply_text(
                    (
                        f"This user ({mention_html(m.from_user.first_name, m.from_user.id)}) "
                        "has been banned judicially!\n\n"
                        f"To get unbanned appeal at @{SUPPORT_GROUP}"
                    ),
                )
                LOGGER.info(f"Banned user {m.from_user.id} in {m.chat.id}")
                return
            except (errors.ChatAdminRequired or errors.UserAdminInvalid):
                # Bot not admin in group and hence cannot ban users!
                # TO-DO - Improve Error Detection
                LOGGER.info(
                    f"User ({m.from_user.id}) is admin in group {m.chat.name} ({m.chat.id})"
                )
                pass
            except Exception as excp:
                await c.send_message(
                    MESSAGE_DUMP,
                    f"<b>Jban Watcher Error!</b>\n<b>Chat:</b> {m.chat.id}\n<b>Error:</b> `{excp}`",
                )
    except AttributeError:
        pass  # Skip attribute errors!
    return
