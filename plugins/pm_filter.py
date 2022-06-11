#Kanged From @sachin9742s
import asyncio
import re
import ast
import pytz
import datetime

from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import(
   del_all,
   find_filter,
   get_filters,
)
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MODE = {}

now = datetime.datetime.now()
tz = pytz.timezone('asia/kolkata')
your_now = now.astimezone(tz)
hour = your_now.hour
if 0 <= hour <12:
    lallus = "Gᴏᴏᴅ ᴍᴏʀɴɪɴɢ"
elif 12 <= hour <15:
    lallus = 'Gᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ'
elif 15 <= hour <20:
    lallus = 'Gᴏᴏᴅ ᴇᴠᴇɴɪɴɢ'
else:
    lallus = 'Gᴏᴏᴅ ɴɪɢʜᴛ'

@Client.on_message(filters.group & filters.text & ~filters.edited & filters.incoming)
async def give_filter(client,message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)   

# Sticker ID
@Client.on_message(
    filters.private
    & ~filters.forwarded
    & ~filters.command(["start", "about", "help", "id"])
)
async def stickers(bot, msg):
    if msg.sticker:
        await msg.reply(f"This Sticker's ID is⚠️ `{msg.sticker.file_id}`", quote=True)
    

@Client.on_message(filters.command('autofilter'))
async def fil_mod(client, message):
      mode_on = ["yes", "on", "true"]
      mode_of = ["no", "off", "false"]

      try:
         args = message.text.split(None, 1)[1].lower()
      except:
         return await message.reply("Vro command is incomplete🥲.")

      m = await message.reply("🚀Processing...")

      if args in mode_on:
          FILTER_MODE[str(message.chat.id)] = "True"
          await m.edit("Auto filter enabled for this chat🎉")

      elif args in mode_of:
          FILTER_MODE[str(message.chat.id)] = "False"
          await m.edit("Auto filter disabled for this chat😴")
      else:
          await m.edit("Use: `/autofilter on` or `/autofilter off🥀`")

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):

    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("oKda", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.",show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    if SINGLE_BUTTON:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]

    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    btn.insert(0, 
        [
            InlineKeyboardButton(f'🔮 {search} 🔮', 'dupe')
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f'📁 Files: {len(files)}', 'dupe'),
            InlineKeyboardButton(f'💫 Tips', 'tips')
        ]
    )
    btn.insert(2,
        [
            InlineKeyboardButton(text="🤖 Support 🤖", url=f"https://t.me/+3wLXc3f1anM3NTU1")
        ]
    )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("𝙱𝙰𝙲𝙺", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"Pages {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append([InlineKeyboardButton(f"{round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages"), InlineKeyboardButton("𝙽𝙴𝚇𝚃", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("𝙱𝙰𝙲𝙺", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages"),
                InlineKeyboardButton("𝙽𝙴𝚇𝚃", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup( 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("⚠️ 𝙱𝚛𝚘. 𝚂𝚎𝚊𝚛𝚌𝚑 𝚈𝚘𝚞𝚛 𝙾𝚠𝚗 𝙵𝚒𝚕𝚎. 𝙳𝚘𝚗'𝚝 𝙲𝚕𝚒𝚌𝚔 𝙾𝚝𝚑𝚎𝚛𝚜 𝚁𝚎𝚚𝚞𝚎𝚜𝚝𝚎𝚍 𝙵𝚒𝚕𝚎𝚜. 🤒", show_alert=True)
    if movie_  == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.message_id)
    if not movies:
        return await query.answer("𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖠𝗀𝖺𝗂𝗇 𝖣𝗎𝖽𝖾, 𝖥𝗂𝗅𝖾 𝖫𝗂𝗇𝗄 𝖾𝗑𝗉𝗂𝗋𝖾𝖽.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('Checking for Movie in database...')
    k = await manual_filters(bot, query.message, text=movie)
    if k==False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            k = await query.message.edit('This Movie Not Found In DataBase')
            await asyncio.sleep(10)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid  = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):    
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!",show_alert=True)

    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Thats not for you!!",show_alert=True)


    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]
        
        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
                InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return

    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occured!!', parse_mode="md")
        return

    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text(
                f"Some error occured!!",
                parse_mode="md"
            )
        return
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occured!!",
                parse_mode="md"
            )
        return
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert,show_alert=True)

    if query.data.startswith("file"):
        FILE_CHANNEL_ID = int(-1001616427269)
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption=f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
            
        try:
            msg = await client.send_cached_media(
                chat_id=AUTH_CHANNEL,
                file_id=file_id,
                caption=f'<b>Hai 👋 {query.from_user.mention}</b> 😍\n\n<code>[KR.OTT] {title}</code>\n\n⚠️ <i>[𝐓𝐡𝐢𝐬 𝐟𝐢𝐥𝐞 𝐰𝐢𝐥𝐥 𝐛𝐞 𝐝𝐞𝐥𝐞𝐭𝐞𝐝 𝐟𝐨𝐫𝐦 𝐡𝐞𝐫𝐞 𝐰𝐢𝐭𝐡 𝐢𝐧 𝟏𝟎 𝐦𝐢𝐧𝐮𝐭𝐞 𝐚𝐬 𝐢𝐭 𝐡𝐚𝐬 𝐜𝐨𝐩𝐲𝐫𝐢𝐠𝐡𝐭...!!!](https://t.me/c/1555030497/75)</i>\n\n<i><b>⚡ Powered by:- {query.message.chat.title}</b></i>\n\n╔════ ᴊᴏɪɴ ᴡɪᴛʜ ᴜs ═════╗\n♻️ 𝙅𝙊𝙄𝙉 :- [𝙆𝙞𝙘𝙘𝙝𝙖 𝙊𝙏𝙏](t.me/Kiccha_OTT)\n♻️ 𝙅𝙊𝙄𝙉 :- [𝙆𝙞𝙘𝙘𝙝𝙖 𝙍𝙚𝙦𝙪𝙚𝙨𝙩](t.me/KicchaRequest)\n╚════ ᴊᴏɪɴ ᴡɪᴛʜ ᴜs ═════╝\n\n\n♡ ㅤ   ❍ㅤ     ⎙      ⌲\nˡᶦᵏᵉ  ᶜᵒᵐᵐᵉⁿᵗ  ˢᵃᵛᵉ   ˢʰᵃʳᵉ',
                protect_content=True if ident == "filep" else False 
            )
            msg1 = await query.message.reply(
                f'<b> Hai 👋 {query.from_user.mention} </b>😍\n\n<b>📫 Your File is Ready</b>\n\n'           
                f'<b>📂 Fɪʟᴇ Nᴀᴍᴇ</b> : <code>[KR.OTT] {title}</code>\n\n'              
                f'<b>⚙️ Fɪʟᴇ Sɪᴢᴇ</b> : <b>{size}</b>\n\n'
                f'<b>⚠️ 𝙏𝙝𝙞𝙨 𝙈𝙚𝙨𝙨𝙖𝙜𝙚 𝙒𝙞𝙡𝙡 𝘽𝙚 𝘿𝙚𝙡𝙚𝙩𝙚𝙙 𝘼𝙛𝙩𝙚𝙧 𝟏𝟎 𝙈𝙞𝙣𝙪𝙩𝙚𝙨…<b>\n\n'
                f'<b>♡ ㅤ   ❍ㅤ     ⎙      ⌲\nˡᶦᵏᵉ  ᶜᵒᵐᵐᵉⁿᵗ  ˢᵃᵛᵉ   ˢʰᵃʳᵉ',
                True,
                'html',
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('📥 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐋𝐢𝐧𝐤 📥 ', url = msg.link)
                        ],                       
                        [
                            InlineKeyboardButton("⚠️ 𝐂𝐚𝐧'𝐭 𝐀𝐜𝐜𝐞𝐬𝐬 ❓ 𝐂𝐥𝐢𝐜𝐤 𝐇𝐞𝐫𝐞 ⚠️", url=f'https://t.me/+7Cd6Sekyf6wyZjg1')
                        ]
                    ]
                )
            )
            await query.answer('Check Out The Chat',)
            await asyncio.sleep(600)
            await msg1.delete()
            await msg.delete()
            del msg1, msg
        except Exception as e:
            logger.exception(e, exc_info=True)
            await query.answer(f"Encountering Issues", True)

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒",show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(m = query.from_user.mention,lallus = lallus,file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
                size = size
                mention = mention
        if f_caption is None:
            f_caption = f"{title}"
        if size is None:
            size = f"{size}"
        if mention is None:
            mention = f"{mention}"


        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
            )
    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ', url='http://t.me/Prabhas_autofilterBOT?startgroup=true')
            ],[
            InlineKeyboardButton('ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.delete()
        if not START_IMAGE_URL:
            await query.message.reply(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
        else:
            await query.message.reply_photo(
                photo=START_IMAGE_URL,
                caption=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
                reply_markup=reply_markup
            )
        await query.answer('Lᴏᴀᴅɪɴɢ..........')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('𝙰𝙳𝙼𝙸𝙽', callback_data='admin'),
            InlineKeyboardButton('𝙲𝙾𝙽𝙽𝙴𝙲𝚃', callback_data='coct'),
            InlineKeyboardButton('𝙵𝙸𝙻𝚃𝙴𝚁', callback_data='auto_manual')
            ],[
            InlineKeyboardButton('𝙶𝚃𝚁𝙰𝙽𝚂', callback_data='gtrans'),
            InlineKeyboardButton('𝙸𝙽𝙵𝙾', callback_data='info'),
            InlineKeyboardButton('𝙿𝙰𝚂𝚃𝙴', callback_data='paste')
            ],[
            InlineKeyboardButton('𝙿𝚄𝚁𝙶𝙴', callback_data='purge'),
            InlineKeyboardButton('𝚁𝙴𝚂𝚃𝚁𝙸𝙲𝚃', callback_data='restric'),
            InlineKeyboardButton('𝚂𝙴𝙰𝚁𝙲𝙷', callback_data='search')
            ],[
            InlineKeyboardButton('𝚃𝙶𝚁𝙰𝙿𝙷', callback_data='tgraph'),
            InlineKeyboardButton('𝚆𝙷𝙾𝙸𝚂', callback_data='whois'),
            InlineKeyboardButton('𝙵𝚄𝙽', callback_data='fun')
            ],[
            InlineKeyboardButton('𝙰𝙻𝙸𝚅𝙴', callback_data='alive'),
            InlineKeyboardButton('𝚂𝙾𝙽𝙶', callback_data='song'),
            InlineKeyboardButton('𝙹𝚂𝙾𝙽', callback_data='json')
            ],[
            InlineKeyboardButton('𝙿𝙸𝙽', callback_data='pin'),
            InlineKeyboardButton('𝙲𝙾𝚁𝙾𝙽𝙰', callback_data='corona'),
            InlineKeyboardButton('𝚂𝚃𝙸𝙲𝙺𝙴𝚁𝙸𝙳', callback_data='stickerid')
            ],[
            InlineKeyboardButton('𝖯𝗂𝗇', callback_data='pin')
            ],[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "about":
        buttons= [[
            InlineKeyboardButton('status', callback_data='stats'),
            InlineKeyboardButton('source', callback_data='source')
            ],[
            InlineKeyboardButton('search movie', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('help & commands', callback_data='help')
            ],[
            InlineKeyboardButton('« Back', callback_data='start'),
            InlineKeyboardButton('Close ✗', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "alive":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.ALIVE_TXT,
            reply_markup=reply_markup,

parse_mode='html'
        )
    elif query.data == "whois":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.WHOIS_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "corona":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.CORONA_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "stickerid":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.STICKER_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "song":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.SONG_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "manualfilter":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='auto_manual'),
            InlineKeyboardButton('Buttons »', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.MANUALFILTER_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "json":
        buttons = [[ 
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.JSON_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "pin":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.PIN_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='manualfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='auto_manual')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "auto_manual":
        buttons = [[
            InlineKeyboardButton('auto', callback_data='autofilter'),

InlineKeyboardButton('manual', callback_data='manualfilter')

],[
            InlineKeyboardButton('« Back', callback_data='help'),
            InlineKeyboardButton('Close ✗', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.AUTO_MANUAL_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "fun":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='filter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.FUN_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )         
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "paste":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help'),
            InlineKeyboardButton('Close ✗', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.PASTE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "tgraph":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.TGRAPH_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "info":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.INFO_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "search":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.SEARCH_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "gtrans":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help'),
            InlineKeyboardButton('lang codes', url='https://cloud.google.com/translate/docs/languages')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.GTRANS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "zombies":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.ZOMBIES_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "purge":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.PURGE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "restric":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        await query.message.edit_text(
            text=script.RESTRIC_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='about'),
            InlineKeyboardButton('Refresh ⧖', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▢▢▢▢▢▢▢▢▢")
        n=await m.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▢▢▢▢▢▢▢")
        o=await n.edit("𝗟𝗼𝗮𝗱𝗶𝗻𝗴▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )


    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='about'),
            InlineKeyboardButton('Refresh ⧖', callback_data='rfrsh')
        ]]
    

async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if SPELL_CHECK_REPLY:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message # msg will be callback query
        search, files, offset, total_results = spoll
    if SINGLE_BUTTON:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'files#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    btn.insert(0, 
        [
            InlineKeyboardButton(f'🔮 {search} 🔮', 'dupe')
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f'📁 Files: {len(files)}', 'dupe'),
            InlineKeyboardButton(f'💫 Tips', 'tips')
        ]
    )
    btn.insert(2,
        [
            InlineKeyboardButton(text="🤖 Support 🤖", url=f"https://t.me/+3wLXc3f1anM3NTU1")
        ]
    )

    if offset != "":
        key = f"{message.chat.id}-{message.message_id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"1/{round(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="𝙽𝙴𝚇𝚃",callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="1/1",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if IMDB else None
    if imdb:
        cap = IMDB_TEMPLATE.format(
            query = search, 
            title = imdb['title'], 
            votes = imdb['votes'], 
            aka = imdb["aka"],
            seasons = imdb["seasons"],
            box_office = imdb['box_office'], 
            localized_title = imdb['localized_title'],
            kind = imdb['kind'], 
            imdb_id = imdb["imdb_id"], 
            cast = imdb["cast"], 
            runtime = imdb["runtime"], 
            countries = imdb["countries"],
            certificates = imdb["certificates"], 
            languages = imdb["languages"],
            director = imdb["director"], 
            writer = imdb["writer"], 
            producer = imdb["producer"], 
            composer = imdb["composer"], 
            cinematographer = imdb["cinematographer"], 
            music_team = imdb["music_team"], 
            distributors = imdb["distributors"],
            release_date = imdb['release_date'], 
            year = imdb['year'],
            genres = imdb['genres'], 
            poster = imdb['poster'],
            plot = imdb['plot'],
            rating = imdb['rating'], 
            url = imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>Hai 👋 {message.from_user.mention}</b> 😍\n\n<b>📁 Found ✨  Files For Your Query : {search} 👇</b> "
    if imdb and imdb.get('poster'):
        try:
            await message.reply_photo(photo=imdb.get('poster'), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            await message.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    if spoll:
        await msg.message.delete()
        

async def advantage_spell_chok(msg):
    query = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)", "", msg.text, flags=re.IGNORECASE) # plis contribute some common words 
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("I couldn't find any movie in that name.")
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE) # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)', '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*", re.IGNORECASE) # match something like Watch Niram | Amazon Prime 
        for mv in g_s:
            match  = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed)) # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True) # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist)) # removing duplicates
    if not movielist:
        k = await msg.reply("I couldn't find anything related to that. Check your spelling")
        await asyncio.sleep(8)
        await k.delete()
        return
    SPELL_CHECK[msg.message_id] = movielist
    btn = [[
                InlineKeyboardButton(
                    text=movie.strip(),
                    callback_data=f"spolling#{user}#{k}",
                )
            ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    await msg.reply("I couldn't find anything related to that\nDid you mean any one of these?", reply_markup=InlineKeyboardMarkup(btn))
    

async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id, 
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id = reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id = reply_id
                        )
                    else:
                        button = eval(btn) 
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id = reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
