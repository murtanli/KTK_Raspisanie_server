import asyncio
from config import API_URL, BOT_TOKEN
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from core.states import RegisterStates
from services.api_client import APIClient
from handlers.base import BaseHandlers
from handlers.registration import RegistrationHandler
from handlers.download_schedule import AdminHandler
from handlers.notifier import ScheduleNotifier
from handlers.schedule_today import ScheduleToday

class TelegramBot:
	def __init__(self, token: str, api_url: str):
		self.bot = Bot(token=token)
		# self.dp = Dispatcher(storage=MemoryStorage())
		self.dp = Dispatcher(storage=RedisStorage.from_url("redis://redis:6379/0"))
		self.states = RegisterStates
		self.api_client = APIClient(api_url)

		# Инициализация обработчиков
		self.base_handlers = BaseHandlers(self.dp, self.states, self.api_client)
		self.registration_handlers = RegistrationHandler(
			self.dp, self.states, self.api_client
		)
		self.download_shedule_handlers = AdminHandler(
			self.dp, self.bot, self.states, self.api_client
		)
		self.notifier = ScheduleNotifier(self.bot, self.api_client)
		self.schedule_today = ScheduleToday(self.dp, self.states, self.api_client)

	def download_schedule_handlers(self):
		self.base_handlers.register_user()
		self.download_shedule_handlers.register_handler()
	def register_all_handlers(self):
		"""Регистрирует все обработчики"""
		self.base_handlers.register_user()
		self.registration_handlers.register_handler()
		self.schedule_today.register_handlers()

	async def start_notification_task(self):
		"""Запускает фоновую задачу для уведомлений"""
		try:
			while True:
				# Проверяем уведомления каждые 30 минут
				print("Цикл запущен !!")
				#await self.notifier.check_and_notify()
				#await asyncio.sleep(60)  # 30 минут = 1800 секунд
		except Exception as e:
			print(f"❌ Ошибка в задаче уведомлений: {e}")
			#await asyncio.sleep(300)
			asyncio.create_task(self.start_notification_task())

	async def start(self):
		"""Запускает бота"""
		self.register_all_handlers()
		self.download_schedule_handlers()

		#asyncio.create_task(self.start_notification_task())
		print("🔔 Фоновая задача уведомлений запущена")

		await self.dp.start_polling(self.bot)

async def main():
    """Главная функция запуска"""
    print("Запуск бота...")
    bot = TelegramBot(BOT_TOKEN, API_URL)
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())