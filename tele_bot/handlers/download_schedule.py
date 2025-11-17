from aiogram import types
from aiogram.fsm.context import FSMContext
from core.states import DownloadSchedule
from keyboards.main import choose_of_action_admin as keyboard_admin
import re
from handlers.notifier import ScheduleNotifier
class AdminHandler:
	def __init__(self, dp,bot, states, api_client):
		self.dp = dp
		self.bot = bot
		self.states = states
		self.api_client = api_client
		self.notifier = ScheduleNotifier(self.bot, self.api_client)

	def register_handler(self):
		@self.dp.message(DownloadSchedule.waitind_for_action)
		async def admin_action_handler(message: types.Message, state: FSMContext):
			if message.text == "🎓 Загрузить расписание":
				await message.answer("📤 Отправьте файл с расписанием групп")
				await state.set_state(DownloadSchedule.waiting_for_schedule_file)
			elif message.text == "👨‍🏫 Расписание на сегодня":
				pass
			elif message.text == "👨‍🏫 Расписание по дате":
				pass
			else:
				await message.answer(
					"Неправильная команда !",
					reply_markup=keyboard_admin
				)
				await state.set_state(DownloadSchedule.waitind_for_action)

		@self.dp.message(DownloadSchedule.waiting_for_schedule_file)
		async def download_schedule(message: types.Message, state: FSMContext):
			if not message.document:
				await message.answer(
					f"❌ Пожалуйста, отправьте файл")
				return

			if not message.document.file_name.endswith(('.xlsx', '.xls')):
				await message.answer(
					"❌ Поддерживаются только Excel файлы (.xlsx, .xls)")
				return
			try:
				file_id = message.document.file_id
				file = await message.bot.get_file(file_id)
				file_bytes = await message.bot.download_file(file.file_path)

				file_path = f"Temp_excel/temp_{message.document.file_name}"
				await message.bot.download_file(file.file_path, file_path)

				file_data = (message.document.file_name, file_bytes,
							 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
				await message.answer("✅ Файл получен! Начинаю обработку...")

				response = await self.api_client.upload_schedule(file_data, message.from_user.id)
				if response:
					#Отправка уведомлений
					#await self.notifier.check_and_notify()
					await self.notifier.check_and_notify()
					file_name = message.document.file_name
					schedule_date = re.search(r'(\d{2}\.\d{2}\.\d{4})', file_name)
					await message.answer(f'✅ Расписание на {schedule_date.group(1)} опубликовано!', reply_markup=keyboard_admin())
				else:
					await message.answer('❌ Расписание не опубликовано')
				await state.clear()
				await state.set_state(DownloadSchedule.waitind_for_action)
			except Exception as e:
				await message.answer(f"❌ Ошибка: {str(e)}")