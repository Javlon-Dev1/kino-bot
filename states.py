from aiogram.fsm.state import StatesGroup, State


class AdminAddMovie(StatesGroup):
    waiting_video = State()
    waiting_title = State()


class AdminRemoveMovie(StatesGroup):
    waiting_code = State()


class AdminAddChannel(StatesGroup):
    waiting_channel = State()


class AdminRemoveChannel(StatesGroup):
    waiting_channel = State()


class UserSearchByCode(StatesGroup):
    waiting_code = State()


class UserSearchByTitle(StatesGroup):
    waiting_query = State()


class UserSubmitMovie(StatesGroup):
    waiting_video = State()
    waiting_title = State()
