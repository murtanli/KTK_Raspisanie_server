import openpyxl
from apps.schedule.models import *
from apps.api.models import NotificationLog
from datetime import datetime

class ScheduleParser:
	def __init__(self, file):
		self.file = file

	def parse_excel_file_save(self):
		try:
			wb = openpyxl.load_workbook(self.file)
			sheet = wb.active

			type_time_id = self.save_time(sheet)
			is_created = self.parse_excel_schedule(type_time_id, sheet)
			if is_created:
				return True
			else:
				return False

		except Exception as e:
			print("Не загружено ((")
			return {'success': False, 'error': str(e)}

	def parse_excel_schedule(self, type_id, sheet):
		date = sheet["A2"].value
		date_clear = date.split(" ")[1]

		# Преобразуем строку в date объект
		try:
			schedule_date = datetime.strptime(date_clear, "%d.%m.%Y").date()
			Schedule.objects.filter(date=schedule_date).delete()
		except Exception as e:
			print(f"Ошибка при удалении: \n {e}")


		try:
			# После удаления
			after_count = Schedule.objects.filter(date=schedule_date).count()
			print(f"📊 Записей после удаления: {after_count}")

			schedule_start_line = 7
			schedule_columns = ['E', 'J', 'O', 'T']
			schedule_columns_kabinet = ['H', 'M', 'R', 'W']
			schedule_columns_kabinet_add = ['F', 'K', 'P', 'U']
			# created_count = 0
			# Получаем объекты тип времени
			schedule_type = ClassTimeType.objects.get(id=type_id)
			schedule_times = ClassTime.objects.filter(class_time_type=type_id).order_by('pair_number')
			schedule_times_list = list(schedule_times)  # преобразуем в список

			max_lines = 1000
			line_count = 0

			while line_count < max_lines:
				has_data = False

				for column, kabinet_column in zip(schedule_columns, schedule_columns_kabinet):
					group_number = sheet[f"{column}{schedule_start_line}"].value

					if not group_number:
						continue

					# Получаем или создаем группу
					group, _ = StudentGroup.objects.get_or_create(name=group_number)
					has_data = True

					for pair_number in range(7):  # 7 пар
						row_offset = schedule_start_line + 1 + (pair_number * 2)

						discipmine_name = sheet[f"{column}{row_offset}"].value
						kabinet_name = sheet[f"{kabinet_column}{row_offset}"].value
						teacher_name = sheet[f"{column}{row_offset + 1}"].value

						# Инициализируем переменные
						discipline_obj = None
						teacher_obj = None
						classroom_obj = None

						# Создаем/получаем объекты
						if discipmine_name:
							clean_name = discipmine_name.replace("_x000D_", "").strip()
							discipmine_code = clean_name.split(" ")[0] if " " in clean_name else ""
							discipline_obj, _ = Discipline.objects.get_or_create(
								name=clean_name,
								defaults={'code': discipmine_code}
							)
							if not kabinet_name:
								column_index = schedule_columns_kabinet.index(kabinet_column)
								kabinet_name = sheet[f"{schedule_columns_kabinet_add[column_index]}{row_offset}"].value

						if teacher_name:
							teacher_obj, _ = Teacher.objects.get_or_create(full_name=teacher_name)

						if kabinet_name:
							classroom_obj, _ = Classroom.objects.get_or_create(name=kabinet_name)


						if discipline_obj and pair_number < len(schedule_times_list):


							schedule = Schedule.objects.create(
								date=schedule_date,
								class_time_type=schedule_type,
								pair_number=schedule_times_list[pair_number],
								discipline=discipline_obj,
								teacher=teacher_obj,
								classroom=classroom_obj
							)
							schedule.groups.add(group)

							notification, created = NotificationLog.objects.get_or_create(
								schedule_date = schedule_date,
								defaults={'notification_sent': False}
							)
							if created:
								print(f"Создано уведомление для даты {schedule_date}")
							# created_count += 1
							# print(
							# 	f"#{created_count} Создано: {schedule.date} | {group.name} | Пара {pair_number + 1}")

				if not has_data:
					return True
					break

				schedule_start_line += 15
				line_count += 1
		except Exception as e:
			print(f" Ошибка при создании расписания: \n {e}")

	def save_time(self, sheet):
		fields = [8, 10, 12, 14, 16, 18, 20]
		excel_times = []
		class_time_types = ClassTimeType.objects.all()

		for field in fields:
			time_value = sheet[f"C{field}"].value

			if time_value:
				start_time_str, end_time_str = time_value.split("-")
				start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
				try:
					end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()
				except:
					end_time_str = end_time_str.replace(".", ":")
					end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()


				formatted_time = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
				excel_times.append(formatted_time)
			else:
				excel_times.append(None)

		for class_type in class_time_types:
			class_times = ClassTime.objects.filter(class_time_type=class_type).order_by('pair_number')

			db_times = []
			for ct in class_times:
				db_times.append(f"{ct.start_time.strftime('%H:%M')}-{ct.end_time.strftime('%H:%M')}")
			if excel_times == db_times:
				return class_type.id

		print("Ни один тип не совпал, создаем новый...")

		max_number = 0
		for class_time_type in class_time_types:
			name = class_time_type.name
			if name.startswith("Тип расписания "):
				try:
					type_number = int(name.replace("Тип расписания ", ""))
					if type_number > max_number:
						max_number = type_number
				except ValueError:
					continue

		new_number = max_number + 1
		new_type_name = f"Тип расписания {new_number}"

		new_type = ClassTimeType.objects.create(
			name=new_type_name,
			description=f"Автоматически созданный тип расписания {new_number}"
		)

		for pair_num, excel_time in enumerate(excel_times, 1):
			if excel_time:
				try:
					start_time_str, end_time_str = excel_time.split("-")
					start_time = datetime.strptime(start_time_str.strip(), "%H:%M").time()
					end_time = datetime.strptime(end_time_str.strip(), "%H:%M").time()

					ClassTime.objects.create(
						class_time_type=new_type,
						pair_number=pair_num,
						start_time=start_time,
						end_time=end_time
					)
				except (ValueError, AttributeError) as e:
					print(f"Ошибка создания времени для пары {pair_num}: {e}")

		print(f"✅ Создан новый тип: {new_type_name}")
		return new_type.id



