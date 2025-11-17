from datetime import datetime, date
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..schedule.models import *
from .models import TelegramUser, SchedulePublication, NotificationLog
from .services.excel_parser import ScheduleParser


@api_view(['POST'])
def register_user(request):
    """Регистрация пользователя через бота"""
    telegram_id = request.data.get('telegram_id')
    user_type = request.data.get('user_type')
    username = request.data.get('username')
    group_name = request.data.get('group_name')
    teacher_name = request.data.get('teacher_name')
    if not telegram_id:
        return Response({'error': 'telegram_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_data = {
            'user_type': user_type,
        }

        if user_type == 'student' and group_name:
            try:
                group = StudentGroup.objects.get(name=group_name)
                user_data['group'] = group
            except StudentGroup.DoesNotExist:
                return Response({'error': 'Группа не найдена'}, status=status.HTTP_404_NOT_FOUND)

        elif user_type == 'teacher' and teacher_name:
            try:
                teacher = Teacher.objects.get(full_name__icontains=teacher_name)
                user_data['teacher_profile'] = teacher
            except Teacher.DoesNotExist:
                return Response({'error': 'Преподаватель не найден'}, status=status.HTTP_404_NOT_FOUND)

        user, created = TelegramUser.objects.update_or_create(
            telegram_id=telegram_id,
            username=username,
            defaults=user_data
        )

        return Response({
            'status': 'success',
            'created': created,
            'user_id': user.id,
            'user_type': user.user_type
        })

    except Exception as e:
        return Response({'error': 'Произошла ошибка, можете написать /help чтобы сообщить об ошибке'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def check_admin_role(request):
    telegram_id = request.data.get('telegram_id')

    if not telegram_id:
        return Response({'error': 'telegram_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        if user.user_type == 'admin':
            return Response({'value': True})
        else:
            return Response({'value': False})
    except TelegramUser.DoesNotExist:
        return Response({'value': False})


@api_view(['POST'])
def download_schedule(request):
    file = request.FILES.get('file')
    telegram_id = request.data.get('telegram_id')
    data = {}
    try:
        telegram_admin = TelegramUser.objects.get(telegram_id=telegram_id)
        data = {
            'published_by': telegram_admin
        }
    except TelegramUser.DoesNotExist:
        return Response({'value': 'profile not found'})

    parser = ScheduleParser(file)
    is_publish = parser.parse_excel_file_save()
    if is_publish:
        data_save = SchedulePublication.objects.update_or_create(
            schedule_date=timezone.now().date(),
            excel_file=file,
            defaults=data
        )
        return Response({'value': 'file save'}, status=status.HTTP_200_OK)
    else:
        return Response({'value': 'Error, file not publis'}, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['GET'])
def get_pending_notifications(request):
    # Если потребуется выдавать уведомы с датой больше чем сегодня ( если меньше то инфы не будет )
    """today = timezone.now().date()
    pending_notifications = NotificationLog.objects.filter(
        notification_sent=False,
        schedule_date__gt=today
    ).order_by('schedule_date')"""

    pending_notifications = NotificationLog.objects.filter(
        notification_sent=False
    ).order_by('schedule_date')

    # Получаем всех пользователей которые должны получать уведомления
    users = TelegramUser.objects.filter(
        models.Q(group__isnull=False) |  # студенты с группами
        models.Q(teacher_profile__isnull=False)  # преподаватели
    )

    # Получаем списки групп и преподавателей из пользователей
    user_groups = set(users.exclude(group__isnull=True).values_list('group__name', flat=True))
    user_teachers = set(
        users.exclude(teacher_profile__isnull=True).values_list('teacher_profile__full_name', flat=True))

    notifications_data = []

    for notification in pending_notifications:
        schedules = Schedule.objects.filter(date=notification.schedule_date).select_related(
            'discipline', 'teacher', 'classroom', 'pair_number'
        ).prefetch_related('groups')

        notification_data = {
            'schedule_date': notification.schedule_date.strftime("%d.%m.%Y"),
            'groups': {},
            'teachers': {},
            'raw_date': notification.schedule_date.isoformat()
        }

        for schedule in schedules:
            # Обрабатываем группы (для студентов)
            for group in schedule.groups.all():
                if group.name in user_groups:  # только группы у которых есть пользователи
                    if group.name not in notification_data['groups']:
                        notification_data['groups'][group.name] = []

                    notification_data['groups'][group.name].append({
                        'pair_number': schedule.pair_number.pair_number,
                        'time': f"{schedule.pair_number.start_time.strftime('%H:%M')}-{schedule.pair_number.end_time.strftime('%H:%M')}",
                        'discipline': schedule.discipline.name,
                        'teacher': schedule.teacher.full_name if schedule.teacher else None,
                        'classroom': schedule.classroom.name if schedule.classroom else None,
                    })

            # Обрабатываем преподавателей
            if schedule.teacher and schedule.teacher.full_name in user_teachers:
                teacher_name = schedule.teacher.full_name
                if teacher_name not in notification_data['teachers']:
                    notification_data['teachers'][teacher_name] = []

                notification_data['teachers'][teacher_name].append({
                    'pair_number': schedule.pair_number.pair_number,
                    'time': f"{schedule.pair_number.start_time.strftime('%H:%M')}-{schedule.pair_number.end_time.strftime('%H:%M')}",
                    'discipline': schedule.discipline.name,
                    'groups': [group.name for group in schedule.groups.all()],
                    'classroom': schedule.classroom.name if schedule.classroom else None,
                })

        if notification_data['groups'] or notification_data['teachers']:
            notifications_data.append(notification_data)

    return Response({'notifications': notifications_data})


@api_view(['POST'])
def mark_notification_sent(request):
    """Бот вызывает этот endpoint после отправки уведомлений"""
    schedule_date_str = request.data.get('schedule_date')

    try:
        schedule_date = datetime.strptime(schedule_date_str, "%Y-%m-%d").date()
        notification = NotificationLog.objects.get(schedule_date=schedule_date)
        notification.notification_sent = True
        notification.sent_at = timezone.now()
        notification.save()

        return Response({'status': 'success'})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def get_all_users(request):
    """Возвращает всех пользователей для уведомлений"""
    users = TelegramUser.objects.all()
    users_data = []
    for user in users:
        data = {
            'telegram_id': user.telegram_id,
            'username': user.username,
            'group': user.group.name if user.group else None,
            'teacher_profile': user.teacher_profile.full_name if user.teacher_profile else None,
            'user_type': user.user_type
        }
        users_data.append(data)
    return Response({'users': users_data})


@api_view(['POST'])
def get_user_info(request):
    user_id = request.data.get('tg_id')
    try:
        tg_user = TelegramUser.objects.get(telegram_id=user_id)

        if tg_user.user_type == "student":
            data = {
                "group_number": tg_user.group.name if tg_user.group else None,
                "teacher_fio": None
            }
        elif tg_user.user_type == "teacher":
            teacher_name = tg_user.teacher_profile.full_name if tg_user.teacher_profile else tg_user.name_person
            data = {
                "group_number": None,
                "teacher_fio": teacher_name
            }
        else:
            return Response({"error": "Вы не прошли регистрацию"}, status.HTTP_400_BAD_REQUEST)
        print(data)
        return Response(data, status.HTTP_200_OK)

    except TelegramUser.DoesNotExist:
        return Response({"error": "Вы не прошли регистрацию"}, status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
def get_schedule(request):
    schedule_date_str = request.data.get('date')
    schedule_group = request.data.get('group')
    schedule_teacher = request.data.get('teacher')
    schedule_classroom = request.data.get('classroom')

    # Начинаем с базового queryset
    queryset = Schedule.objects.all()

    # Фильтр по дате
    if schedule_date_str:
        try:
            schedule_date = datetime.strptime(schedule_date_str, "%Y-%m-%d").date()
            queryset = queryset.filter(date=schedule_date)
        except ValueError:
            return Response({"error": "Неверный формат даты. Используй YYYY-MM-DD."}, status=400)

    # Фильтр по группе (ManyToMany)
    if schedule_group:
        queryset = queryset.filter(groups__name__icontains=schedule_group)

    # Фильтр по преподавателю
    if schedule_teacher:
        queryset = queryset.filter(teacher__full_name__icontains=schedule_teacher)

    # Фильтр по аудитории
    if schedule_classroom:
        queryset = queryset.filter(classroom__name__icontains=schedule_classroom)

    # Исключаем дубликаты (из-за ManyToMany)
    queryset = queryset.distinct()

    # Преобразуем данные в удобный формат
    result = []
    for item in queryset.select_related('teacher', 'discipline', 'classroom', 'pair_number'):
        result.append({
            "date": item.date.strftime("%Y-%m-%d"),
            "pair_number": item.pair_number.pair_number,
            "time": f"{item.pair_number.start_time.strftime('%H:%M')} - {item.pair_number.end_time.strftime('%H:%M')}",
            "groups": [g.name for g in item.groups.all()],
            "discipline": item.discipline.name,
            "teacher": item.teacher.full_name,
            "classroom": item.classroom.name,
            "lesson_type": item.lesson_type,
            "is_online": item.is_online,
            "platform": item.platform,
        })

    return Response(result)
