from django.db import models
from ..schedule.models import StudentGroup, Teacher


class TelegramUser(models.Model):
	"""Пользователи Telegram бота"""
	USER_TYPES = [
		('student', 'Студент'),
		('teacher', 'Преподаватель'),
		('admin', 'Администратор'),
	]

	telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
	username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Username")
	name_person = models.CharField(max_length=100, blank=True, verbose_name="Фио")
	user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student', verbose_name="Тип пользователя")

	# Для студентов
	group = models.ForeignKey(StudentGroup, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Группа")

	# Для преподавателей
	teacher_profile = models.ForeignKey(Teacher, on_delete=models.SET_NULL, blank=True, null=True,
										verbose_name="Профиль преподавателя")
	registered_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
	class Meta:
		verbose_name = "Пользователь Telegram"
		verbose_name_plural = "Пользователи Telegram"
		ordering = ['-registered_at']

	def __str__(self):
		return f"{self.username or self.telegram_id} ({self.get_user_type_display()})"


class SchedulePublication(models.Model):
	published_by = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
	excel_file = models.FileField(upload_to='schedule_excels/')
	publication_date = models.DateTimeField(auto_now_add=True)
	schedule_date = models.DateField()
	notes = models.TextField(blank=True)

	class Meta:
		verbose_name = "Публикация расписания"
		verbose_name_plural = "Публикация расписаний"

	def __str__(self):
		return f"Публикация для {self.schedule_date}"


class NotificationLog(models.Model):
	schedule_date = models.DateField(verbose_name="Дата расписания")
	notification_sent = models.BooleanField(default=False, verbose_name="Уведомление отправлено")
	sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Время отправки")
	recipients_count = models.IntegerField(default=0, verbose_name="Кол-во получателей")

	class Meta:
		verbose_name = "Лог уведомлений"
		verbose_name_plural = "Логи уведомлений"

	def __str__(self):
		return f"Уведомление {self.schedule_date} ({'sent' if self.notification_sent else 'pending'})"