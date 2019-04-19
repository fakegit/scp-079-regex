# SCP-079-REGEX - Manage the regex patterns
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-REGEX.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
from copy import deepcopy

from pyrogram import InlineKeyboardMarkup, InlineKeyboardButton
from xeger import Xeger

from .. import glovar
from .etc import code, code_block, button_data, delay, random_str, send_data
from .files import save
from .telegram import send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)

# Xeger config
xg = Xeger(limit=32)


def data_exchange(client):
    receivers = glovar.update_to
    if glovar.update_type == "reload":
        exchange_text = send_data(
            sender="REGEX",
            receivers=receivers,
            operation="update",
            operation_type="reload",
            data=glovar.reload_path
        )
        delay(5, send_message, [client, glovar.exchange_id, exchange_text])
    else:
        exchange_text = send_data(
            sender="REGEX",
            receivers=receivers,
            operation="update",
            operation_type="download"
        )
        delay(5, send_document, [client, glovar.exchange_id, "data/compiled", exchange_text])


def re_compile(word_type):
    text = ""
    for word in eval(f"glovar.{word_type}_words"):
        text += word + "|"

    text = text[0:len(text) - 1]
    if text != "":
        glovar.compiled[word_type] = re.compile(text, re.I | re.S | re.M)
    else:
        glovar.compiled[word_type] = re.compile(f"预留{glovar.names[f'{word_type}']}词组 {random_str(16)}",
                                                re.I | re.M | re.S)

    save("compiled")
    save(f"{word_type}_words")


def words_add(word_type, word):
    # Check if the word already exits
    if word in eval(f"glovar.{word_type}_words"):
        text = (f"状态：{code('未添加')}\n"
                f"类别：{code(f'{glovar.names[word_type]}')}\n"
                f"词组：{code(word)}\n"
                f"原因：{code('已存在')}")
        markup = None
        return text, markup

    # Check if the pattern is correct
    try:
        pattern = re.compile(word, re.I | re.M | re.S)
    except Exception as e:
        text = (f"状态：{code('未添加')}\n"
                f"类别：{code(f'{glovar.names[word_type]}')}\n"
                f"词组：{code(word)}\n"
                f"原因：{code_block('出现错误')}\n"
                f"错误：{code_block(e)}")
        markup = None
        return text, markup

    # Check if the pattern is special
    for test in ["项脊轩，旧南阁子也。室仅方丈，可容一人居。",
                 "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                 "0123456789"
                 ]:
        if pattern.search(test):
            text = (f"状态：{code('未添加')}\n"
                    f"类别：{code(f'{glovar.names[word_type]}')}\n"
                    f"词组：{code(word)}\n"
                    f"原因：{code('不具有特殊性')}")
            markup = None
            return text, markup

    # Check similar patterns
    word_key = random_str(8)
    while word_key in glovar.ask_words:
        word_key = random_str(8)

    glovar.ask_words[word_key] = {
        "type": word_type,
        "new": word,
        "old": []
    }
    for old in eval(f"glovar.{word_type}_words"):
        if re.search(word, xg.xeger(old)) or re.search(old, xg.xeger(word)):
            glovar.ask_words[word_key]["old"].append(old)

    if glovar.ask_words[word_key]["old"]:
        text = ""
        for old in glovar.ask_words[word_key]["old"]:
            text += f"{code(old)}，"

        text = text[:-1]
        text = (f"状态：{code('未添加')}\n"
                f"类别：{code(f'{glovar.names[word_type]}')}\n"
                f"词组：{code(word)}\n"
                f"原因：{code('等待确认')}\n"
                f"重复：{text}")
        add_new = button_data("ask", "new", word_key)
        replace_all = button_data("ask", "replace", word_key)
        cancel = button_data("ask", "cancel", word_key)
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "另增新词",
                        callback_data=add_new
                    ),
                    InlineKeyboardButton(
                        "替换全部",
                        callback_data=replace_all
                    )
                ],
                [
                    InlineKeyboardButton(
                        "取消",
                        callback_data=cancel
                    )
                ]
            ]
        )
        return text, markup
    else:
        glovar.ask_words.pop(word_key, None)
        eval(f"glovar.{word_type}_words").add(word)
        re_compile(word_type)
        text = (f"状态：{code(f'已添加')}\n"
                f"类别：{code(f'{glovar.names[word_type]}')}\n"
                f"词组：{code(word)}")
        markup = None
        return text, markup


