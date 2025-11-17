from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_role_keyboard() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="🎓 Студент"), KeyboardButton(text="👨‍🏫 Преподаватель")]
		],
		resize_keyboard=True,
		one_time_keyboard=True
	)


def choose_of_action_user() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="👨‍🏫 Расписание на сегодня "),
			 KeyboardButton(text="👨‍🏫 Расписание на завтра "),
			 KeyboardButton(text="👨‍🏫 Расписание по дате ")]
		],
		resize_keyboard=True,
		one_time_keyboard=True
	)


def choose_of_action_admin() -> ReplyKeyboardMarkup:
	return ReplyKeyboardMarkup(
		keyboard=[
			[KeyboardButton(text="🎓 Загрузить расписание"),
			 KeyboardButton(text="👨‍🏫 Расписание на сегодня "),
			 KeyboardButton(text="👨‍🏫 Расписание по дате "), ]
		],
		resize_keyboard=True,
		one_time_keyboard=True
	)
