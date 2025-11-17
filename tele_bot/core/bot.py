from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from states import RegisterStates
from services.api_client import APIClient


class TelegramBot:
	def __init__(self, token: str, api_url: str):
		self.bot = Bot(token=token)
		self.dp = Dispatcher(storage=MemoryStorage())
		self.states = RegisterStates
		self.api_client = APIClient(api_url)