def words_ask(operation: str, word_key):
    if word_key in glovar.ask_words:
        word_type = glovar.ask_words[word_key]["type"]
        new_word = glovar.ask_words[word_key]["new"]
        old_words = glovar.ask_words[word_key]["old"]
        if operation == "new":
            eval(f"glovar.{word_type}_words").add(new_word)
            re_compile(word_type)
            text = (f"状态：{code(f'已添加')}\n"
                    f"类别：{code(f'{glovar.names[word_type]}')}\n"
                    f"词组：{code(new_word)}")
        elif operation == "replace":
            eval(f"glovar.{word_type}_words").add(new_word)
            for old in old_words:
                eval(f"glovar.{word_type}_words").discard(old)

            re_compile(word_type)
            replace_text = ""
            for old in glovar.ask_words[word_key]["old"]:
                replace_text += f"{code(old)}，"

            replace_text = replace_text[:-1]
            text = (f"状态：{code(f'已添加')}\n"
                    f"类别：{code(f'{glovar.names[word_type]}')}\n"
                    f"词组：{code(new_word)}\n"
                    f"替换：{replace_text}")
        else:
            text = (f"状态：{code(f'已取消')}\n"
                    f"类别：{code(f'{glovar.names[word_type]}')}\n"
                    f"词组：{code(new_word)}")

        glovar.ask_words.pop(word_key, None)
    else:
        text = (f"状态：{code('未添加')}\n"
                f"原因：{code('会话已失效')}")

    return text


def words_list(word_type, page):
    text = ""
    markup = None
    words = eval(f"glovar.{word_type}_words")
    if words:
        word = list(deepcopy(words))
        quo = int(len(words) / 50)
        if quo != 0:
            page_count = quo + 1
            if len(words) % 50 == 0:
                page_count = page_count - 1

            if page != page_count:
                word = word[(page - 1) * 50:page * 50]
            else:
                word = word[(page - 1) * 50:len(word)]
            if page_count > 1:
                if page == 1:
                    markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"第 {page} 页",
                                    callback_data=button_data("none")
                                ),
                                InlineKeyboardButton(
                                    ">>",
                                    callback_data=button_data("list", word_type, page + 1)
                                )
                            ]
                        ]
                    )
                elif page == page_count:
                    markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "<<",
                                    callback_data=button_data("list", word_type, page - 1)
                                ),
                                InlineKeyboardButton(
                                    f"第 {page} 页",
                                    callback_data=button_data("none")
                                )
                            ]
                        ]
                    )
                else:
                    markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "<<",
                                    callback_data=button_data("list", word_type, page - 1)
                                ),
                                InlineKeyboardButton(
                                    f"第 {page} 页",
                                    callback_data=button_data("none")
                                ),
                                InlineKeyboardButton(
                                    '>>',
                                    callback_data=button_data("list", word_type, page + 1)
                                )
                            ]
                        ]
                    )

        for w in word:
            text += f"{code(w)}，"

        text = text[:-1]
        text = (f"类别：{code(glovar.names[word_type])}\n"
                f"查询：{code('全部')}\n"
                f"结果：{text}")
    else:
        text = (f"类别：{code(glovar.names[word_type])}\n"
                f"查询：{code('全部')}\n"
                f"结果：{code('无法显示')}\n"
                f"原因：{code('没有找到')}")

    return text, markup


def words_remove(word_type, word):
    if word in eval(f"glovar.{word_type}_words"):
        eval(f"glovar.{word_type}_words").discard(word)
        re_compile(word_type)
        text = (f"状态：{code(f'已移除')}\n"
                f"类别：{code(f'{glovar.names[word_type]}')}\n"
                f"词组：{code(word)}")
        return text

    else:
        text = (f"状态：{code('未移除')}\n"
                f"原因：{code('不存在')}")
        return text