from django.core.management.base import BaseCommand

from tickets.models import Comment, Ticket, User

USERS = [
    ("staff1", "Staff12345", User.Role.STAFF),
    ("student1", "Student12345", User.Role.STUDENT),
    ("student2", "Student12345", User.Role.STUDENT),
]

# тема, описание, кабинет, срочность, статус, автор
TICKETS = [
    ("Не работает проектор", "Нет изображения, лампа мигает.", "204", "high", "new", "student1"),
    ("Нет интернета", "Не загружаются сайты, Wi-Fi подключён.", "315", "high", "in_progress", "student1"),
    ("Не печатает принтер", "Задание зависает в очереди.", "112", "medium", "new", "student2"),
    ("Сломалась клавиатура", "Не работают клавиши Enter и Shift.", "208", "low", "resolved", "student1"),
    ("Не запускается компьютер", "После нажатия кнопки экран чёрный.", "301", "high", "in_progress", "student2"),
    ("Нужна программа для курсовой", "Установите Python и VS Code на ПК.", "210", "medium", "new", "student1"),
    ("Зависает интерактивная доска", "Не реагирует на касания.", "105", "medium", "resolved", "student2"),
    ("Нет звука в аудитории", "Колонки включены, звука нет.", "401", "low", "new", "student2"),
    ("Не подключается к проектору", "Ноутбук не видит второй экран.", "204", "medium", "in_progress", "student1"),
    ("Забыл пароль от учебной почты", "Нужно сбросить пароль.", "Учительская", "low", "resolved", "student2"),
    ("Мигает монитор", "Экран мерцает каждые несколько секунд.", "309", "medium", "new", "student1"),
    ("Не работает розетка у компьютера", "Нет питания на рабочем месте 7.", "311", "high", "new", "student2"),
]


class Command(BaseCommand):
    help = "Наполняет базу демонстрационными данными"

    def handle(self, *args, **options):
        users = {}
        for username, password, role in USERS:
            user, _ = User.objects.get_or_create(username=username, defaults={"role": role})
            user.role = role
            user.set_password(password)
            user.save()
            users[username] = user

        staff = users["staff1"]
        created = 0
        for title, description, room, priority, status, author in TICKETS:
            ticket, is_new = Ticket.objects.get_or_create(
                title=title,
                author=users[author],
                defaults={
                    "description": description,
                    "room": room,
                    "priority": priority,
                    "status": status,
                    "assignee": staff if status != "new" else None,
                },
            )
            if is_new:
                created += 1
                if status != "new":
                    Comment.objects.create(
                        ticket=ticket, author=staff, text="Принял заявку, подойду в течение часа."
                    )
                if status == "resolved":
                    Comment.objects.create(
                        ticket=ticket,
                        author=staff,
                        text="Проблема устранена. Если повторится, напишите в комментарии.",
                    )

        self.stdout.write(self.style.SUCCESS(f"Готово. Новых заявок: {created}."))