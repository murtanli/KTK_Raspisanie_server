from aiogram import Bot
from services.api_client import APIClient
from keyboards.main import choose_of_action_user

class ScheduleNotifier:
	def __init__(self, bot: Bot, api_client: APIClient):
		self.bot = bot
		self.api_client = api_client

	async def check_and_notify(self):
		"""Главная функция - проверяет и отправляет уведомления"""
		print("🔔 Проверяем новые расписания...")

		response = await self.api_client.get_pending_notifications()
		notifications = response.get('notifications', [])

		if not notifications:
			print("📭 Нет новых расписаний для уведомлений")
			return

		print(f"📨 Найдено {len(notifications)} расписаний для уведомлений")

		for notification in notifications:
			await self._send_notification(notification)

	async def _send_notification(self, notification_data):
		"""Отправляет уведомление конкретным пользователям"""
		schedule_date = notification_data['schedule_date']
		groups_data = notification_data['groups']
		teachers_data = notification_data['teachers']
		raw_date = notification_data['raw_date']

		response = await self.api_client.get_all_users()
		all_users = response.get('users', [])

		sent_count = 0

		for user in all_users:
			user_message = None

			if user['user_type'] == 'student' and user['group']:
				if user['group'] in groups_data:
					user_message = self._format_student_message(
						schedule_date,
						user['group'],
						groups_data[user['group']]
					)

			elif user['user_type'] == 'teacher' and user['teacher_profile']:
				if user['teacher_profile'] in teachers_data:
					user_message = self._format_teacher_message(
						schedule_date,
						user['teacher_profile'],
						teachers_data[user['teacher_profile']]
					)

			if user_message:
				try:
					await self.bot.send_message(
						chat_id=user['telegram_id'],
						text=user_message,
						parse_mode='HTML',
						reply_markup=choose_of_action_user()
					)
					sent_count += 1
					print(f"✅ Отправлено пользователю {user['telegram_id']} ({user['user_type']})")
				except Exception as e:
					print(f"❌ Ошибка отправки пользователю {user['telegram_id']}: {e}")

		await self.api_client.mark_notification_sent(raw_date)
		print(f"✅ Уведомление на {schedule_date} отправлено {sent_count} пользователям")

	def _format_student_message(self, schedule_date, group_name, group_schedules):
		"""Сообщение для студентов"""
		message = f"📅 <b>Опубликовано новое расписание для вашей группы!</b>\n\n"
		message += f"👥 <b>Группа:</b> {group_name}\n"
		message += f"🗓️ <b>Дата:</b> {schedule_date}\n\n"

		for i, schedule in enumerate(group_schedules):
			message += f"{i + 1}. {schedule['time']} - {schedule['discipline']}\n"
			if schedule['teacher']:
				message += f"   👨‍🏫 {schedule['teacher']}\n"
			if schedule['classroom']:
				message += f"   🏫 {schedule['classroom']}\n"
			message += "\n"


		return message

	def _format_teacher_message(self, schedule_date, teacher_name, teacher_schedules):
		"""Сообщение для преподавателей"""
		message = f"📅 <b>Опубликовано новое расписание для вас!</b>\n\n"
		message += f"👨‍🏫 <b>Преподаватель:</b> {teacher_name}\n"
		message += f"🗓️ <b>Дата:</b> {schedule_date}\n\n"

		for i, schedule in enumerate(teacher_schedules):
			message += f"{i + 1}. {schedule['time']} - {schedule['discipline']}\n"
			if schedule['groups']:
				message += f"   👥 Группы: {', '.join(schedule['groups'])}\n"
			if schedule['classroom']:
				message += f"   🏫 {schedule['classroom']}\n"
			message += "\n"

		return message