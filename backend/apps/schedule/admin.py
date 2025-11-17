from django.contrib import admin
from django.utils.html import format_html
from .models import (
	ClassTimeType, ClassTime, Teacher, StudentGroup,
	Discipline, Classroom, Schedule
)


@admin.register(ClassTimeType)
class ClassTimeTypeAdmin(admin.ModelAdmin):
	list_display = ['name', 'description_preview', 'class_times_count']
	search_fields = ['name', 'description']
	list_per_page = 10

	def description_preview(self, obj):
		if obj.description:
			preview = obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
			return preview
		return "-"

	description_preview.short_description = 'Описание'

	def class_times_count(self, obj):
		count = ClassTime.objects.filter(class_time_type=obj).count()
		return format_html(
			'<span style="color: {};">{}</span>',
			'green' if count > 0 else 'gray',
			f"{count} расписаний"
		)

	class_times_count.short_description = 'Кол-во расписаний'


@admin.register(ClassTime)
class ClassTimeAdmin(admin.ModelAdmin):
	list_display = [
		'class_time_type',
		'pair_number',
		'start_time',
		'end_time',
		'duration'
	]
	list_filter = ['class_time_type', 'pair_number']
	ordering = ['class_time_type', 'pair_number']
	list_per_page = 15

	def duration(self, obj):
		return f"{obj.start_time} - {obj.end_time}"

	duration.short_description = 'Время'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
	list_display = [
		'full_name',
		'telegram_username',
		'telegram_chat_id',
		'schedules_count'
	]
	search_fields = ['full_name', 'telegram_username']
	list_per_page = 20

	def schedules_count(self, obj):
		count = Schedule.objects.filter(teacher=obj).count()
		return format_html(
			'<span style="color: {};">{} пар</span>',
			'green' if count > 0 else 'gray',
			count
		)

	schedules_count.short_description = 'Пар в расписании'


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
	list_display = ['name', 'course', 'students_count', 'schedules_count']
	list_filter = ['course']
	search_fields = ['name']
	list_per_page = 25

	def students_count(self, obj):
		from apps.api.models import TelegramUser  # Локальный импорт чтобы избежать циклического импорта
		count = TelegramUser.objects.filter(group=obj).count()
		return format_html(
			'<span style="color: {};">{} студентов</span>',
			'blue' if count > 0 else 'gray',
			count
		)

	students_count.short_description = 'Студентов'

	def schedules_count(self, obj):
		count = Schedule.objects.filter(groups=obj).count()
		return format_html(
			'<span style="color: {};">{} пар</span>',
			'green' if count > 0 else 'gray',
			count
		)

	schedules_count.short_description = 'Пар в расписании'


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'schedules_count']
	search_fields = ['name', 'code']
	list_per_page = 20

	def schedules_count(self, obj):
		count = Schedule.objects.filter(discipline=obj).count()
		return format_html(
			'<span style="color: {};">{} пар</span>',
			'green' if count > 0 else 'gray',
			count
		)

	schedules_count.short_description = 'Пар в расписании'


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
	list_display = ['name', 'building', 'schedules_count']
	list_filter = ['building']
	search_fields = ['name', 'building']
	list_per_page = 20

	def schedules_count(self, obj):
		count = Schedule.objects.filter(classroom=obj).count()
		return format_html(
			'<span style="color: {};">{} пар</span>',
			'green' if count > 0 else 'gray',
			count
		)

	schedules_count.short_description = 'Пар в расписании'


class GroupFilter(admin.SimpleListFilter):
	title = 'Группа'
	parameter_name = 'group'

	def lookups(self, request, model_admin):
		from .models import StudentGroup  # Локальный импорт
		groups = StudentGroup.objects.all()
		return [(group.id, group.name) for group in groups]

	def queryset(self, request, queryset):
		if self.value():
			return queryset.filter(groups__id=self.value())
		return queryset


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
	list_display = [
		'date',
		'pair_number',
		'groups_display',
		'discipline',
		'teacher',
		'classroom',
		'lesson_type_display',
		'is_online_display'
	]
	list_filter = [
		'date',
		'class_time_type',
		'teacher',
		'classroom',
		'lesson_type',
		'is_online',
		GroupFilter
	]
	search_fields = [
		'groups__name',
		'discipline__name',
		'teacher__full_name',
		'classroom__name'
	]
	filter_horizontal = ['groups']
	list_per_page = 25
	date_hierarchy = 'date'

	fieldsets = (
		('Основная информация', {
			'fields': (
				'date',
				'class_time_type',
				'pair_number'
			)
		}),
		('Учебный процесс', {
			'fields': (
				'groups',
				'discipline',
				'teacher',
				'classroom'
			)
		}),
		('Дополнительно', {
			'fields': (
				'subgroup',
				'lesson_type',
				'is_online',
				'platform'
			),
			'classes': ('collapse',)
		})
	)

	def groups_display(self, obj):
		groups = obj.groups.all()
		if groups:
			names = [group.name for group in groups]
			return ", ".join(names)
		return "-"

	groups_display.short_description = 'Группы'

	def lesson_type_display(self, obj):
		if obj.lesson_type:
			type_map = {
				'Л': 'Лекция',
				'пр': 'Практика',
				'лаб': 'Лабораторная'
			}
			display_name = type_map.get(obj.lesson_type, obj.lesson_type)
			color = {
				'Л': 'purple',
				'пр': 'orange',
				'лаб': 'brown'
			}.get(obj.lesson_type, 'gray')
			return format_html(
				'<span style="color: {}; font-weight: bold;">{}</span>',
				color,
				display_name
			)
		return "-"

	lesson_type_display.short_description = 'Тип занятия'

	def is_online_display(self, obj):
		if obj.is_online:
			return format_html(
				'<span style="color: green;">✅ Онлайн</span>'
			)
		return format_html(
			'<span style="color: blue;">📚 Очно</span>'
		)

	is_online_display.short_description = 'Формат'