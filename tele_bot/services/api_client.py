import aiohttp
import requests
from typing import Dict, Optional
import json
from datetime import datetime
class APIClient:
	def __init__(self, base_url: str):
		self.base_url = base_url

	async def register_user(self,
							telegram_id: int,
							username: str,
							user_type: str,
							group_name: str = None,
							teacher_name: str = None
							) -> str:
		try:
			data = {
				"telegram_id": telegram_id,
				"user_type": user_type,
				"username": username
			}

			if user_type == "student" and group_name:
				data["group_name"] = str(group_name)
			elif user_type == "teacher" and teacher_name:
				data["teacher_name"] = teacher_name
			response = requests.post(f"{self.base_url}/users/register/", json=data)
			if response.status_code == 200 or response.status_code == 201:
				return response.text
			else:
				print(f"Произошла ошибка ответ - {response.status_code}")

		except Exception as e:
			print(f"Error registering user: {e}")
			return False

	async def check_admin(self, telegram_id: int) -> bool:
		data = {
			'telegram_id': telegram_id
		}
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(
						f"{self.base_url}/users/is_admin/",
						json=data
				) as response:
					if response.status == 200:
						result = await response.json()
						return result.get('value', False)
					return False
		except Exception as e:
			print(f"Ошибка при проверке админа: {e}")
			return False

	async def upload_schedule(self, file_data: tuple, telegram_id: int) -> bool:
		try:
			form_data = aiohttp.FormData()
			form_data.add_field('file',
								file_data[1],
								filename=file_data[0],
								content_type=file_data[2])
			form_data.add_field('telegram_id', str(telegram_id))

			async with aiohttp.ClientSession() as session:
				async with session.post(
						f"{self.base_url}/users/download_schedule/",
						data=form_data
				) as response:
					if response.status == 200:
						return True
					else:
						return False

		except Exception as e:
			print(f"Error uploading schedule: {e}")
			return {'status': 'error', 'message': str(e)}

	async def get_pending_notifications(self):
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(f"{self.base_url}/notifications/pending/") as response:
					if response.status == 200:
						return await response.json()
					return {'notifications': []}
		except Exception as e:
			print(f"Error getting notifications: {e}")
			return {'notifications': []}

	async def mark_notification_sent(self, schedule_date):
		"""Сообщает API что уведомление отправлено"""
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(
						f"{self.base_url}/notifications/mark_sent/",
						json={'schedule_date': schedule_date}
				) as response:
					return response.status == 200
		except Exception as e:
			print(f"Error marking notification sent: {e}")
			return False

	async def get_all_users(self):
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(
						f"{self.base_url}/users/get_users/"
				) as response:
					if response.status == 200:
						data = await response.json()
						return data
					return {'users': []}
		except Exception as e:
			print(f"Error getting users: {e}")
			return {'users': []}

	async def get_user_info(self, telegram_id: int):
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(
						f"{self.base_url}/users/get_user_info/",
						json={'tg_id': telegram_id}
				) as response:
					data = await response.json()

					if response.status in (200, 400):
						return data

					return {}

		except Exception as e:
			print(f"Error getting user info: {e}")
			return {}

	async def get_schedule_today(self, student_group=None, teacher_fio=None):
		today = datetime.today().strftime("%Y-%m-%d")
		if student_group:
			payload = {"date": today, "group": student_group}
		elif teacher_fio:
			payload = {"date": today, "teacher": teacher_fio}
		else:
			raise ValueError("student_group или teacher_fio должны быть указаны")

		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(
						f"{self.base_url}/schedule/get_schedule/",
						json=payload
				) as response:
					data = await response.json()

					if response.status in (200, 400):
						print(data)
						return data

					return {}

		except Exception as e:
			print(f"Error getting schedule: {e}")
			return {}