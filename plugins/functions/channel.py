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
from time import sleep
from typing import List

from pyrogram import Client

from .. import glovar
from .etc import crypt_str, delay, format_data, thread
from .file import crypt_file
from .telegram import send_document, send_message


# Enable logging
logger = logging.getLogger(__name__)


def share_data(client: Client, sender: str, receivers: List[str], action: str, action_type: str, data=None) -> bool:
    # Use this function to share data in exchange channel
    try:
        text = format_data(
            sender=sender,
            receivers=receivers,
            action=action,
            action_type=action_type,
            data=data
        )
        thread(send_message, (client, glovar.exchange_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_regex_update(client: Client) -> bool:
    try:
        receivers = glovar.update_to
        if glovar.update_type == "reload":
            exchange_text = share_data(
                client=client,
                sender="REGEX",
                receivers=receivers,
                action="update",
                action_type="reload",
                data=crypt_str("encrypt", glovar.reload_path, glovar.key)
            )
            delay(5, send_message, [client, glovar.exchange_channel_id, exchange_text])
        else:
            exchange_text = share_data(
                client=client,
                sender="REGEX",
                receivers=receivers,
                action="update",
                action_type="download",
                data=crypt_str("encrypt", glovar.reload_path, glovar.key)
            )
            sleep(5)
            crypt_file("encrypt", "data/compiled", "tmp/compiled")
            thread(send_document, (client, glovar.exchange_channel_id, "tmp/compiled", exchange_text))

        return True
    except Exception as e:
        logger.warning(f"Data exchange error: {e}", exc_info=True)

    return False
