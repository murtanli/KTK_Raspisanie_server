from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
	waiting_for_role = State()
	waiting_for_group = State()
	waiting_for_teacher_name = State()


class DownloadSchedule(StatesGroup):
	waitind_for_action = State()
	waiting_for_schedule_file = State()