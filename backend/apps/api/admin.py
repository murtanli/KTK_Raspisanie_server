
from django.utils import timezone
from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser, SchedulePublication, NotificationLog


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
	list_display = [
		'telegram_id',
		'username',
		'name_person',
		'user_type_display',
		'group_info',
		'teacher_info',
		'registered_at'
	]
	list_filter = [
		'user_type',
		'group',
		'teacher_profile',
		'registered_at'
	]
	search_fields = [
		'telegram_id',
		'username',
		'name_person',
		'group__name',
		'teacher_profile__full_name'
	]
	readonly_fields = ['registered_at']
	list_per_page = 20

	fieldsets = (
		('Основная информация', {
			'fields': (
				'telegram_id',
				'username',
				'name_person',
				'user_type'
			)
		}),
		('Связи', {
			'fields': (
				'group',
				'teacher_profile'
			)
		}),
		('Системная информация', {
			'fields': ('registered_at',),
			'classes': ('collapse',)
		})
	)

	def user_type_display(self, obj):
		type_colors = {
			'student': 'blue',
			'teacher': 'green',
			'admin': 'red'
		}
		color = type_colors.get(obj.user_type, 'gray')
		return format_html(
			'<span style="color: {}; font-weight: bold;">{}</span>',
			color,
			obj.get_user_type_display()
		)

	user_type_display.short_description = 'Тип пользователя'

	def group_info(self, obj):
		if obj.group:
			return format_html(
				'<span style="color: #0066cc;">{}</span>',
				obj.group.name
			)
		return "-"

	group_info.short_description = 'Группа'

	def teacher_info(self, obj):
		if obj.teacher_profile:
			return format_html(
				'<span style="color: #00aa00;">{}</span>',
				obj.teacher_profile.full_name
			)
		return "-"

	teacher_info.short_description = 'Преподаватель'


@admin.register(SchedulePublication)
class SchedulePublicationAdmin(admin.ModelAdmin):
	list_display = [
		'schedule_date',
		'published_by_info',
		'publication_date',
		'excel_file_link',
		'notes_preview'
	]
	list_filter = [
		'schedule_date',
		'publication_date',
		'published_by__user_type'
	]
	search_fields = [
		'published_by__username',
		'published_by__first_name',
		'notes',
		'schedule_date'
	]
	readonly_fields = ['publication_date']
	list_per_page = 15
	date_hierarchy = 'schedule_date'

	fieldsets = (
		('Информация о публикации', {
			'fields': (
				'schedule_date',
				'published_by',
				'excel_file',
				'notes'
			)
		}),
		('Системная информация', {
			'fields': ('publication_date',),
			'classes': ('collapse',)
		})
	)

	def published_by_info(self, obj):
		return format_html(
			'{} ({})',
			obj.published_by.username or obj.published_by.telegram_id,
			obj.published_by.get_user_type_display()
		)

	published_by_info.short_description = 'Опубликовал'

	def excel_file_link(self, obj):
		if obj.excel_file:
			return format_html(
				'<a href="{}" download>📥 Скачать</a>',
				obj.excel_file.url
			)
		return "-"

	excel_file_link.short_description = 'Файл'

	def notes_preview(self, obj):
		if obj.notes:
			preview = obj.notes[:50] + "..." if len(obj.notes) > 50 else obj.notes
			return format_html(
				'<span title="{}">{}</span>',
				obj.notes,
				preview
			)
		return "-"

	notes_preview.short_description = 'Примечания'


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
	list_display = [
		'schedule_date',
		'notification_status',
		'sent_at',
		'recipients_count',
		'days_until'
	]

	list_filter = [
		'notification_sent',
		'schedule_date',
		'sent_at'
	]

	search_fields = [
		'schedule_date'
	]

	readonly_fields = [
		'sent_at',
		'recipients_count'
	]

	fieldsets = (
		('Основная информация', {
			'fields': ('schedule_date', 'recipients_count')
		}),
		('Статус уведомления', {
			'fields': ('notification_sent', 'sent_at')
		}),
	)

	actions = ['mark_as_sent', 'mark_as_pending']

	def notification_status(self, obj):
		if obj.notification_sent:
			return '✅ Отправлено'
		else:
			return '⏳ Ожидает'

	notification_status.short_description = 'Статус'

	def days_until(self, obj):
		today = timezone.now().date()
		delta = (obj.schedule_date - today).days
		if delta == 0:
			return 'Сегодня'
		elif delta == 1:
			return 'Завтра'
		elif delta > 1:
			return f'Через {delta} дн.'
		else:
			return f'{-delta} дн. назад'

	days_until.short_description = 'Дней до'

	def mark_as_sent(self, request, queryset):
		updated = queryset.update(
			notification_sent=True,
			sent_at=timezone.now()
		)
		self.message_user(request, f'{updated} уведомлений помечено как отправленные')

	mark_as_sent.short_description = 'Пометить как отправленные'

	def mark_as_pending(self, request, queryset):
		updated = queryset.update(
			notification_sent=False,
			sent_at=None
		)
		self.message_user(request, f'{updated} уведомлений помечено как ожидающие')

	mark_as_pending.short_description = 'Пометить как ожидающие'

	# Автоматическая подсветка в списке
	def get_list_display_links(self, request, list_display):
		return ['schedule_date']

	# Порядок сортировки по умолчанию
	ordering = ['-schedule_date']