from django.db import models
from django.contrib.auth.models import User

class ClassTimeType(models.Model):
	"""Типы расписания (понедельник, вт-сб, предпраздничный)"""
	name = models.CharField(max_length=100, verbose_name="Название типа")
	description = models.TextField(blank=True, verbose_name="Описание")

	class Meta:
		verbose_name = "Тип расписания"
		verbose_name_plural = "Типы расписаний"

	def __str__(self):
		return self.name


class ClassTime(models.Model):
	"""Время пар для разных типов расписания"""
	class_time_type = models.ForeignKey(ClassTimeType, on_delete=models.CASCADE, verbose_name="Тип расписания")
	pair_number = models.IntegerField(verbose_name="Номер пары")
	start_time = models.TimeField(verbose_name="Время начала")
	end_time = models.TimeField(verbose_name="Время окончания")

	class Meta:
		unique_together = ['class_time_type', 'pair_number']
		ordering = ['class_time_type', 'pair_number']
		verbose_name = "Время пары"
		verbose_name_plural = "Время пар"

	def __str__(self):
		return f"{self.class_time_type} - Пара {self.pair_number} ({self.start_time}-{self.end_time})"


class Teacher(models.Model):
	"""Преподаватели"""
	full_name = models.CharField(max_length=200, verbose_name="ФИО преподавателя")
	telegram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram username")
	telegram_chat_id = models.BigIntegerField(blank=True, null=True, verbose_name="Telegram Chat ID")

	class Meta:
		verbose_name = "Преподаватель"
		verbose_name_plural = "Преподаватели"
		ordering = ['full_name']

	def __str__(self):
		return self.full_name


class StudentGroup(models.Model):
	"""Учебные группы"""
	name = models.CharField(max_length=50, unique=True, verbose_name="Название группы")
	course = models.IntegerField(verbose_name="Курс", blank=True, null=True)

	class Meta:
		verbose_name = "Учебная группа"
		verbose_name_plural = "Учебные группы"
		ordering = ['name']

	def __str__(self):
		return self.name


class Discipline(models.Model):
	"""Дисциплины"""
	name = models.CharField(max_length=300, verbose_name="Название дисциплины")
	code = models.CharField(max_length=50, blank=True, verbose_name="Код дисциплины")

	class Meta:
		verbose_name = "Дисциплина"
		verbose_name_plural = "Дисциплины"
		ordering = ['name']

	def __str__(self):
		return f"{self.code} - {self.name}" if self.code else self.name


class Classroom(models.Model):
	"""Аудитории"""
	name = models.CharField(max_length=50, verbose_name="Название аудитории")
	building = models.CharField(max_length=50, blank=True, verbose_name="Корпус")

	class Meta:
		verbose_name = "Аудитория"
		verbose_name_plural = "Аудитории"
		ordering = ['name']

	def __str__(self):
		return f"{self.building} - {self.name}" if self.building else self.name


class Schedule(models.Model)	:
	"""Основное расписание"""
	date = models.DateField(verbose_name="Дата")
	class_time_type = models.ForeignKey(ClassTimeType, on_delete=models.CASCADE, verbose_name="Тип расписания")
	pair_number = models.ForeignKey(ClassTime, on_delete=models.CASCADE,verbose_name="Номер пары")

	# Группы (может быть несколько групп на одной паре)
	groups = models.ManyToManyField(StudentGroup, verbose_name="Группы")

	discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name="Дисциплина")
	teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")
	classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="Аудитория")

	# Дополнительные поля из Excel
	subgroup = models.CharField(max_length=50, blank=True, verbose_name="Подгруппа")
	lesson_type = models.CharField(max_length=20, blank=True, verbose_name="Тип занятия (Л/пр/лаб)")
	is_online = models.BooleanField(default=False, verbose_name="Онлайн занятие")
	platform = models.CharField(max_length=100, blank=True, verbose_name="Платформа (Moodle и т.д.)")

	class Meta:
		ordering = ['date', 'pair_number']
		indexes = [
			models.Index(fields=['date']),
			models.Index(fields=['teacher']),
			models.Index(fields=['pair_number']),
		]
		verbose_name = "Расписание"
		verbose_name_plural = "Расписания"

	def __str__(self):
		groups_str = ", ".join([group.name for group in self.groups.all()])
		return f"{self.date} - Пара {self.pair_number} - {groups_str} - {self.discipline}"



