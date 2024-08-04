import logging


from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from linode_api import LinodeAPI, ShadowsocksStackscriptData, Region

from settings import STACKSCRIPT_ID, SHADOWSOCKS_PASSWORD, LINODE_API_KEY


logger = logging.getLogger(__name__)

# Confirmation keyboard
confirm_inline_builder = InlineKeyboardBuilder()
confirm_inline_builder.button(
    text="Confirm",
    callback_data="confirm",
)
confirm_inline_builder.button(
    text="Back",
    callback_data="back",
)

# Region keyboard
region_inline_builder = InlineKeyboardBuilder()
buttons = [
    InlineKeyboardButton(text=region.name, callback_data=region.value)
    for region in Region
]
for i in range(0, len(buttons), 2):
    region_inline_builder.row(*buttons[i : i + 2])
region_inline_builder.row(InlineKeyboardButton(text="Back", callback_data="back"))

# Spawning
spawn_router = Router()


class Spawn(StatesGroup):
    region = State()
    confirm = State()


# Step 0: spawn entry
@spawn_router.message(Command("spawn"))
async def command_spawn(message: Message, state: FSMContext) -> None:
    linode_api = LinodeAPI(LINODE_API_KEY)
    linodes = linode_api.list_linodes_all()
    vpn_linodes = [
        linode for linode in linodes if linode.label.lower().startswith("vpn-bot")
    ]
    if len(vpn_linodes) >= 3:
        await message.answer(
            "You can't spawn more than 3 Linodes. Delete some with /delete"
        )
        return

    await state.set_state(Spawn.region)
    await message.answer(
        "Choose region",
        reply_markup=region_inline_builder.as_markup(),
    )


# Step 1: Choose region
@spawn_router.callback_query(Spawn.region)
async def handle_region(query: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(query.message, Message):
        return
    if query.data == "back":
        await state.clear()
        await query.message.delete()
        return

    await state.update_data(region=query.data)
    await state.set_state(Spawn.confirm)

    await query.message.edit_text(f"Do you confirm linode creation in {query.data}?")
    await query.message.edit_reply_markup(
        reply_markup=confirm_inline_builder.as_markup()
    )


# Step 3: Confirm creation
@spawn_router.callback_query(Spawn.confirm)
async def confirm_creation(query: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(query.message, Message):
        return

    if query.data == "back":
        await state.set_state(Spawn.region)
        await query.message.edit_text("Choose region")
        await query.message.edit_reply_markup(
            reply_markup=region_inline_builder.as_markup()
        )
        return

    data = await state.get_data()
    if not (region := data.get("region")):
        await query.message.answer(
            "Something went wrong!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    linode_api = LinodeAPI(LINODE_API_KEY)
    response = linode_api.create_linode(
        region,
        label=f"vpn-bot-{query.id}",
        stackscript_id=STACKSCRIPT_ID,
        stackscript_data=ShadowsocksStackscriptData(PASSWORD=SHADOWSOCKS_PASSWORD),
    )

    if response.status_code != 200:
        logger.error(response.text)
        await query.message.answer(
            "Something went wrong!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    ipv4 = "\n".join(response.json().get("ipv4"))

    await state.clear()
    await query.message.answer(
        f"Successfully created Linode ID {response.json().get('id')}! Wait 3-5 minutes to start.\n{ipv4}",
        reply_markup=ReplyKeyboardRemove(),
    )


### Listing


@spawn_router.message(Command("list"))
async def command_list(message: Message, state: FSMContext) -> None:
    linode_api = LinodeAPI(LINODE_API_KEY)
    linodes = linode_api.list_linodes_all()

    msg = "Linodes:\n\n"
    for linode in linodes:
        if not linode.label.lower().startswith("vpn-bot"):
            continue
        msg += str(linode)
        msg += "\n\n"

    await message.answer(msg)


### Deleting

# Spawning
delete_router = Router()


class Delete(StatesGroup):
    linode = State()
    confirm = State()


@spawn_router.message(Command("delete"))
async def command_delete(message: Message, state: FSMContext) -> None:
    linode_api = LinodeAPI(LINODE_API_KEY)
    linodes = linode_api.list_linodes_all()

    # Server keyboard
    linode_inline_builder = InlineKeyboardBuilder()
    buttons = [
        InlineKeyboardButton(
            text=f"{linode.id} {linode.region}", callback_data=str(linode.id)
        )
        for linode in linodes
        if linode.label.lower().startswith("vpn-bot")
    ]
    for button in buttons:
        linode_inline_builder.row(button)
    linode_inline_builder.row(InlineKeyboardButton(text="Back", callback_data="back"))

    await state.set_state(Delete.linode)
    await message.answer(
        "Choose linode to delete",
        reply_markup=linode_inline_builder.as_markup(),
    )


# Step 1: Choose linode
@spawn_router.callback_query(Delete.linode)
async def handle_server(query: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(query.message, Message):
        return

    if query.data == "back":
        await state.clear()
        await query.message.delete()
        return

    await state.update_data(linode=query.data)
    await state.set_state(Delete.confirm)

    await query.message.edit_text(f"Do you confirm deletion Linode ID {query.data}?")
    await query.message.edit_reply_markup(
        reply_markup=confirm_inline_builder.as_markup()
    )


# Step 2: Confirm deletion
@spawn_router.callback_query(Delete.confirm)
async def confirm_deletion(query: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(query.message, Message):
        return

    if query.data == "back":
        await state.clear()
        await query.message.delete()
        return

    data = await state.get_data()
    if not (linode_id := data.get("linode")):
        await query.message.answer(
            "Something went wrong!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    linode_api = LinodeAPI(LINODE_API_KEY)
    success = linode_api.delete_linode(int(linode_id))

    if not success:
        await query.message.answer(
            "Something went wrong!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await state.clear()
    await query.message.answer(
        f"Successfully deleted Linode ID {linode_id}",
        reply_markup=ReplyKeyboardRemove(),
    )
